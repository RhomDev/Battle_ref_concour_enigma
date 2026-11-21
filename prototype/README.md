# Battle Ref Arena · dossier de première mission

Ouvrir `apercu.html` dans un navigateur. Le dossier fonctionne localement sans compilation ni connexion. Cliquer sur « Jouer la Ref » dans l’inspecteur pour déclencher la scène. L’onglet Catalogue permet d’afficher les 15 fiches dans leur cadre graphique.

- [Aperçu du plateau](apercu.html) et [capture PNG du plateau](plateau.png).
- [Directions visuelles](directions.html) et [planche PNG](directions.png).
- Cartes exportées en PNG dans `exemples/` · [Donald Trump](exemples/personnage-trump.png), [Emmanuel Macron](exemples/personnage-macron.png), [PSY](exemples/personnage-psy.png) et [Poudre de perlimpinpin](exemples/ref-perlimpinpin.png). Les crédits des photos figurent dans le registre média.
- [Recherche culturelle et état des médias](docs/recherche.md).
- [Audit, règles, dix synergies, architecture, pipeline et roadmap](docs/conception.md).
- [Prompts des cadres](docs/prompts-cadres.md), maîtres PNG et dérivés WebP dans `assets/frames/`.
- [Cartes](catalogue/cartes.json), fiches JSON individuelles dans `catalogue/fiches/`, [synergies](catalogue/synergies.json), [médias et crédits](catalogue/medias.json).
- Schémas JSON pour les [cartes](schemas/carte.schema.json), les [synergies](schemas/synergie.schema.json) et les [médias](schemas/media.schema.json).

La scène de démonstration permet d’inspecter les cartes, de jouer Poudre de perlimpinpin, de révéler la synergie et de voir sa conséquence sur le plateau. Le signal sonore original est facultatif. Les règles complètes décrivent le futur moteur. Trois photographies sont empaquetées, les extraits d’œuvres sont référencés pour revue.

Pour modifier les données, éditer les fiches individuelles, les synergies ou le registre média. Python 3 et `jsonschema` sont nécessaires pour contrôler les données et reconstruire le catalogue agrégé et l’instantané JavaScript.

```bash
python3 outils/valider.py --apercu
```
