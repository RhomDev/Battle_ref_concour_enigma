#!/usr/bin/env bash
set -euo pipefail

project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project"
sdk=${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$project/.android-sdk}}
ndk=${ANDROID_NDK_HOME:-$sdk/ndk/25.1.8937393}
p4a=${P4A:-p4a}
storage=${P4A_STORAGE_DIR:-$project/android/build/p4a}
dist=${P4A_DIST_NAME:-battleref}
debug_key=${ANDROID_DEBUG_KEYSTORE:-$project/android/.debug.keystore}
if [[ ! -d "$sdk/platforms/android-35" || ! -d "$ndk/toolchains/llvm" ]]; then
    printf '%s\n' 'Installez Android SDK Platform 35 et NDK r25b, puis définissez ANDROID_HOME et ANDROID_NDK_HOME.' >&2
    exit 1
fi

mkdir -p "$project/android/build"
stage=$(mktemp -d "$project/android/build/stage.XXXXXXXX")
trap 'rm -rf -- "$stage"' EXIT
app="$stage/app"
mkdir -p "$app/asset/image" "$app/data" "$app/scenes"
cp main.py config.py "$app/"
cp -R core gameplay ui "$app/"
cp scenes/*.py "$app/scenes/"
cp -R data/card_perso data/card_ref data/medias.json "$app/data/"
cp -R asset/board asset/fonts asset/frames asset/gif asset/sound asset/video "$app/asset/"
cp -R asset/image/catalogue "$app/asset/image/"

export VERSION_pygame=2.6.1
read -r -a architectures <<< "${ANDROID_ARCHS:-arm64-v8a x86_64}"
arch_args=()
for arch in "${architectures[@]}"; do
    arch_args+=("--arch=$arch")
done

(
    cd "$stage"
    "$p4a" apk --bootstrap=sdl2 --requirements=python3,pygame,pillow \
        "${arch_args[@]}" --android-api=35 --ndk-api=24 --sdk-dir="$sdk" --ndk-dir="$ndk" \
        --storage-dir="$storage" --dist-name="$dist" --private="$app" \
        --name='Battle Ref Arena' --package=fr.battleref.arena --version=0.4.2 --numeric-version=9 \
        --orientation=portrait --permission=INTERNET --permission=ACCESS_NETWORK_STATE \
        --permission=ACCESS_WIFI_STATE --permission=CHANGE_WIFI_MULTICAST_STATE
)
apks=("$stage"/*.apk)
apk="$project/android/battle-ref-debug.apk"
signed="$stage/battle-ref-signed.apk"
signer="$sdk/build-tools/35.0.0/apksigner"
if [[ -f "$debug_key" ]]; then
    "$signer" sign --ks "$debug_key" --ks-pass pass:android --out "$signed" "${apks[0]}"
else
    cp "${apks[0]}" "$signed"
fi
"$signer" verify "$signed"
mv -f -- "$signed" "$apk"
printf 'APK créé : %s\n' "$apk"
