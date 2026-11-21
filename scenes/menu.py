
import pygame
from config import WIDTH, HEIGHT
from scenes.booster import BoosterScene
from scenes.media_collection import MediaCollectionScene


class MenuScene:
    def __init__(self, game):
        self.game = game

        # Couleurs
        self.BACKGROUND = (20, 24, 36)
        self.PANEL = (29, 35, 51)
        self.BUTTON = (43, 53, 75)
        self.BUTTON_HOVER = (65, 88, 125)
        self.WHITE = (240, 243, 250)
        self.GRAY = (155, 165, 185)
        self.ACCENT = (65, 170, 220)
        self.GREEN = (65, 190, 130)

        # Polices
        self.font_title = pygame.font.SysFont(
            "arial", max(20, int(HEIGHT * 0.045)), bold=True
        )
        self.font_button = pygame.font.SysFont(
            "arial", max(18, int(HEIGHT * 0.033)), bold=True
        )
        self.font_small = pygame.font.SysFont(
            "arial", max(15, int(HEIGHT * 0.025))
        )

        # Dimensions générales
        self.panel = pygame.Rect(
            int(WIDTH * 0.055),
            int(HEIGHT * 0.04),
            int(WIDTH * 0.89),
            int(HEIGHT * 0.92)
        )

        # Informations du joueur
        self.pseudo = "JOUEUR"
        self.niveau = "NIVEAU 1"

        self.pseudo_rect = pygame.Rect(
            int(WIDTH * 0.075),
            int(HEIGHT * 0.055),
            int(WIDTH * 0.37),
            int(HEIGHT * 0.105)
        )

        self.niveau_rect = pygame.Rect(
            int(WIDTH * 0.555),
            int(HEIGHT * 0.055),
            int(WIDTH * 0.37),
            int(HEIGHT * 0.105)
        )

        # Photo de profil
        self.profile_center = (
            WIDTH // 2,
            int(HEIGHT * 0.365)
        )

        self.profile_radius = int(min(WIDTH * 0.13, HEIGHT * 0.17))

        self.plus_center = (
            self.profile_center[0] + int(self.profile_radius * 0.78),
            self.profile_center[1] - int(self.profile_radius * 0.78)
        )

        self.plus_radius = max(20, int(HEIGHT * 0.038))

        self.plus_rect = pygame.Rect(
            self.plus_center[0] - self.plus_radius,
            self.plus_center[1] - self.plus_radius,
            self.plus_radius * 2,
            self.plus_radius * 2
        )

        # Boutons principaux
        button_width = int(WIDTH * 0.39)
        button_height = int(HEIGHT * 0.105)

        left_x = int(WIDTH * 0.10)
        right_x = int(WIDTH * 0.51)

        row1_y = int(HEIGHT * 0.59)
        row2_y = int(HEIGHT * 0.76)

        self.buttons = {
            "GAME": pygame.Rect(
                left_x, row1_y, button_width, button_height
            ),

            "PERSONNAGE": pygame.Rect(
                right_x, row1_y, button_width, button_height
            ),

            "REF": pygame.Rect(
                left_x, row2_y, button_width, button_height
            ),

            "BOOSTER": pygame.Rect(
                right_x, row2_y, button_width, button_height
            ),

            "QUITTER": pygame.Rect(
                right_x, row2_y + 100, button_width, button_height
            )
        }

        # Animation
        self.hover_scale = {name: 0.0 for name in self.buttons}

    # -------------------------------------------------
    # CONVERSION DES COORDONNEES SOURIS
    # -------------------------------------------------

    def to_canvas_position(self, pos):
        """
        Convertit les coordonnées de la fenêtre
        vers celles du canvas logique.
        """

        window_w, window_h = self.game.screen.get_size()

        scale = min(
            window_w / WIDTH,
            window_h / HEIGHT
        )

        offset_x = (window_w - WIDTH * scale) / 2
        offset_y = (window_h - HEIGHT * scale) / 2

        x = (pos[0] - offset_x) / scale
        y = (pos[1] - offset_y) / scale

        return int(x), int(y)

    # -------------------------------------------------
    # GESTION DES EVENEMENTS
    # -------------------------------------------------

    def handle_event(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:

                mouse_pos = self.to_canvas_position(event.pos)

                # Bouton GAME
                if self.buttons["GAME"].collidepoint(mouse_pos):
                    self.open_game()

                # Bouton PERSONNAGE
                elif self.buttons["PERSONNAGE"].collidepoint(mouse_pos):
                    self.open_personnages()

                # Bouton REF
                elif self.buttons["REF"].collidepoint(mouse_pos):
                    self.open_references()

                # Bouton BOOSTER
                elif self.buttons["BOOSTER"].collidepoint(mouse_pos):
                    self.open_booster()
                # Bouton QUITTER
                elif self.buttons["QUITTER"].collidepoint(mouse_pos):
                    self.game.running = False

                # Ajouter une image de profil
                elif self.plus_rect.collidepoint(mouse_pos):
                    self.add_profile_image()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.running = False

    # -------------------------------------------------
    # ACTIONS DES BOUTONS
    # -------------------------------------------------

    def open_game(self):
        print("Lancement du jeu")

        # TODO :
        # Ajouter ici le changement vers BattleScene.

    def open_personnages(self):
        self.game.change_scene(MediaCollectionScene(self, "character"))

    def open_references(self):
        self.game.change_scene(MediaCollectionScene(self, "ref"))

    def add_profile_image(self):
        print("Ajout d'une image de profil")

        # TODO :
        # Ajouter un système de sélection d'image.

    def open_booster(self):
        self.game.change_scene(BoosterScene(self.game))
    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------

    def update(self, dt):

        mouse_pos = self.to_canvas_position(
            pygame.mouse.get_pos()
        )

        # Animation de survol des boutons
        for name, rect in self.buttons.items():

            if rect.collidepoint(mouse_pos):
                target = 1.0
            else:
                target = 0.0

            self.hover_scale[name] += (
                target - self.hover_scale[name]
            ) * min(1.0, dt * 10)

    # -------------------------------------------------
    # DESSIN DES ELEMENTS
    # -------------------------------------------------

    def draw_text_center(self, surface, text, font, color, rect):

        rendered = font.render(text, True, color)

        text_rect = rendered.get_rect(
            center=rect.center
        )

        surface.blit(rendered, text_rect)

    def draw_header(self, surface):

        # Fond du pseudo
        pygame.draw.rect(
            surface,
            self.BUTTON,
            self.pseudo_rect,
            border_radius=12
        )

        # Fond du niveau
        pygame.draw.rect(
            surface,
            self.BUTTON,
            self.niveau_rect,
            border_radius=12
        )

        pygame.draw.rect(
            surface,
            self.GRAY,
            self.pseudo_rect,
            2,
            border_radius=12
        )

        pygame.draw.rect(
            surface,
            self.GRAY,
            self.niveau_rect,
            2,
            border_radius=12
        )

        self.draw_text_center(
            surface,
            self.pseudo,
            self.font_title,
            self.WHITE,
            self.pseudo_rect
        )

        self.draw_text_center(
            surface,
            self.niveau,
            self.font_title,
            self.WHITE,
            self.niveau_rect
        )

    def draw_profile(self, surface):

        # Ombre
        pygame.draw.circle(
            surface,
            (12, 16, 26),
            (self.profile_center[0] + 5,
             self.profile_center[1] + 7),
            self.profile_radius
        )

        # Fond du profil
        pygame.draw.circle(
            surface,
            self.BUTTON,
            self.profile_center,
            self.profile_radius
        )

        # Silhouette du joueur
        head_radius = int(self.profile_radius * 0.23)

        pygame.draw.circle(
            surface,
            self.GRAY,
            (
                self.profile_center[0],
                self.profile_center[1] - int(self.profile_radius * 0.25)
            ),
            head_radius
        )

        body_rect = pygame.Rect(
            self.profile_center[0] - int(self.profile_radius * 0.48),
            self.profile_center[1] + int(self.profile_radius * 0.08),
            int(self.profile_radius * 0.96),
            int(self.profile_radius * 0.62)
        )

        pygame.draw.ellipse(
            surface,
            self.GRAY,
            body_rect
        )

        # Contour du profil
        pygame.draw.circle(
            surface,
            self.ACCENT,
            self.profile_center,
            self.profile_radius,
            4
        )

        # Bouton +
        pygame.draw.circle(
            surface,
            self.GREEN,
            self.plus_center,
            self.plus_radius
        )

        pygame.draw.circle(
            surface,
            self.WHITE,
            self.plus_center,
            self.plus_radius,
            3
        )

        plus = self.font_title.render(
            "+", True, self.WHITE
        )

        surface.blit(
            plus,
            plus.get_rect(center=self.plus_center)
        )

    def draw_buttons(self, surface):

        for name, rect in self.buttons.items():

            hover = self.hover_scale[name]

            # Interpolation de la couleur
            color = tuple(
                int(self.BUTTON[i] +
                    (self.BUTTON_HOVER[i] - self.BUTTON[i]) * hover)
                for i in range(3)
            )

            # Légère mise en avant au survol
            expanded = rect.inflate(
                int(hover * 4),
                int(hover * 4)
            )

            pygame.draw.rect(
                surface,
                color,
                expanded,
                border_radius=14
            )

            pygame.draw.rect(
                surface,
                self.ACCENT if hover > 0.1 else self.GRAY,
                expanded,
                2,
                border_radius=14
            )

            self.draw_text_center(
                surface,
                name,
                self.font_button,
                self.WHITE,
                expanded
            )

    # -------------------------------------------------
    # DRAW
    # -------------------------------------------------

    def draw(self, surface):

        # Fond général
        surface.fill(self.BACKGROUND)

        # Panneau principal
        pygame.draw.rect(
            surface,
            self.PANEL,
            self.panel,
            border_radius=22
        )

        pygame.draw.rect(
            surface,
            (65, 78, 105),
            self.panel,
            3,
            border_radius=22
        )

        # Eléments du menu
        self.draw_header(surface)
        self.draw_profile(surface)
        self.draw_buttons(surface)
