#!/usr/bin/env bash
set -euo pipefail

project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project"

sdk=${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}
build_tools="$sdk/build-tools/35.0.0"
android_jar="$sdk/platforms/android-35/android.jar"
python=${PYTHON:-python3}
debug_key="$project/android/.debug.keystore"
apk="$project/android/battle-ref-menu.apk"

if [[ ! -x "$build_tools/aapt2" || ! -f "$android_jar" ]]; then
    echo 'Installez les packages Android build-tools;35.0.0 et platforms;android-35, puis définissez ANDROID_HOME.' >&2
    exit 1
fi

work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/assets" "$work/classes"

"$python" -B -m android.render_menu "$work/assets/menu.png"
javac --release 8 -classpath "$android_jar" -d "$work/classes" android/MenuActivity.java
"$build_tools/d8" --min-api 24 --lib "$android_jar" --output "$work" \
    "$work/classes/fr/battleref/menutest/MenuActivity.class"
"$build_tools/aapt2" link -I "$android_jar" --manifest android/AndroidManifest.xml \
    -A "$work/assets" -o "$work/unsigned.apk"
(cd "$work" && zip -q unsigned.apk classes.dex)
"$build_tools/zipalign" -f 4 "$work/unsigned.apk" "$work/aligned.apk"

if [[ ! -f "$debug_key" ]]; then
    keytool -genkeypair -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 \
        -dname 'CN=Android Debug,O=Android,C=US' -keystore "$debug_key" \
        -storepass android -keypass android
fi
"$build_tools/apksigner" sign --ks "$debug_key" --ks-pass pass:android \
    --out "$work/battle-ref-menu.apk" "$work/aligned.apk"
"$build_tools/apksigner" verify "$work/battle-ref-menu.apk"
mv -f -- "$work/battle-ref-menu.apk" "$apk"
printf 'APK créé : %s\n' "$apk"
