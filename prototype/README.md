# Battle Ref Arena · prototype

Ouvrir [`../apercu/index.html`](../apercu/index.html) dans un navigateur. La scène guidée et les médias locaux fonctionnent hors ligne. Cliquer sur « Piocher · 1 ⚡ » pour commencer le tour ou sur une carte pour l’examiner. Le bouton Cartes ouvre le catalogue et permet de chercher par nom, œuvre ou Personnage associé. Options donne accès aux crédits et au volume.

Cet aperçu sert de référence au développement du jeu en **Python avec Pygame**. Les consignes de portage sont dans [AGENTS.md](../AGENTS.md).

- [Aperçu du plateau](../apercu/index.html) et [capture PNG de la première démo](../asset/image/maquettes/plateau.png).
- [Directions visuelles](directions.html) et [planche PNG](../asset/image/maquettes/directions.png).
- [Premières maquettes de cartes en PNG](../asset/image/maquettes/) et [leurs crédits historiques](docs/recherche.md#crédits-des-premières-maquettes).
- [Recherche culturelle et état des médias](docs/recherche.md).
- [Audit, règles, dix synergies, architecture, pipeline et roadmap](docs/conception.md).
- [Prompts du plateau et des cadres](docs/prompts-cadres.md), maîtres PNG et dérivés WebP dans `../asset/frames/`, fond illustré dans `../asset/board/`.
- [Cartes compilées](../data/cartes.json), [fiches éditables](../data/README.md), [synergies](../data/synergies.json), [médias et crédits](../data/medias.json).
- Schémas JSON pour les [cartes](../data/schemas/carte.schema.json), les [synergies](../data/schemas/synergie.schema.json) et les [médias](../data/schemas/media.schema.json).

Avec 5 énergies, la scène propose de piocher Macron pour 1, de le déployer pour 2, puis de jouer Y.M.C.A. pour 2. Trump amplifie la Ref et Vegeta protège le joueur adverse. À la résolution, la projection diffuse six secondes de la vraie danse de Trump à Norfolk. Si le son est activé dans Options, elle joue aussi six secondes de l’enregistrement original des Village People depuis le MP3 local.

Dans le catalogue, **Tester les médias** lit les fichiers disponibles sur la carte. Les fiches de Vegeta et de Mista affichent les visuels officiels des séries. Les fiches donnent accès aux fichiers téléchargeables et aux pages de leur diffuseur.

Les polices Barlow Condensed et Instrument Sans sont servies localement. Leurs licences sont dans [asset/fonts/](../asset/fonts/).

Pour modifier les données, éditer les fiches individuelles, les synergies ou le registre média. Python 3 et `jsonschema` sont nécessaires pour contrôler les données et reconstruire le catalogue agrégé et l’instantané JavaScript.

```bash
python3 outils/valider.py --apercu
```
