# scenes/booster.py
import pygame


class BoosterScene:
    def __init__(self, game):
        self.game = game
        self.BACKGROUND = (20, 24, 36)
        self.GREEN = (65, 190, 130)

        self.PANEL = (29, 35, 51)
        self.BUTTON = (43, 53, 75)
        self.BUTTON_HOVER = (65, 88, 125)
        self.WHITE = (240, 243, 250)
        self.GRAY = (155, 165, 185)
        self.ACCENT = (65, 170, 220)
        self.GREEN = (65, 190, 130)



    def handle_event(self, event):
        pass

    def update(self, dt):
        pass
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
