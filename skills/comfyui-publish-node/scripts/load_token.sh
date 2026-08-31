# Resolve the Comfy Registry token into $TOKEN. Source it, don't execute it:
#
#     . /path/to/skills/comfyui-publish-node/scripts/load_token.sh
#     uvx comfy-cli node publish --token "$TOKEN"
#
# Order: process environment -> .env in the current directory -> refuse.
# Never prints the token. Sets TOKEN and returns 0, or prints why and exits 1.
#
# Both steps must run in ONE shell invocation: shell state does not survive
# between separate tool calls, so a token loaded in an earlier call is gone.

TOKEN="${REGISTRY_ACCESS_TOKEN:-${COMFY_REGISTRY_TOKEN:-${COMFY_API_KEY:-}}}"
_token_source="environment"

if [ -z "$TOKEN" ] && [ -f .env ]; then
  _token_source=".env"
  # Last matching assignment wins. Strips CR, surrounding whitespace, and one
  # layer of matching single or double quotes.
  TOKEN=$(
    grep -aE '^[[:space:]]*(REGISTRY_ACCESS_TOKEN|COMFY_REGISTRY_TOKEN|COMFY_API_KEY)[[:space:]]*=' .env \
      | tail -1 \
      | cut -d= -f2- \
      | tr -d '\r' \
      | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
            -e 's/^"\(.*\)"$/\1/' \
            -e "s/^'\(.*\)'\$/\1/"
  )
fi

if [ -z "$TOKEN" ]; then
  echo "No Comfy Registry token configured - refusing to publish." >&2
  echo "" >&2
  echo "Create an API key at https://registry.comfy.org (publisher page -> API Keys)," >&2
  echo "then set it in the environment or in .env in this directory:" >&2
  echo "" >&2
  echo "    REGISTRY_ACCESS_TOKEN=<your key>" >&2
  echo "" >&2
  echo "Accepted names: REGISTRY_ACCESS_TOKEN, COMFY_REGISTRY_TOKEN, COMFY_API_KEY." >&2
  echo "If you use .env, add .env to .gitignore first." >&2
  exit 1
fi

# Presence and length only - never the value.
echo "Token loaded from ${_token_source} (${#TOKEN} chars)." >&2

if [ "$_token_source" = ".env" ]; then
  if git check-ignore -q .env 2>/dev/null; then
    echo ".env is gitignored - ok." >&2
  else
    echo "WARNING: .env is NOT gitignored. Add it to .gitignore before publishing." >&2
  fi
fi

unset _token_source
