#!/usr/bin/env bash
# TRACK D — stand up a private ComfyUI from the SHIPPED tarball on ports 319xx.
# Ports are Track D's alone: 18188 (A) and 28191 (B) are never touched.
set -uo pipefail
export WS5_WORK=/workspace/d-gate-verify
export WS5_TARGET=/workspace/comfy-d-gate
export WS5_MIRROR_PORT=31921
export WS5_DEAD_PORT=31939
REPO=/workspace/nsfw-fix
EXPECT=06ad99f2f733ea3f6a9eb8c0e8594da12821f3c496f91354508d2c88134affb9

echo "=== artifact verification (before anything is unpacked) ==="
GOT=$(sha256sum "$REPO/dist/AIOFMTech-NSFW.tar.gz" | cut -d' ' -f1)
echo "  expected sha256 : $EXPECT"
echo "  actual   sha256 : $GOT"
[[ "$GOT" == "$EXPECT" ]] || { echo "  ✗ ARTIFACT HASH MISMATCH — refusing to continue"; exit 2; }
echo "  bytes           : $(stat -c%s "$REPO/dist/AIOFMTech-NSFW.tar.gz")"
echo "  files (non-dir) : $(tar -tzf "$REPO/dist/AIOFMTech-NSFW.tar.gz" | grep -vc '/$')"
echo "  top-level       : $(tar -tzf "$REPO/dist/AIOFMTech-NSFW.tar.gz" | head -1)"

echo "=== target must not exist beforehand ==="
if [[ -e "$WS5_TARGET" ]]; then echo "  ✗ $WS5_TARGET already exists — refusing (empty-dir requirement)"; exit 2; fi
echo "  $WS5_TARGET does not exist: OK"

for P in "$WS5_MIRROR_PORT" "$WS5_DEAD_PORT"; do
  if curl -fsS --max-time 2 "http://127.0.0.1:$P/" >/dev/null 2>&1; then
    echo "  ✗ something answers on $P — FAIL LOUD, not falling through"; exit 2
  fi
done
echo "  ports $WS5_MIRROR_PORT / $WS5_DEAD_PORT are dead: OK"

bash "$REPO/tools/verify_buyer_path.sh" gist    || exit 1
bash "$REPO/tools/verify_buyer_path.sh" prepare || exit 1
bash "$REPO/tools/verify_buyer_path.sh" happy   || exit 1
echo "=== done ==="
