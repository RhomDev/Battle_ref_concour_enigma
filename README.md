# Battle Ref Arena

Battle Ref Arena est un jeu de cartes avec 57 Refs et 20 Personnages inspirés de mèmes. Les fiches et leur modèle sont dans [data](data/README.md).

## Jouer sur PC

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

**Jouer** ouvre le choix des modes. **Solo** lance une bataille hors ligne contre le bot. **Personnages** et **Références** ouvrent les collections depuis l’accueil.

## Jouer sur Android

Installer [l’APK de test](android/battle-ref-debug.apk) sur un appareil Android 7.0 ou supérieur équipé d’un processeur ARM 64 bits. L’APK inclut aussi la version x86-64 pour émulateur.

Pour le reconstruire, installer le JDK 17, Gradle 8.11.1, Python 3.12 et Android SDK Platform 35, puis lancer `bash android/build.sh`. Si nécessaire, définir `ANDROID_HOME` vers le SDK et `GRADLE` vers l’exécutable Gradle. Le script écrit `android/battle-ref-debug.apk`.

## Jouer à deux sur le même réseau

1. Connecter le téléphone ou le PC de chaque joueur au même Wi-Fi. Un PC relié en Ethernet au même réseau fonctionne aussi.
2. Sur un appareil, ouvrir **Jouer → Créer une partie** et communiquer l’adresse affichée.
3. Sur l’autre appareil, ouvrir **Jouer → Rejoindre une partie**, saisir cette adresse et sélectionner **Se connecter**.

Les deux appareils doivent utiliser la même version du jeu et des fiches. Si l’hôte est un PC avec pare-feu, autoriser le jeu sur le réseau local pour le port TCP 51427.

## Pendant la partie

Sélectionner une carte de la main pour afficher ses cibles possibles, puis sélectionner un emplacement en surbrillance ou la plaque adverse si son terrain est vide. Les personnages occupent un des trois emplacements alliés. Les Refs peuvent attaquer, soigner ou ajouter un bouclier. Chaque joueur commence à 15 PV et perd à 0 PV. Au début de son tour, son énergie revient à 5. **Piocher** coûte 1 énergie et **Passer** est possible à tout moment pendant son tour.

Le [plateau guidé](apercu/index.html) permet de revoir la démonstration de Macron et Y.M.C.A. dans un navigateur.

## Vérifier les règles et le réseau

```bash
python3 -m unittest discover -s tests -v
```
