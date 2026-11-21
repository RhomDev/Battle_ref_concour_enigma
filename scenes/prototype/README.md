# Battle Ref Arena · prototype

Ouvrir `apercu.html` dans un navigateur. Le dossier fonctionne localement sans compilation ni connexion. La table de projection bordeaux sert de fond au plateau. Cliquer sur une carte pour l’examiner, ou sur « Jouer la Ref » pour déclencher la scène. Le bouton Cartes ouvre les 15 fiches et les crédits photo se trouvent dans Options.

Cet aperçu sert de référence au développement du jeu en **Python avec Pygame**. Les consignes de portage sont dans [AGENTS.md](../AGENTS.md).

- [Aperçu du plateau](apercu.html) et [capture PNG du plateau](plateau.png).
- [Directions visuelles](directions.html) et [planche PNG](directions.png).
- Cartes en PNG dans [exemples/](exemples/) · [Donald Trump](exemples/personnage-trump.png), [Emmanuel Macron](exemples/personnage-macron.png), [PSY](exemples/personnage-psy.png), [Poudre de perlimpinpin](exemples/ref-perlimpinpin.png), [Y.M.C.A.](exemples/ref-ymca.png), [Canzoni preferite](exemples/ref-jojo.png), [Touche pas à ma Bulma !](exemples/ref-bulma.png) et [Sssplendide !](exemples/ref-mask.png).
- [Recherche culturelle et état des médias](docs/recherche.md).
- [Audit, règles, dix synergies, architecture, pipeline et roadmap](docs/conception.md).
- [Prompts du plateau et des cadres](docs/prompts-cadres.md), maîtres PNG et dérivés WebP dans `assets/frames/`, fond illustré dans `assets/board/`.
- [Cartes](catalogue/cartes.json), fiches JSON individuelles dans `catalogue/fiches/`, [synergies](catalogue/synergies.json), [médias et crédits](catalogue/medias.json).
- Schémas JSON pour les [cartes](schemas/carte.schema.json), les [synergies](schemas/synergie.schema.json) et les [médias](schemas/media.schema.json).

La scène de démonstration permet d’inspecter les cartes, de jouer Poudre de perlimpinpin, de révéler la synergie et de voir sa conséquence sur le plateau. Le signal sonore original est facultatif. Les règles complètes décrivent le futur moteur. Les cinq Refs ont une photographie locale. Les photos de cosplay illustrent les Refs dont les extraits restent à autoriser. Les légendes distinguent les photos d’illustration des scènes d’origine.

La [capture du plateau](plateau.png) et les exports PNG de Y.M.C.A., Bulma et The Mask incluent des photographies CC BY-SA 2.0. Ces composites sont distribués sous la même licence. Les crédits et les sources figurent dans le [registre média](catalogue/medias.json). [Licence CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/)

Les polices Barlow Condensed et Instrument Sans sont servies localement. Leurs licences sont dans [assets/fonts/](assets/fonts/).

Pour modifier les données, éditer les fiches individuelles, les synergies ou le registre média. Python 3 et `jsonschema` sont nécessaires pour contrôler les données et reconstruire le catalogue agrégé et l’instantané JavaScript.

```bash
python3 outils/valider.py --apercu
```
