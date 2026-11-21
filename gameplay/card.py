import json
import pygame

def read_json(path):
    with open("data/"+path+".json", "r", encoding="utf-8") as fichier:
        data = json.load(fichier)
    return data

class Card_Item:
    def __init__(self, json_name, cat):
        data = read_json(cat+"/" + json_name)

        self.type = data["kind"]
        self.id = data["id"]

        self.name = data["name"]

        self.PV_init = data["stats"]["hp"]
        self.PV_actu = self.PV_init

        self.shield = 0

        self.cost = data["cost"]

        self.category = data["category"]

        self.text = data["text"]

        if self.type == "ref":

            self.amount = data["abilities"]["effects"]["amount"]
            self.op = data["abilities"]["effect"]["op"]

            self.id_effect = data["id_character"]
            self.effect = data["effect"]
            self.effect_amount = data["effect_amount"]

        self.x = 0
        self.y = 0

        self.width = 800
        self.height = 200

        self.hitbox = pygame.Rect(self.x, self.y, self.width, self.height)

        if self.type =="character":
            background_path = "asset/frames/personnage.png"
        elif self.type =="ref":
            background_path = "asset/frames/ref.png"
        else:
            background_path = ""

        self.background = pygame.image.load(
            background_path
        ).convert_alpha()
        self.background = pygame.transform.smoothscale(
            self.background, self.hitbox.size
        )

        self.profile = pygame.image.load(
            "asset/image/catalogue/"+json_name+".webp"
        ).convert_alpha()
        self.profile = pygame.transform.smoothscale(
            self.profile, (120, 140)
        )

        self.font = pygame.font.SysFont(None, 26)


    def ability(self):
        if self.effect == "add":
            self.amount += self.effect_amount

    def attacking(self, attacker):
        if self.sheild > 0:
            attacker -= self.shield
            self.shield = 0
        if attacker > 0:
            self.PV_actu -= attacker
        return self.PV_actu

    def healing(self, healer):
        if self.PV_actu < self.PV_init:
            self.PV_actu += healer
        if self.PV_actu > self.PV_init:
            self.PV_actu = self.PV_init

    def shielding(self, shield):
        self.shield += shield

    def draw(self, surface):
        rect = self.hitbox

        # Fond
        surface.blit(self.background, rect.topleft)

        # Image du personnage
        profile_x = rect.x + 20
        profile_y = rect.y + 25

        surface.blit(
            self.profile,
            (profile_x, profile_y)
        )

        # Nom
        text_name = self.font.render(
            self.name, True, (255, 255, 255)
        )
        name_rect = text_name.get_rect(
            center=(rect.centerx, rect.y + 12)
        )
        surface.blit(text_name, name_rect)

        # Catégorie
        text_category = self.font.render(
            str(self.category), True, (220, 220, 220)
        )
        category_rect = text_category.get_rect(
            center=(rect.centerx, rect.y + 178)
        )
        surface.blit(text_category, category_rect)

        # Description
        text_description = self.font.render(
            str(self.text), True, (255, 255, 255)
        )
        description_rect = text_description.get_rect(
            center=(rect.centerx, rect.y + 198)
        )
        surface.blit(text_description, description_rect)
