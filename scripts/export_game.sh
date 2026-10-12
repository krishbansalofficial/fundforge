#!/bin/sh
# Export the Godot client for Linux and Windows and prove the Linux build boots.
#   scripts/export_game.sh GODOT_BINARY TEMPLATES.tpz [OUT_DIR]
# TEMPLATES.tpz must be the official Godot_v4.7.2-stable_export_templates.tpz; its SHA-512 is checked
# against the release's published sum before anything is extracted. Only the two release templates
# these presets need are installed. Output: OUT_DIR/linux/FundForge.x86_64 and
# OUT_DIR/windows/FundForge.exe, each self-contained (the presets embed the .pck). These are test builds for CI artifacts, not
# signed releases; nothing here publishes anything.
set -eu
godot=$1
tpz=$2
out=${3:-export}
version=4.7.2.stable
sha512=ca4d71c4d7b81dfc15d1a98baa07534aa95b03fdda78a0075b06672e1648d2e5f40980c9adc28d23e1b92e732ee7bf3461997aa804af74ec2fcd7a93ccb84079
root=$(cd "$(dirname "$0")/.." && pwd)
case $out in /*) ;; *) out=$(pwd)/$out ;; esac

echo "$sha512  $tpz" | sha512sum -c -
dest=${XDG_DATA_HOME:-$HOME/.local/share}/godot/export_templates/$version
mkdir -p "$dest"
unzip -o -j -q "$tpz" templates/linux_release.x86_64 templates/windows_release_x86_64.exe templates/version.txt -d "$dest"
[ "$(cat "$dest/version.txt")" = "$version" ] || { echo "templates are not $version" >&2; exit 1; }

cd "$root/game"
"$godot" --headless --path . --import >/dev/null 2>&1 || true  # first import may report missing cache; exports check below
mkdir -p "$out/linux" "$out/windows"
"$godot" --headless --path . --export-release "Linux" "$out/linux/FundForge.x86_64"
"$godot" --headless --path . --export-release "Windows Desktop" "$out/windows/FundForge.exe"
for f in "$out/linux/FundForge.x86_64" "$out/windows/FundForge.exe"; do  # the presets embed the .pck
    [ -s "$f" ] || { echo "missing export output $f" >&2; exit 1; }
done

# The exported Linux build itself must boot cleanly to its menu (no server needed for the menu).
log=$(mktemp)
"$out/linux/FundForge.x86_64" --headless --quit-after 300 >"$log" 2>&1
if grep -qiE "SCRIPT ERROR|^ERROR|Parse Error|Failed to load" "$log"; then
    cat "$log" >&2
    echo "exported build reported errors" >&2
    exit 1
fi
rm -f "$log"
ls -la "$out/linux" "$out/windows"
echo "export ok"
