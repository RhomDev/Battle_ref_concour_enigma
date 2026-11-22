# Battle Ref Arena

## Télécharger l’APK Android 0.4.2

[Télécharger Battle Ref Arena 0.4.2 — téléphone Android ARM64 (.apk)](https://github.com/RhomDev/Battle_ref_concour_enigma/releases/download/android-v0.4.2/battle-ref-arena-arm64-v8a.apk)

[Télécharger Battle Ref Arena 0.4.2 — émulateur PC x86_64 (.apk)](https://github.com/RhomDev/Battle_ref_concour_enigma/releases/download/android-v0.4.2/battle-ref-arena-x86_64.apk)

Sur téléphone, ouvre l’APK ARM64 pour l’installer. Sur PC, glisse l’APK x86_64 dans la fenêtre de l’émulateur.

## Construire l’APK Android depuis le code

Installer Android SDK Platform 35, Build Tools 35.0.0, NDK r25b et python-for-android. Définir `ANDROID_HOME`, et `ANDROID_NDK_HOME` si le NDK est installé hors du SDK. Lancer `bash android/build.sh` pour créer `android/battle-ref-debug.apk` avec le catalogue du dépôt. Pour cibler uniquement un émulateur PC ou un téléphone ARM 64 bits, définir `ANDROID_ARCHS=x86_64` ou `ANDROID_ARCHS=arm64-v8a`. Pour installer l’APK par-dessus une version déjà installée, le signer avec la même clé via `ANDROID_DEBUG_KEYSTORE`.

Le catalogue contient **101 Refs et 43 Personnages** inspirés de mèmes d’animé, de jeu vidéo, de politique et de cinéma. Les fiches éditables et leur modèle se trouvent dans [`data/`](data/README.md). Les fichiers du jeu se trouvent dans [`asset/`](asset/).

- Ouvrir [le plateau guidé](apercu/index.html) dans un navigateur. Activer le son dans Options, piocher, déployer Macron puis jouer Y.M.C.A. pour déclencher sa projection.
- Pour consulter les médias avec Pygame, installer les dépendances avec `python3 -m pip install -r requirements.txt`, puis lancer `python3 main.py`. Les boutons **Personnages** et **Références** ouvrent les collections.
- Dans Pygame, **Jouer** propose une partie solo ou une partie sur le réseau local. Jouer une Réf lance son extrait dans l’arène lorsqu’il est disponible. **Piocher** coûte 1 énergie et **Passer** termine le tour.
