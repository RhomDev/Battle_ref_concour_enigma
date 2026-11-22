import json
import queue
import select
import socket
import struct
import threading
import time


DEFAULT_TCP_PORT = 5555
DEFAULT_UDP_PORT = 5556
HOTSPOT_DEFAULT_IP = "192.168.43.1"
BEACON_MAGIC = "BATTLE_REF_BEACON"


def get_local_ip():
    """Détecte l'adresse IP locale sur le Wi-Fi ou le point d'accès."""
    # Méthode 1 : Connexion UDP factice (sans envoi réel) pour déterminer l'interface
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.3)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    # Méthode 2 : Détection via nom d'hôte
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127."):
                return ip
    except Exception:
        pass

    # Repli : adresse standard du point d'accès Android
    return HOTSPOT_DEFAULT_IP


def send_packet(sock, data):
    """Envoie un dictionnaire sous forme de paquet JSON préfixé par sa taille."""
    raw = json.dumps(data).encode("utf-8")
    header = struct.pack(">I", len(raw))
    sock.sendall(header + raw)


def recv_packet(sock):
    """Lit un paquet complet préfixé par sa taille (bloquant ou timeouté)."""
    header = _recv_exact(sock, 4)
    if not header:
        return None
    length = struct.unpack(">I", header)[0]
    raw = _recv_exact(sock, length)
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def _recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


class DiscoveryBeacon:
    """Diffuseur de balise UDP pour la découverte automatique sur le réseau local."""

    def __init__(self, host_name, tcp_port=DEFAULT_TCP_PORT, udp_port=DEFAULT_UDP_PORT):
        self.host_name = host_name
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1.0)
        message = json.dumps({
            "magic": BEACON_MAGIC,
            "name": self.host_name,
            "port": self.tcp_port,
        }).encode("utf-8")

        while self.running:
            try:
                # Diffuse sur le broadcast universel et sur le subnet hotspot Android
                sock.sendto(message, ("255.255.255.255", self.udp_port))
                sock.sendto(message, ("192.168.43.255", self.udp_port))
            except Exception:
                pass
            time.sleep(1.2)
        sock.close()


class DiscoveryListener:
    """Écouteur UDP pour découvrir les parties hôtes sur le réseau local."""

    def __init__(self, udp_port=DEFAULT_UDP_PORT):
        self.udp_port = udp_port
        self.running = False
        self.thread = None
        self.servers = {}  # (ip, port) -> {"name": ..., "last_seen": timestamp}
        self.lock = threading.Lock()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def get_discovered_servers(self):
        now = time.time()
        with self.lock:
            # Conserve uniquement les serveurs vus dans les 5 dernières secondes
            self.servers = {k: v for k, v in self.servers.items() if now - v["last_seen"] < 5.0}
            return [
                {"ip": ip, "port": port, "name": info["name"]}
                for (ip, port), info in self.servers.items()
            ]

    def _listen_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", self.udp_port))
        except Exception:
            sock.close()
            return

        sock.settimeout(1.0)
        while self.running:
            try:
                data, addr = sock.recvfrom(2048)
                msg = json.loads(data.decode("utf-8"))
                if msg.get("magic") == BEACON_MAGIC:
                    ip = addr[0]
                    port = msg.get("port", DEFAULT_TCP_PORT)
                    name = msg.get("name", "Partie locale")
                    with self.lock:
                        self.servers[(ip, port)] = {"name": name, "last_seen": time.time()}
            except (socket.timeout, json.JSONDecodeError):
                continue
            except Exception:
                break
        sock.close()


class GameServer:
    """Serveur de jeu local TCP. Gère l'état de la partie et la synchronisation avec le client."""

    def __init__(self, host_ip="0.0.0.0", port=DEFAULT_TCP_PORT, host_name="Joueur 1"):
        self.host_ip = host_ip
        self.port = port
        self.host_name = host_name
        self.partie = None
        self.running = False
        self.server_sock = None
        self.client_sock = None
        self.client_addr = None
        self.client_name = "Joueur 2"
        self.thread = None
        self.host_events = queue.Queue()
        self.client_connected = False
        self.lock = threading.Lock()

    def start(self):
        from gameplay.partie import Partie
        self.partie = Partie(p1_name=self.host_name, p2_name=self.client_name)
        self.running = True
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.host_ip, self.port))
        self.server_sock.listen(1)
        self.server_sock.settimeout(0.5)

        self.thread = threading.Thread(target=self._server_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.client_sock:
            try:
                self.client_sock.close()
            except Exception:
                pass
            self.client_sock = None
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
            self.server_sock = None

    def poll_events(self):
        events = []
        while not self.host_events.empty():
            try:
                events.append(self.host_events.get_nowait())
            except queue.Empty:
                break
        return events

    def submit_action(self, player_id, action_data):
        with self.lock:
            act = action_data.get("action")
            ok, reason = False, "Action inconnue"
            if act == "play_character":
                ok, reason = self.partie.play_character(
                    player_id, action_data["hand_index"], action_data["slot_index"]
                )
            elif act == "play_ref":
                ok, reason = self.partie.play_ref(
                    player_id,
                    action_data["hand_index"],
                    action_data["target_player"],
                    action_data["target_slot"],
                )
            elif act == "pass_turn":
                ok, reason = self.partie.pass_turn(player_id)
            elif act == "surrender":
                ok, reason = self.partie.surrender(player_id)

            if ok:
                self._broadcast_state()
            else:
                if player_id == 1:
                    self.host_events.put({"type": "error", "message": reason})
                elif self.client_sock:
                    try:
                        send_packet(self.client_sock, {"type": "action_error", "message": reason})
                    except Exception:
                        pass

    def _broadcast_state(self):
        state_p1 = self.partie.get_state_for_player(1)
        self.host_events.put({"type": "state_update", "state": state_p1})

        if self.client_sock and self.client_connected:
            state_p2 = self.partie.get_state_for_player(2)
            try:
                send_packet(self.client_sock, {"type": "state_update", "state": state_p2})
            except Exception:
                self._handle_client_disconnect()

    def _handle_client_disconnect(self):
        self.client_connected = False
        if self.client_sock:
            try:
                self.client_sock.close()
            except Exception:
                pass
            self.client_sock = None
        self.host_events.put({
            "type": "opponent_disconnected",
            "message": "Le joueur 2 s'est déconnecté.",
        })

    def _server_loop(self):
        last_ping = time.time()
        while self.running:
            # Attente de connexion du client si non connecté
            if not self.client_connected:
                try:
                    sock, addr = self.server_sock.accept()
                    sock.settimeout(0.2)
                    self.client_sock = sock
                    self.client_addr = addr
                    self.client_connected = True
                    self.host_events.put({
                        "type": "player_joined",
                        "message": f"Joueur 2 connecté ({addr[0]})",
                    })

                    # Envoi message de bienvenue et état initial
                    with self.lock:
                        send_packet(self.client_sock, {
                            "type": "welcome",
                            "player_id": 2,
                            "opponent_name": self.host_name,
                        })
                        self._broadcast_state()
                except socket.timeout:
                    continue
                except Exception:
                    break

            # Lecture des messages du client connecté
            try:
                r, _, _ = select.select([self.client_sock], [], [], 0.3)
                if r:
                    packet = recv_packet(self.client_sock)
                    if packet is None:
                        self._handle_client_disconnect()
                        continue

                    msg_type = packet.get("type")
                    if msg_type == "join":
                        self.client_name = packet.get("name", "Joueur 2")
                        with self.lock:
                            self.partie.players[2].name = self.client_name
                            self._broadcast_state()
                    elif msg_type == "action":
                        self.submit_action(2, packet.get("data", {}))
                    elif msg_type == "ping":
                        send_packet(self.client_sock, {"type": "pong"})
                    elif msg_type == "leave":
                        self._handle_client_disconnect()

                # Keepalive ping
                if time.time() - last_ping > 4.0:
                    send_packet(self.client_sock, {"type": "ping"})
                    last_ping = time.time()

            except (socket.error, ConnectionError):
                self._handle_client_disconnect()
            except Exception:
                pass


class GameClient:
    """Client de jeu local TCP. Se connecte à l'hôte et échange les actions/états."""

    def __init__(self, player_name="Joueur 2"):
        self.player_name = player_name
        self.sock = None
        self.running = False
        self.thread = None
        self.events = queue.Queue()
        self.connected = False
        self.player_id = 2

    def connect(self, host_ip, port=DEFAULT_TCP_PORT, timeout=4.0):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect((host_ip, port))
            self.sock.settimeout(0.2)
            self.connected = True
            self.running = True

            # Envoi du message d'identification
            send_packet(self.sock, {"type": "join", "name": self.player_name})

            self.thread = threading.Thread(target=self._client_loop, daemon=True)
            self.thread.start()
            return True, "Connecté avec succès"
        except socket.timeout:
            return False, "Délai d'attente dépassé (hôte introuvable)"
        except ConnectionRefusedError:
            return False, "Connexion refusée (partie non lancée)"
        except Exception as e:
            return False, f"Erreur de connexion : {e}"

    def disconnect(self):
        self.running = False
        self.connected = False
        if self.sock:
            try:
                send_packet(self.sock, {"type": "leave"})
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def poll_events(self):
        events = []
        while not self.events.empty():
            try:
                events.append(self.events.get_nowait())
            except queue.Empty:
                break
        return events

    def send_action(self, action_data):
        if not self.connected or not self.sock:
            return False
        try:
            send_packet(self.sock, {"type": "action", "data": action_data})
            return True
        except Exception:
            self._handle_disconnect()
            return False

    def _handle_disconnect(self):
        self.connected = False
        self.events.put({
            "type": "disconnected",
            "message": "Connexion avec l'hôte perdue.",
        })

    def _client_loop(self):
        while self.running and self.connected:
            try:
                r, _, _ = select.select([self.sock], [], [], 0.3)
                if r:
                    packet = recv_packet(self.sock)
                    if packet is None:
                        self._handle_disconnect()
                        break

                    msg_type = packet.get("type")
                    if msg_type == "welcome":
                        self.player_id = packet.get("player_id", 2)
                        self.events.put(packet)
                    elif msg_type == "state_update":
                        self.events.put(packet)
                    elif msg_type == "action_error":
                        self.events.put(packet)
                    elif msg_type == "opponent_disconnected":
                        self.events.put(packet)
                    elif msg_type == "ping":
                        send_packet(self.sock, {"type": "pong"})
            except (socket.error, ConnectionError):
                self._handle_disconnect()
                break
            except Exception:
                pass
