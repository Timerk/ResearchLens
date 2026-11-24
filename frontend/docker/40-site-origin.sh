#!/bin/sh
# Rewrites the absolute URLs in index.html (canonical link, Open Graph and Twitter
# card tags) to the public origin taken from SITE_ADDRESS, the hostname Caddy serves.
# Runs from the nginx image's /docker-entrypoint.d on every container start, always
# from the pristine build output, so a changed SITE_ADDRESS takes effect on restart.
# Without SITE_ADDRESS the local default http://localhost:4200 stays.
set -eu

html=/usr/share/nginx/html/index.html
pristine=/usr/share/nginx/index.source.html
default_origin=http://localhost:4200

cp "$pristine" "$html"

# Caddy accepts "host", "host:port", "https://host" and comma- or space-separated lists.
# Use the first address; a bare host means HTTPS.
address=$(printf '%s' "${SITE_ADDRESS:-}" | tr ',' ' ' | awk '{print $1}')
case "$address" in
  "" | :*) echo "$0: SITE_ADDRESS not set, link previews use $default_origin"; exit 0 ;;
  http://* | https://*) origin=$address ;;
  *) origin=https://$address ;;
esac
origin=${origin%/}

# Only hostname characters; anything else would be unsafe in sed and in HTML.
if ! printf '%s' "$origin" | grep -Eq '^https?://[A-Za-z0-9.-]+(:[0-9]+)?$'; then
  echo "$0: SITE_ADDRESS '$address' is not a plain hostname, link previews use $default_origin" >&2
  exit 0
fi

sed -i "s#$default_origin#$origin#g" "$html"
echo "$0: link previews use $origin"
