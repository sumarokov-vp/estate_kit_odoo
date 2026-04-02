#!/usr/bin/env bash
set -euo pipefail

ANTHROPIC_API_KEY=$(gpg --quiet --yes --batch --decrypt ~/.password-store/agent_fleet/infra/anthropic_key.gpg)
export ANTHROPIC_API_KEY

exec hurl --variable "anthropic_api_key=$ANTHROPIC_API_KEY" "$@"
