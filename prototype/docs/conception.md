# Battle Ref Arena · Audit et conception

## Audit de main

Dépôt [RhomDev/Battle_ref_concour_enigma](https://github.com/RhomDev/Battle_ref_concour_enigma), branche `main`, commit local et distant `bc1010c208b8986a7773712b7d630793f05effbd` vérifiés avec Git. Une branche distante a été listée. Le dossier de livraison est externe au dépôt.

| Fichier ou dossier | Observation et conséquence |
|---|---|
| `README.md` | Titre seul. Les règles, la méthode de lancement et les crédits média restent à documenter. |
| `data/fiche_perso/the_mask.json` | JSON lisible. `name`, `image`, `attack.standard/fort/ultime` pointent tous vers `the_mask_ref_1`. `celebrate`, `rarity`, `strength` valent 0. `weakness` et `combination` renvoient à `the_mask`. L’ID dépend du fichier. PV, attaque chiffrée et coût d’invocation à introduire. |
| `data/fiche_ref/the_mask_ref_1.json` | JSON lisible. `name_pers: "the_mask"`, `name: "Sssplendide"`, image renseignée, GIF et son vides. `cost`, `damage`, `cooldown`, `effect`, `value_effect` valent 0. Les valeurs sont des marqueurs de prototype. |
| `data/Kard.py` | `read_json(path)` ouvre toujours `data.json`, absent. Les constructeurs appellent `open(json_name)` avant le chargeur. Les deux chemins d’image commencent à la racine du système dans Python. GIF et son sont chargés comme des images, même avec une chaîne vide. `convert_alpha()` suppose un mode d’affichage initialisé. |
| `data/Read_Data.py` | Deux imports `json` et aucun chargement. |
| `src/image/` | Captures 1280 × 720 RGBA, alpha entièrement opaque. Les deux PNG ont le même SHA-256 `38111582369717d973207f3c4034f22d7492c169e2431ee09e743a6e4e8317dd`. Ils montrent la même scène de The Mask. La provenance et les conditions d’intégration restent à renseigner. |
| `src/gif/`, `src/sound/` | Fichiers marqueurs vides. |
| `.idea/` | Métadonnées de l’IDE. Aucun point d’entrée de match, test, gestion de dépendances ou build dans les fichiers suivis. Pygame manque dans l’environnement courant. |

Migration proposée dans une future branche. Déplacer les fiches d’origine et les scripts vers `legacy/python/` au premier commit de réorganisation. Conserver `the_mask` et fixer un alias d’import `the_mask_ref_1 → sss_plendide`. Les trois pointeurs d’attaque historiques laissent place aux règles d’attaque globales. Les valeurs factices sont converties à la main à partir des nouvelles fiches, avec revue de l’équipe. Les PNG historiques sont conservés dans Git comme preuves de travail et traités comme médias de recherche dans le registre jusqu’à validation des droits.

## Direction graphique retenue

La **table de projection** assemble un tapis de jeu bordeaux, des bobines en périphérie et deux cadres inspirés du cinéma imprimé. Le fond illustré laisse libres les deux rangées du duel. Les jauges de PV longent le tapis et la main reste sur une zone papier séparée. Les directions alternatives restent consultables dans la [planche graphique](../directions.html).

Les deux cadres PNG de 1 024 × 1 536 px ont été générés avec une fenêtre réellement transparente. Les WebP alpha de 660 × 990 px servent au jeu. L’interface place la photo derrière le cadre puis ajoute le texte et les statistiques devant. Les pourcentages de la fenêtre et du médaillon vivent dans la feuille de style.

- **Personnage.** Bordeaux et angles biseautés. Le coût apparaît dans le médaillon. Le bandeau inférieur accueille univers, effet, attaque, PV et Bouclier. En combat, la fiche agrandie donne le détail de la règle.
- **Ref.** Vert profond et or, avec perforations latérales et encoches de ticket. Les cinq cartes ont une photographie locale. Sur la fiche, le bas présente la règle et la catégorie. Les médias de substitution sont identifiés sous la carte et dans les crédits.
- **Rareté.** Différée au-delà du premier playtest.
- **Échelles.** Maîtres PNG avec alpha, cadres WebP à moins de 80 Ko chacun, cartes du plateau autour de 116 px de large sur ordinateur. Les exemples autonomes mesurent 600 × 900 px. Le fond généré est stocké en WebP à 1 560 × 780 px.

## Règles proposées

### Mise en place et rythme

- La partie oppose deux joueurs à **18 PV**, chacun avec un paquet de 15 cartes identique, une occurrence par ID, mélangé avec une graine enregistrée. Main de 4 cartes et un remplacement initial facultatif des cartes choisies. Les cartes remplacées retournent dans le paquet après le repêchage, puis le paquet est remélangé. Joueur initial tiré par cette même graine.
- Chaque joueur joue son tour en entier. Il a **trois emplacements** Personnage et une main de **sept cartes** maximum. Il récupère toute son énergie au début de son tour, avec un maximum égal au numéro de son propre tour, plafonné à **6**. Le premier joueur saute sa toute première pioche. Chaque autre début de tour pioche une carte.
- Au début de son tour, le joueur rend ses unités prêtes. Une unité invoquée rejoint le plateau épuisée et peut riposter. Une unité prête peut accomplir **une action** par tour, parmi une attaque ou sa capacité active. La capacité active peut demander de l’énergie. Les invocations et les Refs dépensent de l’énergie sans consommer l’action d’une unité.
- Une attaque vise un Personnage adverse, ou le joueur adverse s’il n’a aucun Personnage avec **Garde**. En présence d’une ou plusieurs Gardes adverses, toutes les attaques doivent en cibler une. Les Refs et capacités ciblent selon leur propre règle. Une unité ciblée riposte avec son ATQ actuelle, même épuisée. Un joueur ciblé ne riposte pas.

| Action | Coût et dégâts | Charge |
|---|---|---|
| Normale | 0 ⚡ · ATQ courante | L’attaquant gagne 1 Charge s’il survit à la résolution de l’échange. |
| Forte | 1 ⚡ · ATQ +2 | Aucune Charge gagnée. |
| Ultime | 2 ⚡ et 2 Charges · ATQ +3, cible Personnage uniquement | Les Charges sont dépensées à l’annonce. |

### États et résolution

- Bouclier absorbe autant de dégâts que de points disponibles, jusqu’à 3. Les soins plafonnent aux PV imprimés. Charge plafonne à 2 par unité. Les bonus d’ATQ des cartes du premier lot durent jusqu’à la fin du tour actif. Garde dure jusqu’à dissipation ou K.-O.
- `dispel` retire Boucliers, Garde et bonus positifs d’ATQ. La Charge est une ressource et ne se dissipe pas. `defeated` est émis pour une unité retirée du plateau. `draw` pioche même avec une main pleine. Dans ce cas, la carte piochée va à la défausse. Chaque tentative sur paquet vide inflige au joueur 1, puis 2, puis 3 dégâts de fatigue, etc.
- Valider puis payer la commande. Les cibles publiques sont décidées à la validation, y compris le choix de renoncer à une cible facultative. Appliquer les effets dans leur ordre déclaré. Un effet sur plusieurs unités prend une photographie de l’ensemble des cibles. Pour une attaque, appliquer dégâts et riposte dans un même lot. Pour chaque lot, calculer les Boucliers, appliquer les PV et retirer tous les K.-O. simultanément.
- Dépiler les effets de K.-O. une vague à la fois, joueur actif puis autre joueur, chacun dans l’ordre des emplacements. Les capacités de base priment sur les synergies cachées. Les matches de synergie utilisent le plateau à la fin des effets de base, puis sont traités par ID dans un ordre stable. Une cible disparue ou absente fait échouer l’effet qui la vise. Une synergie s’inscrit au journal si au moins un effet change l’état. Les bonus découverts sont limités à un déclenchement par joueur et par match. Les événements de synergie ne cherchent pas de nouvelle synergie. Les K.-O. consécutifs suivent la file normale.
- La victoire se vérifie à la fin de la résolution de la commande et de sa file. Un seul joueur à zéro PV perd, les deux à zéro donnent un match nul. Si le douzième tour de chaque joueur est terminé et que les deux survivent, comparer les PV du joueur, puis attribuer un nul en cas d’égalité. L’interface affiche l’état final après la file d’effets.

### Les dix interactions cachées

Chaque révélation apparaît en bandeau, entre dans un journal consultable, et nomme la carte ainsi que ses cibles. Les effets visibles qui la précèdent utilisent les icônes du plateau.

| ID et titre | Déclencheur et effet | Ressort et mise en scène |
|---|---|---|
| s1 · Le smoking prend feu | Sssplendide ! cible votre Mask. Il gagne 1 Charge après le soin. | La mise en scène alimente le Mask. Flash cyan et carton de la réplique. |
| s2 · Poudre aux yeux | Vous jouez Poudre de perlimpinpin avec Macron sur votre plateau. Piochez 1. | Il relance le débat avec sa propre formule. Tampon « Débat 2017 ». |
| s3 · Dernier rappel | Y.M.C.A. avec votre Trump en jeu. Il gagne 1 Charge, en plus de son Bouclier passif de Danse. | Le morceau de sortie lui rend de l’élan. Projecteur cuivre. |
| s4 · Sex Pistols sur la piste | Canzoni preferite cible votre Mista. Piochez 1. | Il retrouve sa chorégraphie. Trois projecteurs et titre de la piste. |
| s5 · Fierté saiyenne | Touche pas à ma Bulma ! cible votre Vegeta. Il gagne 1 Charge. | La réplique provoque sa montée de puissance. Jauge et flash ambre. |
| s6 · Battle de chorés | Y.M.C.A. avec PSY sur votre plateau. PSY reçoit 1 Bouclier. | Le pas de cheval répond aux poings du meeting. Faisceaux croisés. |
| s7 · C’est pas faux, c’est long | Vous invoquez Otis alors que Perceval est déjà chez vous. Otis gagne 1 Bouclier. | Perceval accompagne la digression d’un acquiescement. Sous-titre « C’est pas faux. » |
| s8 · Le lien surprise | Vous invoquez Rick Astley face à Mista. Rick gagne 1 Bouclier. | La playlist de Mista bascule. Lecteur qui change de canal. |
| s9 · Psssh… sans le son | Vous jouez Poudre de perlimpinpin sur le Creeper adverse. Il subit 1 dégât après la dissipation. | Le grand effet d’annonce finit en grésillement. Parasites puis bulle « Psssh. » |
| s10 · Duel de grimaces | Votre Mask attaque Vegeta et survit. Le Mask gagne 1 Bouclier. La cible est l’identité enregistrée à l’annonce. | Le visage déformé contraste avec son adversaire. Carton à double cadre. |

**Trois plans de jeu.** Danse prépare un tour d’attaque en largeur avec PSY, Trump et Y.M.C.A. Garde met Vegeta sous protection et crée une menace d’ultime. Contrôle par Macron, Poudre et Creeper ouvre les cibles et casse les bonus. Otis protège, Perceval et Rick renouvellent la main, The Mask sert de menace intermédiaire et Mista finit les blessés. L’équilibrage reste une hypothèse. Mesurer taux de victoire en premier, longueur de partie, avantage de tempo à 1/2/3 énergies, synergies visibles par partie et unités qui gardent trop longtemps.

## Web ou Python

| Critère | Web statique avec TypeScript | Python avec Pygame |
|---|---|---|
| Départ | Interface racontable au jury avec HTML/CSS et fichiers de données. Un prototype d’écran est livré. | Les classes actuelles fournissent quelques exemples de champs et de blit. Il faut créer la boucle de jeu et réparer le chargement. |
| Cartes | Composants de données, CSS, clavier et mise à l’échelle native. | Chaque mise en page, texte, mise à l’échelle et interaction demande du code de dessin et d’événement. |
| GIF + son | Image animée ou vidéo, lecture événementielle, gestion du son et mode mouvement réduit via navigateur. | Décodage ou préparation des trames GIF, lecture via mixer, réglages et lifecycle à gérer. |
| Combat | Fonction TS pure, tests Node et navigateur. Même moteur pour le duel local et un bot éventuel. | Python convient pour un moteur pur et des simulations. Partager la logique de combat avec un frontend Web demande une interface supplémentaire. |
| Jury | Ouvrir une version statique hors ligne ou via hébergement dès autorisation. | Préparer un environnement ou un exécutable par plateforme et tester le plein écran. |

**Choix.** Web TypeScript, build statique, UI HTML/CSS. Le duel local se joue sur une machine. Les outils d’import et de recherche peuvent rester en Python. Commencer avec le DOM et un composant de carte partagé. Ajouter une bibliothèque UI selon les habitudes de l’équipe quand l’état de l’interface se complexifie.

```text
data/
  cards/{characters,refs}/   # Une fiche par ID
  synergies/                # Conditions, effets, texte de révélation
  decks/                    # Listes d'IDs et variante de règles
  media/                    # Inventaire, droits, provenance, points focaux
schemas/                    # JSON Schema 2020-12
src/
  engine/                   # state, commands, rules, effects, events, shuffle
  ui/                       # Board, Card, Inspector, EventLog
  media/                    # Politique de chargement, player, AudioBus
public/
  media/{images,clips,sfx}/
  templates/                # PNG maîtres en archive, WebP runtime
tools/{research,import,validate,preview}/
tests/{engine,catalogue,ui}/
docs/
legacy/python/
```

Conventions. ID et fichiers de données en `snake_case` ASCII, labels français avec ponctuation, chemins relatifs POSIX, noms de propriétés en `camelCase`. Les fiches individuelles constituent la source maître lors de l’intégration. Le snapshot agrégé est généré au build. Les JSON de la livraison exposent déjà ces deux représentations. `schemaVersion` permet de versionner les entrées. Garder trois schémas indépendants pour carte, synergie et média. Valider aussi les références croisées, le typage des cibles et la compatibilité des opérations avec les événements. Une session identifie chaque unité par un ID d’instance. Les IDs catalogue servent à construire les matchs, les cibles et les journaux.

Moteur recommandé. `applyCommand(state, command) → {state, events}`. Commandes `Summon`, `CastRef`, `Attack`, `Activate`, `EndTurn`. Un registre d’opérations implémente une fois par famille `damage`, `heal`, `shield`, `draw`, `dispel`, `boost_attack`, `charge` et `guard`. Les faits du combat sont portés par les événements. L’UI observe les événements pour l’animation, les crédits et le journal de découverte.

## Intégration automatique des médias

1. Dans une fiche, inscrire les IDs des médias candidats, par format. Dans le registre, conserver URL de source, auteur, titulaire ou interlocuteur, licence et autres restrictions. Une URL d’origine autorise le repérage et la vérification.
2. Après confirmation de l’usage précis, l’importeur télécharge en préparation depuis une URL autorisée, contrôle type et dimensions, calcule SHA-256 et crée un dérivé d’affichage. Ajouter URL du fichier, date de récupération, fichier de preuve, contexte d’usage, état d’autorisation et point focal `x,y` au registre de production. Réserver les extraits avec un minutage précis par version et doublage.
3. Le build publie seulement les fichiers marqués admissibles à l’usage visé et leurs crédits. Les médias d’identification dont l’usage reste à vérifier restent dans le catalogue de recherche. Si une photo de remplacement est utilisée, documenter la différence avec la scène originale.
4. Le composant carte pose par couches le fond, la photo recadrée `object-fit: cover`, le PNG/WebP alpha du type de carte, les icônes d’état, les champs texte/statistiques du JSON et enfin l’animation transitoire. En cas de fichier absent, remplacer son rectangle par un motif de la famille de carte. Les données de combat n’attendent jamais le téléchargement d’une image.
5. Afficher un poster statique. Après `RefResolved` ou `SynergyDiscovered`, ouvrir un seul lecteur au premier plan pour 1 à 2 secondes. Privilégier MP4/WebM muet pour une scène compressée, utiliser GIF ou WebP animé quand c’est le seul format admissible, monter l’élément animé uniquement pendant la séquence, puis le retirer. Avec mouvement réduit, afficher poster et libellé. Objectif pour un clip de référence < 700 Ko en format vidéo à 480p. Mettre les fichiers locaux à nom haché en cache et précharger seulement ceux de la main ou du jeu de démo.
6. Relier `CharacterSummoned`, `AttackResolved`, `UltimateResolved`, `RefResolved`, `SynergyDiscovered` et `MatchEnded` à des cues dédiés. Initialiser l’audio au clic « Activer le son ». Appliquer volume et mute dans un bus commun, interrompre un effet obsolète et tolérer un refus de lecture. La maquette contient un signal sonore original synthétisé pour une découverte, avec volume et activation. [Règles d’autoplay MDN](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay)

## Pipeline éditorial assisté par IA

1. Sujet et public → requêtes documentées, puis deux sources compatibles quand l’origine est ambiguë.
2. Vérification humaine de l’œuvre, du créateur, de la date, du contexte, du minutage et de la version. Capturer un extrait de preuve textuelle limité.
3. Recherche média puis revue des droits, par fichier et par contexte. Identifiant du média et alternative originale enregistrés même si l’extrait est en attente.
4. Proposer deux effets avec écart de puissance attendu. Les candidats comiques sont relus pour garder une justification compréhensible.
5. Chercher des synergies avec les cartes existantes. Formaliser déclencheurs, bornes, cible et révélation dans un schéma fermé.
6. Générer la fiche, la valider et contrôler les liens croisés. Sélection du cadre par type. Prendre une prévisualisation du plateau et de l’inspection.
7. Simuler avec graine, jouer plusieurs tours à la main et vérifier les cas de défausse, disparition de cible, simultanéité et absence de média.
8. Un membre de l’équipe approuve origine, droits, règles et rendu. Les propositions et les preuves suivent la carte dans la revue. Le contenu ne rejoint le paquet de démo qu’après validation.

## Roadmap de production

| Lot | Livrable | Critère de sortie |
|---|---|---|
| 1 · Contrat | Schémas, migration Mask, catalogue | Échec explicite sur type, ID, média local et synergie incohérents. |
| 2 · Combat minimal | Duel local à unités simples, main, actions, tours et résultat | Rejouer la même graine et vérifier énergie, Garde, riposte, sortie simultanée et match nul. |
| 3 · Rendu et chargement | Cadres, inspecteur, adaptation petit écran, cartes chargées depuis les JSON | Les deux types se lisent à 120 px. Démarrage offline, parcours clavier et erreur média testés. |
| 4 · Médias | Signal au lancement, son et animation par événement | Audio volontaire, prise en charge du mute, fallback poster, une seule animation lourde. |
| 5 · Paquet | 10 Personnages, 5 Refs, 10 synergies | Vérifier chaque déclencheur et contre-exemple. Les deux joueurs peuvent gagner avec plusieurs plans. |
| 6 · Démonstration | Match guidé, départ rapide, replay local | 3 parties chronométrées complètes. Une variante prévisible garantit une occasion de découverte pendant le passage jury. |

Première livraison vérifiable. L’aperçu joue une scène guidée et illustre la composition des cartes, le coût d’une Ref, la dissipation, la découverte et la pioche. Les autres règles constituent le cahier de conception du moteur. Les statistiques et le paquet seront calibrés avec les parties de test.
