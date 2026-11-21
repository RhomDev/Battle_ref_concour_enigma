# Battle Ref Arena

Battle Ref Arena est un jeu de cartes tactique pour deux joueurs en local. Le thème « T’as la ref ? » réunit des personnages et des scènes de cinéma, d’animé, de musique et de culture Internet. Un Personnage occupe un emplacement et possède des PV et une attaque. Une Ref dépense de l’énergie, applique un effet et peut révéler une synergie.

## Pile technique et état du projet

- Développer le jeu et ses outils en **Python 3**, avec **Pygame** pour la fenêtre, le rendu, les entrées et l’audio.
- `apercu/index.html` est une démonstration visuelle locale qui montre une scène guidée. Les collections de Pygame lisent les fiches de `data/`.
- `data/template.json` illustre la structure des fiches sous `data/`. Le duel Pygame reste à construire.
- Le plan de jeu, les règles de résolution et les synergies sont décrits dans [le document de conception](prototype/docs/conception.md).

## Données et visuels de référence

- Les fiches sources sont dans `data/card_perso/` et `data/card_ref/`. Les synergies et les crédits média sont dans `data/synergies.json` et `data/medias.json`.
- Les schémas JSON sont dans `data/schemas/`. Conserver des identifiants stables en `snake_case` et des chemins de médias relatifs à la racine.
- La direction retenue utilise le fond bordeaux de la table de projection dans `asset/board/plateau.webp`. Les cadres dans `asset/frames/` sont bordeaux pour les Personnages et vert profond avec une bordure dorée pour les Refs.
- Composer les cartes à partir des données. Placer la photo recadrée dans la fenêtre transparente puis superposer le cadre, le nom, le coût, le texte d’effet et les statistiques. Les PNG maîtres et leurs dérivés WebP servent de base au rendu Pygame.
- Ranger les médias locaux dans `asset/`. Garder leur auteur, leur source et leur licence dans le registre. `localCopies` indique les fichiers téléchargés depuis les sources d’origine.

## Organisation du portage

- Isoler le moteur de combat dans des modules Python indépendants de Pygame. Il valide les commandes, applique les effets et produit les événements que le rendu et le son consomment.
- Charger cartes et effets depuis le catalogue JSON. Utiliser les identifiants d’instance pour les cibles d’une partie, et les identifiants du catalogue pour les définitions des cartes.
- Résoudre les cibles, ripostes, éliminations et synergies dans un ordre déterministe. Garder la graine du mélange pour reproduire une partie.
- Prioriser un duel local complet avec invocation, attaque, Ref, fin de tour et résultat. Vérifier ensuite l’inspection des cartes, les animations et la lisibilité sur petit écran.
- Vérifier le catalogue avec `python3 data/valider.py` (dépendance `jsonschema`). Après modification des fiches, lancer la commande avec `--apercu` pour régénérer les données de l’aperçu. Tester séparément les cas limites du moteur au fil du portage.
