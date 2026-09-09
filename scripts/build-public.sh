#!/usr/bin/env bash
set -euo pipefail
# Run after each variant selects its final assets. Replace an existing query,
# never append a second query, and keep the original script order/defer flags.
version_public_assets() {
  local artifact="$1" asset digest
  case "$artifact" in dist|dist-public-beta|dist-public-beta-activation) ;; *) return 2 ;; esac
  for asset in site-config.js site.js styles.css tools-public-beta.js tools-public-beta.css; do
    test -f "$artifact/assets/$asset" || continue
    digest="$(shasum -a 256 "$artifact/assets/$asset" | awk '{print $1}')"
    ASSET_NAME="$asset" ASSET_DIGEST="$digest" find "$artifact" -name '*.html' -type f -exec \
      perl -0pi -e 's{((?:src|href)="/assets/\Q$ENV{ASSET_NAME}\E)(?:\?[^"\s]*)?"}{$1 . "?v=" . $ENV{ASSET_DIGEST} . "\""}ge' {} +
  done
}
if [[ "${1:-}" == "--version-assets" ]]; then
  version_public_assets "${2:?artifact directory required}"
  exit
fi

# Publish only the public static site. Source contracts, test fixtures and
# internal handoff reports remain in the repository but are never copied to
# the Pages output directory.
rm -rf dist
mkdir -p dist

for item in 404.html _headers _routes.json index.html llms.txt robots.txt sitemap.xml; do
  cp "$item" dist/
done

for directory in about assets faq healthz privacy refund resources search solutions support terms waitlist; do
  cp -R "$directory" dist/
done

# Keep the life-number calculator source for a future controlled release, but
# exclude it from every generated public artifact.
mkdir -p dist/tools
cp tools/index.html dist/tools/
for tool in sms-suite line-automation contact-converter smart-close; do
  cp -R "tools/$tool" dist/tools/
done

test -f dist/index.html
test -f dist/_headers
test ! -e dist/tests
test ! -e dist/release_contract.json
test ! -e dist/waitlist_contract.json
test ! -e dist/tools/life-number-calculator
test ! -e dist/tools/follow-up-rhythm
version_public_assets dist
