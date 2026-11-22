import ipaddress
import json
import select
import socket
from queue import Empty, Queue
from threading import Event, Thread
from time import monotonic

from gameplay.partie import Partie


PORT = 51427
VERSION = 1
MAX_FRAME = 65536
HANDSHAKE_TIMEOUT = 6
HEARTBEAT_INTERVAL = 4
DISCONNECT_TIMEOUT = 15


class _Channel:
    def __init__(self, sock):
        self.sock = sock
        self.sock.settimeout(0.75)
        self.buffer = bytearray()
        self.last_seen = monotonic()

    def send(self, **message):
        self.sock.sendall(json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode() + b"\n")

    def receive(self):
        data = self.sock.recv(8192)
        if not data:
            raise ConnectionError
        self.buffer.extend(data)
        while (end := self.buffer.find(b"\n")) >= 0:
            if end > MAX_FRAME:
                raise ValueError("Message trop long")
            frame = bytes(self.buffer[:end])
            del self.buffer[:end + 1]
            message = json.loads(frame.decode())
            if not isinstance(message, dict):
                raise ValueError("Message invalide")
            self.last_seen = monotonic()
            yield message
        if len(self.buffer) > MAX_FRAME:
            raise ValueError("Message trop long")


class BattleSession:
    """One worker owns the current game or its client connection."""

    def __init__(self, catalogue, mode, address="", *, port=PORT):
        self.catalogue = catalogue
        self.mode = mode
        self.address = address
        self.port = port
        self.events = Queue()
        self.actions = Queue()
        self.stopped = Event()
        self.worker = Thread(target=self._run, daemon=True)
        self.worker.start()

    def close(self):
        self.stopped.set()

    def submit(self, action):
        if not self.stopped.is_set():
            self.actions.put(action)

    def poll(self):
        events = []
        while (event := self._take(self.events)) is not None:
            events.append(event)
        return events

    @staticmethod
    def _take(queue):
        try:
            return queue.get_nowait()
        except Empty:
            return None

    def _emit(self, kind, value):
        if not self.stopped.is_set():
            self.events.put({"type": kind, "value": value})

    def _run(self):
        try:
            if self.mode == "solo":
                self._solo()
            elif self.mode == "host":
                self._host()
            else:
                self._join()
        except OSError:
            detail = ("Impossible d’ouvrir la partie sur cette adresse."
                      if self.mode == "host" else "Connexion impossible. Vérifiez l’adresse et le Wi-Fi.")
            self._emit("closed", detail)

    def _solo(self):
        game = Partie(self.catalogue)
        self._emit("state", game.view(1))
        next_bot_move = monotonic() + 0.45
        while not self.stopped.wait(0.04):
            action = self._take(self.actions)
            if action is not None:
                error = game.apply(1, action)
                self._emit("error" if error else "state", error or game.view(1))
                next_bot_move = monotonic() + 0.45
            if game.result is None and game.active == 2 and monotonic() >= next_bot_move:
                game.apply(2, game.bot_action(2))
                self._emit("state", game.view(1))
                next_bot_move = monotonic() + 0.30

    def _host(self):
        channels = {}
        peer = None
        game = None
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.address, self.port))
            server.listen(5)
            server.setblocking(False)
            self._emit("waiting", {"address": self.address, "port": server.getsockname()[1]})
            try:
                while not self.stopped.is_set():
                    ready, _, _ = select.select([server, *channels], [], [], 0.05)
                    if server in ready:
                        incoming, _ = server.accept()
                        ready.remove(server)
                        if len(channels) >= 5:
                            incoming.close()
                        else:
                            channels[incoming] = _Channel(incoming)
                    if peer is not None:
                        action = self._take(self.actions)
                        if action is not None:
                            self._host_action(game, peer, 1, action)
                    for sock, channel in list(channels.items()):
                        timeout = DISCONNECT_TIMEOUT if channel is peer else HANDSHAKE_TIMEOUT
                        try:
                            if monotonic() - channel.last_seen > timeout:
                                raise TimeoutError
                            if sock not in ready:
                                continue
                            for message in channel.receive():
                                if channel is peer:
                                    if message.get("type") == "ping":
                                        peer.send(type="pong")
                                    else:
                                        self._host_action(game, peer, 2, message)
                                else:
                                    rejection = self._rejection(message, peer is not None)
                                    if rejection:
                                        channel.send(type="closed", value=rejection)
                                        raise ConnectionError
                                    peer = channel
                                    game = Partie(self.catalogue)
                                    self._publish(game, peer)
                        except (OSError, ValueError, RecursionError):
                            channels.pop(sock).sock.close()
                            if channel is peer:
                                self._emit("closed", "L’adversaire s’est déconnecté.")
                                return
            except OSError:
                if peer is None:
                    raise
                self._emit("closed", "L’adversaire s’est déconnecté.")
            finally:
                for sock in channels:
                    sock.close()

    def _rejection(self, message, full):
        if (message.get("type") != "hello" or type(message.get("version")) is not int
                or message["version"] != VERSION or message.get("catalogue") != self.catalogue.fingerprint):
            return "Versions incompatibles. Utilisez la même version du jeu."
        if full:
            return "Cette partie est complète."
        return None

    def _host_action(self, game, peer, player, action):
        error = game.apply(player, action)
        if not error:
            self._publish(game, peer)
        elif player == 1:
            self._emit("error", error)
        else:
            peer.send(type="error", value=error)

    def _publish(self, game, peer):
        self._emit("state", game.view(1))
        peer.send(type="state", value=game.view(2))

    def _join(self):
        try:
            address = str(ipaddress.IPv4Address(self.address))
        except ValueError:
            self._emit("closed", "Saisissez une adresse IPv4 valide, par exemple 192.168.1.20.")
            return
        connected = False
        try:
            with socket.create_connection((address, self.port), timeout=HANDSHAKE_TIMEOUT) as sock:
                if self.stopped.is_set():
                    return
                channel = _Channel(sock)
                channel.send(type="hello", version=VERSION, catalogue=self.catalogue.fingerprint)
                next_ping = monotonic() + HEARTBEAT_INTERVAL
                while not self.stopped.is_set():
                    if select.select([sock], [], [], 0.05)[0]:
                        for message in channel.receive():
                            kind = message.get("type")
                            if kind == "state" and isinstance(message.get("value"), dict):
                                connected = True
                                self._emit(kind, message["value"])
                            elif kind in ("error", "closed") and isinstance(message.get("value"), str):
                                self._emit(kind, message["value"])
                                if kind == "closed":
                                    return
                            elif kind != "pong":
                                raise ValueError("Réponse invalide")
                    now = monotonic()
                    if now - channel.last_seen > (DISCONNECT_TIMEOUT if connected else HANDSHAKE_TIMEOUT):
                        raise TimeoutError
                    if connected:
                        action = self._take(self.actions)
                        if action is not None:
                            channel.send(**action)
                        if now >= next_ping:
                            channel.send(type="ping")
                            next_ping = now + HEARTBEAT_INTERVAL
        except (OSError, ValueError, RecursionError):
            detail = ("La connexion avec l’hôte a été perdue." if connected else
                      "Connexion impossible. Vérifiez l’adresse et le Wi-Fi.")
            self._emit("closed", detail)
