import json
import pygame

def read_json(path):
    with open(path, "r", encoding="utf-8") as fichier:
        data = json.load(fichier)
    return data


class Personage_Kard:
    def __init__(self, json_name):
        data = read_json(json_name)

        # Data
        self.nom = data["name"]
        self.image = pygame.image.load(data["image"]).convert_alpha()

        self.attack = data["attack"]

        self.celebrate = data["celebrate"]
        self.rarity = data["rarity"]

        self.weakness = data["weakness"]
        self.strength = data["strength"]
        self.combination = data["combination"]

        # Position
        self.coord = pygame.Vector2(0, 0)
        self.base_coord = pygame.Vector2(0, 0)
        self.target_coord = pygame.Vector2(0, 0)

        # Animation
        self.scale = 1.0
        self.target_scale = 1.0

        self.angle = 0
        self.target_angle = 0

        # Hover
        self.is_hovered = False

        # Shake
        self.shaking = False
        self.shake_timer = 0
        self.shake_duration = 0
        self.shake_power = 0
        self.shake_offset = pygame.Vector2(0, 0)

        # Flip
        self.flipping = False
        self.flip_progress = 0
        self.flip_speed = 5
        self.flip_finished = False

        # Selection
        self.selected = False

        # ---------------------------------
        # DEPLACEMENT
        # ---------------------------------

    def move_to(self, x, y):

        self.target_coord = pygame.Vector2(x, y)
        self.base_coord = pygame.Vector2(x, y)

        # ---------------------------------
        # HOVER
        # ---------------------------------

    def hover(self, mouse_pos):

        rect = self.image.get_rect(
            center=(round(self.coord.x), round(self.coord.y))
        )

        self.is_hovered = rect.collidepoint(mouse_pos)

        if self.is_hovered:

            self.target_coord.y = self.base_coord.y - 30
            self.target_scale = 1.12

        else:

            self.target_coord = self.base_coord.copy()

            if not self.selected:
                self.target_scale = 1.0

        # ---------------------------------
        # TILT
        # ---------------------------------

    def tilt(self, mouse_pos):

        if self.is_hovered:

            center_x = self.coord.x

            difference = mouse_pos[0] - center_x

            self.target_angle = max(
                -12, min(12, difference * 0.04)
            )

        else:
            self.target_angle = 0

        # ---------------------------------
        # SHAKE
        # ---------------------------------

    def shake(self, duration=0.4, power=8):

        self.shaking = True
        self.shake_timer = 0
        self.shake_duration = duration
        self.shake_power = power

        # ---------------------------------
        # FLIP
        # ---------------------------------

    def flip(self):

        if not self.flipping:
            self.flipping = True
            self.flip_progress = 0
            self.flip_finished = False

        # ---------------------------------
        # SELECT
        # ---------------------------------

    def select(self):

        self.selected = not self.selected

        if self.selected:
            self.target_scale = 1.2
            self.target_coord.y = self.base_coord.y - 40

        else:
            self.target_scale = 1.0
            self.target_coord = self.base_coord.copy()

        # ---------------------------------
        # UPDATE
        # ---------------------------------

    def update(self, dt):

        # Déplacement fluide
        self.coord += (
                              self.target_coord - self.coord
                      ) * min(1, 12 * dt)

        # Taille fluide
        self.scale += (
                              self.target_scale - self.scale
                      ) * min(1, 12 * dt)

        # Rotation fluide
        self.angle += (
                              self.target_angle - self.angle
                      ) * min(1, 15 * dt)

        # Shake
        self.shake_offset.update(0, 0)

        if self.shaking:

            self.shake_timer += dt

            if self.shake_timer >= self.shake_duration:
                self.shaking = False

            else:
                intensity = (
                                    1 - self.shake_timer / self.shake_duration
                            ) * self.shake_power

                self.shake_offset.x = random.uniform(
                    -intensity, intensity
                )

                self.shake_offset.y = random.uniform(
                    -intensity, intensity
                )

        # Flip
        if self.flipping:

            self.flip_progress += self.flip_speed * dt

            if self.flip_progress >= math.pi:
                self.flip_progress = 0
                self.flipping = False
                self.flip_finished = True

        # ---------------------------------
        # DRAW
        # ---------------------------------

    def draw(self, screen):

        width = max(1, int(self.image.get_width() * self.scale))
        height = max(1, int(self.image.get_height() * self.scale))

        image = pygame.transform.smoothscale(
            self.image, (width, height)
        )

        # Flip horizontal
        if self.flipping:
            flip_scale = abs(math.cos(self.flip_progress))

            width_flip = max(1, int(image.get_width() * flip_scale))

            image = pygame.transform.smoothscale(
                image,
                (width_flip, image.get_height())
            )

        # Rotation
        image = pygame.transform.rotate(image, self.angle)

        rect = image.get_rect(
            center=(
                round(self.coord.x + self.shake_offset.x),
                round(self.coord.y + self.shake_offset.y)
            )
        )

        screen.blit(image, rect)

class Ref_Kard:
    def __init__(self, json_name):
        data = read_json(json_name)

        self.coord = (0, 0)
        self.cache = False

        self.name_perso = data["name_pers"]
        self.name = data["name"]

        self.gif = pygame.image.load(data["gif"]).convert_alpha()
        self.image = pygame.image.load(data["image"]).convert_alpha()
        self.sound = pygame.image.load(data["sound"]).convert_alpha()

        self.cost = data["cost"]

        self.damage = data["damage"]
        self.cooldown = data["cooldown"]

        self.effect = data["effect"]
        self.value_effect = data["value_effect"]

    def update(self, screen):
        screen.blit(self.image, self.coord)
