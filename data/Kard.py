import json
import pygame

def read_json(path):
    with open("data.json", "r", encoding="utf-8") as fichier:
        data = json.load(fichier)
    return data


class Personage_Kard:
    def __init__(self, json_name):
        data = read_json(open(json_name))

        self.coord = (0, 0)
        self.cache = False

        self.nom = data["name"]
        self.image = pygame.image.load(data["image"]).convert_alpha()

        self.attack = data["attack"]

        self.celebrate = data["celebrate"]
        self.rarity = data["rarity"]

        self.weakness = data["weakness"]
        self.strength = data["strength"]
        self.combination = data["combination"]

    def update(self, screen):
        screen.blit(self.image, self.coord)


class Ref_Kard:
    def __init__(self, json_name):
        data = read_json(open(json_name))

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
