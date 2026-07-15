#!/usr/bin/env bash
set -euo pipefail

# Publish only the public static site. Source contracts, test fixtures and
# internal handoff reports remain in the repository but are never copied to
# the Pages output directory.
rm -rf dist
mkdir -p dist

for item in 404.html _headers _routes.json index.html llms.txt robots.txt sitemap.xml; do
  cp "$item" dist/
done

for directory in about assets faq privacy resources search solutions terms waitlist; do
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
