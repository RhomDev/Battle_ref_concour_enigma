"""Fiches du jeu et lecture locale des médias du catalogue."""

import json
import webbrowser

import pygame

from config import HEIGHT, WIDTH
from core.asset_manager import ROOT, AssetManager
from ui.media_preview import MediaPreview


INK = (255, 243, 222)
MUTED = (209, 184, 179)
GOLD = (232, 192, 114)
PANEL = (43, 21, 27)
BUTTON = (73, 36, 44)
SELECTED = (39, 83, 69)
CARDS_PER_PAGE = 10


class MediaCollectionScene:
    def __init__(self, menu, kind):
        self.menu = menu
        self.game = menu.game
        self.title = "Personnages" if kind == "character" else "Références"
        catalogue = ROOT / "data"
        folder = "card_perso" if kind == "character" else "card_ref"
        self.cards = sorted(
            (json.loads(file.read_text(encoding="utf-8")) for file in (catalogue / folder).glob("*.json")),
            key=lambda card: (card["cost"], card["name"].casefold()),
        )
        self.assets = AssetManager()
        self.font_title = pygame.font.SysFont("arial", 46, bold=True)
        self.font_name = pygame.font.SysFont("arial", 32, bold=True)
        self.font = pygame.font.SysFont("arial", 23)
        self.font_small = pygame.font.SysFont("arial", 19)
        self.font_compact = pygame.font.SysFont("arial", 17)

        self.back_rect = pygame.Rect(WIDTH - 196, 36, 160, 48)
        self.card_rects = [
            pygame.Rect(36 + (i % 2) * 329, 110 + (i // 2) * 52, 319, 42)
            for i in range(min(len(self.cards), CARDS_PER_PAGE))
        ]
        body_top = self.card_rects[-1].bottom + 18 if self.card_rects else 170
        self.page_count = (len(self.cards) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE
        self.prev_rect = pygame.Rect(36, body_top - 5, 172, 32)
        self.next_rect = pygame.Rect(WIDTH - 208, body_top - 5, 172, 32)
        if self.page_count > 1:
            body_top += 42
        self.body = pygame.Rect(36, body_top, WIDTH - 72, HEIGHT - body_top - 30)
        picture_height = min(326, max(145, self.body.height - 520))
        self.picture_rect = pygame.Rect(56, body_top + 101, WIDTH - 112, picture_height)
        self.play_rect = pygame.Rect(56, self.picture_rect.bottom + 75, 250, 46)
        self.video_rect = pygame.Rect(318, self.play_rect.top, 160, 46)
        self.source_rect = pygame.Rect(490, self.play_rect.top, 174, 46)
        self.index = 0
        self.preview = MediaPreview(self.picture_rect.size)
        self.notice = ""
        if self.cards:
            self.select_card(0)

    @property
    def page(self):
        return self.index // CARDS_PER_PAGE

    def select_card(self, index):
        self.preview.stop()
        self.index = index % len(self.cards)
        self.card = self.cards[self.index]
        media = self.assets.media_for(self.card["media"])
        self.audio = media["audio"]
        self.animation = media["gif"]
        self.video = media["video"]
        self.photo = None
        self.notice = ""
        photo = media["image"]
        self.source_url = next(
            (url for item in (self.animation, self.audio, photo)
             if item and (url := item.get("sourceUrl") or item.get("assetUrl"))),
            self.card["origin"]["sources"][0],
        )
        if photo:
            try:
                image = self.assets.load_image(photo["localPath"])
                self.photo = self.preview.fit(image)
            except (OSError, pygame.error):
                self.notice = "Image locale indisponible."

    def play_preview(self):
        self.notice = self.preview.play(self.animation, self.audio)

    def leave(self):
        self.preview.stop()
        self.game.change_scene(self.menu)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.leave()
            elif self.cards and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.select_card(self.index + (-1 if event.key == pygame.K_LEFT else 1))
            elif self.cards and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.play_preview()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.menu.to_canvas_position(event.pos)
            if self.back_rect.collidepoint(mouse):
                self.leave()
                return
            if self.page > 0 and self.prev_rect.collidepoint(mouse):
                self.select_card((self.page - 1) * CARDS_PER_PAGE)
                return
            if self.page < self.page_count - 1 and self.next_rect.collidepoint(mouse):
                self.select_card((self.page + 1) * CARDS_PER_PAGE)
                return
            for index, rect in enumerate(self.card_rects):
                card_index = self.page * CARDS_PER_PAGE + index
                if card_index < len(self.cards) and rect.collidepoint(mouse):
                    self.select_card(card_index)
                    return
            if self.cards and (self.audio or self.animation) and self.play_rect.collidepoint(mouse):
                self.play_preview()
            elif self.cards and self.video and self.video_rect.collidepoint(mouse):
                self.preview.stop()
                if not webbrowser.open((ROOT / self.video["localPath"]).as_uri()):
                    self.notice = "Ouverture de la vidéo indisponible."
            elif self.cards and self.source_rect.collidepoint(mouse):
                if not webbrowser.open(self.source_url):
                    self.notice = "Ouverture de la source indisponible."

    def update(self, dt):
        self.preview.update()

    def fit_label(self, label, font, width):
        if font.size(label)[0] <= width:
            return label
        while label and font.size(label + "…")[0] > width:
            label = label[:-1]
        return label + "…"

    def draw_button(self, surface, rect, label, color):
        pygame.draw.rect(surface, color, rect, border_radius=8)
        text = self.font_small.render(self.fit_label(label, self.font_small, rect.width - 20), True, INK)
        surface.blit(text, text.get_rect(midleft=(rect.left + 10, rect.centery)))

    def draw(self, surface):
        surface.fill((27, 12, 19))
        surface.blit(self.font_title.render(self.title, True, GOLD), (36, 32))
        self.draw_button(surface, self.back_rect, "Retour · Échap", BUTTON)
        start = self.page * CARDS_PER_PAGE
        for i, (rect, card) in enumerate(zip(self.card_rects, self.cards[start:]), start):
            self.draw_button(surface, rect, card["name"], SELECTED if i == self.index else BUTTON)
        if self.page_count > 1:
            if self.page > 0:
                self.draw_button(surface, self.prev_rect, "Page précédente", BUTTON)
            if self.page < self.page_count - 1:
                self.draw_button(surface, self.next_rect, "Page suivante", BUTTON)
            page_label = self.font_small.render(f"{self.page + 1} / {self.page_count}", True, MUTED)
            surface.blit(page_label, page_label.get_rect(center=(WIDTH // 2, self.prev_rect.centery)))
        if not self.cards:
            surface.blit(self.font.render("Aucune carte disponible.", True, MUTED), (36, 110))
            return

        pygame.draw.rect(surface, PANEL, self.body, border_radius=14)
        name = self.font_name.render(self.card["name"], True, INK)
        surface.blit(name, (56, self.body.top + 18))
        year = self.card["origin"]["year"]
        origin = f'{self.card["origin"]["work"]} · {year}'
        origin_font = self.font_small
        if origin_font.size(origin)[0] > self.picture_rect.width:
            origin_font = self.font_compact
        origin = self.fit_label(origin, origin_font, self.picture_rect.width)
        surface.blit(origin_font.render(origin, True, MUTED), (56, self.body.top + 61))

        picture = self.preview.frame or self.photo
        pygame.draw.rect(surface, (25, 14, 19), self.picture_rect, border_radius=8)
        if picture:
            surface.blit(picture, picture.get_rect(center=self.picture_rect.center))
        else:
            message = self.font_small.render("Aucun visuel local disponible", True, MUTED)
            surface.blit(message, message.get_rect(center=self.picture_rect.center))

        line = ""
        line_y = self.picture_rect.bottom + 14
        for word in self.card["text"].split():
            addition = f"{line} {word}".lstrip()
            if self.font.size(addition)[0] > self.picture_rect.width and line:
                surface.blit(self.font.render(line, True, INK), (56, line_y))
                line_y += 27
                line = word
            else:
                line = addition
        surface.blit(self.font.render(line, True, INK), (56, line_y))

        preview = self.audio or self.animation
        notice_y = self.play_rect.bottom + 7
        self.draw_button(surface, self.source_rect, "Source originale", BUTTON)
        if self.video:
            self.draw_button(surface, self.video_rect, "Vidéo locale", BUTTON)
        if preview:
            playing = self.preview.playing
            self.draw_button(surface, self.play_rect, "Relancer l’aperçu" if playing else "Lire l’aperçu · Espace", SELECTED)
            if preview.get("caption"):
                caption = self.fit_label(preview["caption"], self.font_small, self.picture_rect.width)
                surface.blit(self.font_small.render(caption, True, GOLD), (56, notice_y))
                notice_y += 23
        notice = self.notice
        if not preview and not notice:
            notice = "Aucun aperçu audio ou animé disponible."
        if notice:
            surface.blit(self.font_small.render(notice, True, MUTED), (56, notice_y))
