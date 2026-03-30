#!/usr/bin/env bash
set -euo pipefail

# Cloudflare Access user management for CRM Tech Docs
# App: crm-docs.estate-kit.com
# App ID: 73dc1b87-bb51-4336-b330-21fc83213d1c

CF_TOKEN="$(pass agent_fleet/projects/estate-kit/cloudflare_api_token)"
CF_ACCOUNT_ID="$(pass agent_fleet/infra/cloudflare/estate-kit | grep account_id | cut -d= -f2-)"
APP_ID="73dc1b87-bb51-4336-b330-21fc83213d1c"

CF_BASE="https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/apps/$APP_ID"
AUTH="Authorization: Bearer $CF_TOKEN"
CT="Content-Type: application/json"

usage() {
  cat <<'EOF'
Usage: users.sh <command> [options]

Commands:
  list                          List all access policies (who has access)
  add EMAIL [EMAIL...]          Grant access to one or more emails
  remove EMAIL                  Revoke access for an email
  add-domain DOMAIN             Grant access to all emails from domain (e.g. company.com)

Examples:
  users.sh list
  users.sh add user@example.com
  users.sh add user1@example.com user2@example.com
  users.sh remove user@example.com
  users.sh add-domain example.com
EOF
  exit 1
}

cmd_list() {
  curl -sS -H "$AUTH" "$CF_BASE/policies" | jq '[.result[] | {id, name, decision, emails: [.include[]? | .email?.email // .email_domain?.domain // "everyone"]}]'
}

cmd_add() {
  local emails=("$@")
  local include=""

  include=$(printf '%s\n' "${emails[@]}" | jq -R . | jq -s '[.[] | {email: {email: .}}]')

  local name
  if [[ ${#emails[@]} -eq 1 ]]; then
    name="${emails[0]}"
  else
    name="Group: ${emails[*]}"
  fi

  local body
  body=$(jq -n --arg name "$name" --argjson include "$include" '{name: $name, decision: "allow", include: $include}')

  curl -sS -X POST -H "$AUTH" -H "$CT" -d "$body" "$CF_BASE/policies" | jq '{success: .success, result: .result | {id, name, decision}}'
}

cmd_remove() {
  local email="$1"

  # Find policy containing this email
  local policy_id
  policy_id=$(curl -sS -H "$AUTH" "$CF_BASE/policies" | jq -r --arg email "$email" '.result[] | select(.include[]? | .email?.email == $email) | .id')

  if [[ -z "$policy_id" ]]; then
    echo "Error: no policy found for $email" >&2
    exit 1
  fi

  curl -sS -X DELETE -H "$AUTH" "$CF_BASE/policies/$policy_id" | jq '{success: .success}'
}

cmd_add_domain() {
  local domain="$1"

  local body
  body=$(jq -n --arg name "Domain: $domain" --arg d "$domain" '{name: $name, decision: "allow", include: [{email_domain: {domain: $d}}]}')

  curl -sS -X POST -H "$AUTH" -H "$CT" -d "$body" "$CF_BASE/policies" | jq '{success: .success, result: .result | {id, name, decision}}'
}

[[ $# -lt 1 ]] && usage

case "$1" in
  list) cmd_list ;;
  add) [[ $# -lt 2 ]] && usage; cmd_add "${@:2}" ;;
  remove) [[ $# -lt 2 ]] && usage; cmd_remove "$2" ;;
  add-domain) [[ $# -lt 2 ]] && usage; cmd_add_domain "$2" ;;
  *) usage ;;
esac
