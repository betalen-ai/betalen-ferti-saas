#!/bin/sh
set -eu

output=/usr/share/nginx/html/runtime-config.js
url=${VITE_SUPABASE_URL:-}
key=${VITE_SUPABASE_PUBLISHABLE_KEY:-}

json_string() {
  value=$1
  value=$(printf '%s' "$value" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\r/\\r/g; s/\n/\\n/g')
  printf '"%s"' "$value"
}

printf 'window.__BETALEN_CONFIG__ = { supabaseUrl: %s, supabasePublishableKey: %s };\n' \
  "$(json_string "$url")" "$(json_string "$key")" > "$output"