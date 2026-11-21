# Fiches de Battle Ref Arena

Éditer les Personnages dans [`card_perso/`](card_perso/) et les Refs dans [`card_ref/`](card_ref/). Le nom du fichier reprend l’`id` de la carte en `snake_case`. [Le modèle JSON](template.json) donne la structure d’une Ref. Un Personnage utilise `kind: "character"`, possède `stats.hp` et indique le moment de sa capacité avec `timing`.

`origin.sources` contient les liens des œuvres, épisodes ou captations. `media` contient les identifiants du [registre des médias](medias.json) dans l’ordre de préférence. Pour chaque fichier local, le registre documente le chemin, la source, le crédit et la licence. `localCopies` associe une source à ses fichiers téléchargés. Les MP3, GIF et MP4 locaux portent une durée en millisecondes. Les fichiers se trouvent dans [`asset/`](../asset/), sous `image/catalogue`, `sound`, `gif` et `video`.

Une Ref a une amplification dans [le registre des synergies](synergies.json). La condition indique le Personnage allié qui la déclenche.

Pygame lit les fiches directement. Après une modification, la commande suivante valide les données et reconstruit le catalogue de l’aperçu. Python 3 et `jsonschema` sont requis.

```bash
python3 data/valider.py --apercu
```
