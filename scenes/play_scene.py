import ipaddress

import ifaddr
import pygame

from config import HEIGHT, WIDTH
from core.battle_session import BattleSession
from gameplay.partie import Catalogue
from scenes.battle_scene import BattleScene
from scenes.media_collection import GOLD, INK
from ui.fonts import interface_font


class PlayScene:
    def __init__(self, menu):
        self.menu = menu
        self.game = menu.game
        self.catalogue = None
        self.session = None
        self.mode = "choices"
        self.notice = ""
        self.address = ""
        self.interfaces = []
        self.font = interface_font(36, bold=True)
        self.small = interface_font(26)
        self.back_rect = pygame.Rect(36, 38, 158, 64)
        self.buttons = [pygame.Rect(64, 660 + index * 108, WIDTH - 128, 80) for index in range(3)]

    def start(self, mode, address=""):
        if self.catalogue is None:
            self.catalogue = Catalogue()
        self.mode = mode
        self.notice = ""
        pygame.key.stop_text_input()
        self.session = BattleSession(self.catalogue, mode, address)

    def close(self):
        pygame.key.stop_text_input()
        if self.session:
            self.session.close()
            self.session = None

    def return_with_notice(self, notice):
        self.close()
        self.mode = "choices"
        self.notice = notice

    def back(self):
        if self.mode == "choices":
            self.game.change_scene(self.menu)
        else:
            self.return_with_notice("")

    def choose_host(self):
        self.interfaces = sorted({
            entry.ip
            for adapter in ifaddr.get_adapters()
            for entry in adapter.ips
            if isinstance(entry.ip, str) and not ipaddress.IPv4Address(entry.ip).is_loopback
            and not ipaddress.IPv4Address(entry.ip).is_link_local
        })
        if not self.interfaces:
            self.notice = "Connectez-vous à un réseau Wi-Fi ou Ethernet."
        elif len(self.interfaces) == 1:
            self.start("host", self.interfaces[0])
        else:
            self.mode = "interface"
            self.notice = ""

    def join(self):
        self.mode = "address"
        self.notice = ""
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(self.buttons[0])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back()
        elif self.mode == "address" and event.type == pygame.TEXTINPUT:
            digits = "".join(char for char in event.text if char in "0123456789.")
            self.address = (self.address + digits)[:15]
        elif self.mode == "address" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.address = self.address[:-1]
            elif event.key == pygame.K_RETURN:
                self.start("join", self.address)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.menu.to_canvas_position(event.pos)
            if self.back_rect.collidepoint(pos):
                self.back()
            elif self.mode == "choices":
                for button, handler in zip(self.buttons, (lambda: self.start("solo"), self.choose_host, self.join)):
                    if button.collidepoint(pos):
                        handler()
                        break
            elif self.mode == "address" and self.buttons[1].collidepoint(pos):
                self.start("join", self.address)
            elif self.mode == "interface":
                for rect, address in self.interface_rows():
                    if rect.collidepoint(pos):
                        self.start("host", address)
                        break

    def interface_rows(self):
        return [(pygame.Rect(64, 640 + index * 56, WIDTH - 128, 50), address)
                for index, address in enumerate(self.interfaces[:10])]

    def update(self, dt):
        if self.session is None:
            return
        state = None
        for event in self.session.poll():
            if event["type"] == "waiting":
                self.notice = event["value"]["address"]
            elif event["type"] == "closed":
                self.return_with_notice(event["value"])
                return
            elif event["type"] == "state":
                state = event["value"]
        if state:
            session, self.session = self.session, None
            self.game.change_scene(BattleScene(self, session, state))

    def draw(self, surface):
        surface.blit(self.menu.background, (0, 0))
        label = self.menu.draw_centered
        title = {
            "choices": "Jouer",
            "solo": "Mode solo",
            "interface": "Choisir l’adresse de l’hôte",
            "host": "Créer une partie",
            "address": "Rejoindre une partie",
            "join": "Connexion…",
        }[self.mode]
        label(surface, title, self.font, INK, (WIDTH // 2, 430))
        self.draw_button(surface, self.back_rect, "Retour" if self.mode == "choices" else "Annuler")
        if self.mode == "choices":
            for rect, name in zip(self.buttons, ("Solo", "Créer une partie", "Rejoindre une partie")):
                self.draw_button(surface, rect, name)
            label(surface, self.notice, self.small, GOLD, (WIDTH // 2, HEIGHT - 240))
        elif self.mode == "host":
            label(surface, self.notice or "Ouverture de la partie…", self.font, GOLD, (WIDTH // 2, 685))
            label(surface, "En attente d’un joueur sur le même Wi-Fi", self.small, INK, (WIDTH // 2, 763))
        elif self.mode == "interface":
            for rect, address in self.interface_rows():
                self.draw_button(surface, rect, address)
        elif self.mode == "address":
            label(surface, "Adresse IPv4 affichée par l’hôte", self.small, INK, (WIDTH // 2, 604))
            self.draw_button(surface, self.buttons[0], self.address or "192.168.1.20", muted=not self.address)
            self.draw_button(surface, self.buttons[1], "Se connecter")

    def draw_button(self, surface, rect, name, *, muted=False):
        hovered = rect.collidepoint(self.menu.to_canvas_position(pygame.mouse.get_pos()))
        pygame.draw.rect(surface, (39, 48, 65) if hovered else (29, 35, 51), rect, border_radius=12)
        pygame.draw.rect(surface, GOLD, rect, width=2, border_radius=12)
        self.menu.draw_centered(surface, name, self.small, (168, 167, 170) if muted else INK, rect.center)
