#!/bin/sh
# Build the docs and push the generated site to the public repo luokelabs/luoke-atlas (GitHub Pages).
# Only the generated site/ goes public; sources stay in the private top-level repo.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
python3 "$HERE/build.py"
WORK=$(mktemp -d)
git clone -q https://github.com/luokelabs/luoke-atlas.git "$WORK"
cp "$HERE/site/index.html" "$HERE/site/.nojekyll" "$WORK/"
cd "$WORK"
if git diff --quiet && [ -z "$(git status --porcelain)" ]; then echo "no change"; exit 0; fi
git add -A
git -c user.name="Luoke Labs" -c user.email="zhixian@luoke.ai" commit -qm "Update docs"
git push -q origin main
echo "published: https://luokelabs.github.io/luoke-atlas/"
