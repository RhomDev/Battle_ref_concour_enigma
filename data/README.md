# Fiches de Battle Ref Arena

Éditer les Personnages dans [`card_perso/`](card_perso/) et les Refs dans [`card_ref/`](card_ref/). Le nom du fichier reprend l’`id` de la carte en `snake_case`. [Le modèle JSON](template.json) donne la structure d’une Ref. Un Personnage utilise `kind: "character"` et possède `stats.hp`.

`origin.sources` contient les liens des œuvres, épisodes ou captations. `media` contient les identifiants du [registre des médias](medias.json) dans l’ordre de préférence. Pour chaque fichier local, le registre documente le chemin, la source, le crédit et la licence. `localCopies` associe une source à ses fichiers téléchargés. Les MP3, GIF et MP4 locaux portent une durée en millisecondes. Les fichiers se trouvent dans [`asset/`](../asset/), sous `image/catalogue`, `sound`, `gif` et `video`.

L’aperçu dans Pygame lit le GIF et le MP3 ensemble. Quand une Réf possède un MP4 local, ajouter aussi le GIF correspondant. La légende du visuel précise quand le photogramme provient de la bande-annonce.

Chaque Ref définit un seul `abilities.effect` avec un type (`attack`, `heal` ou `shield`) et un montant de base (`amount`). L’attaque vise un Personnage adverse tant que l’adversaire en a sur le terrain. Si son terrain est vide, l’attaque peut viser directement ses PV. Le soin et le bouclier visent un Personnage allié.

Le champ `synergy` contient `character_id` et `bonus`, ou vaut `null`. Lorsque ce Personnage est sur le terrain du joueur qui joue la Ref, le bonus s’ajoute au montant du même effet.

Pygame lit les fiches directement. Après une modification, la commande suivante valide les données et reconstruit le catalogue de l’aperçu. Python 3 et `jsonschema` sont requis.

```bash
python3 data/valider.py --apercu
```
