#!/usr/bin/env bash
# Deploy a release on the server, from the repository checkout:
#   ./deploy/deploy.sh v1.0.0              # check out the tag, build, start, verify
#   ./deploy/deploy.sh v1.0.0 --reingest   # also rebuild the dense tier index
# The expected tier is EXPECTED_TIER, else RETRIEVAL_TIER from .env, else light.
# With minimal (2 GB servers), no PyTorch image is built and nothing is downloaded:
# the TF-IDF index is built into the backend image.
# GitHub Actions runs the same script over SSH; see .github/workflows/deploy.yml.
set -euo pipefail

# A function body is parsed completely before it runs, so checking out a newer copy of
# this script mid-run cannot change what executes.
main() {
  ref="${1:?usage: deploy/deploy.sh <tag-or-commit> [--reingest]}"
  reingest="${2:-}"
  if [[ ! "$ref" =~ ^[A-Za-z0-9._/-]+$ ]]; then
    echo "Refusing unexpected ref: $ref" >&2
    exit 2
  fi

  cd "$(dirname "$0")/.."
  if [[ ! -f .env ]]; then
    echo "Missing .env next to docker-compose.yml; copy .env.example and fill it in." >&2
    exit 1
  fi
  configured_tier="$(sed -n 's/^RETRIEVAL_TIER=[[:space:]]*//p' .env | tail -n 1 | tr -d '"[:space:]')"
  expected_tier="${EXPECTED_TIER:-${configured_tier:-light}}"
  [[ "$expected_tier" == "auto" ]] && expected_tier=light
  compose=(docker compose -f docker-compose.yml)
  if [[ "$expected_tier" != "minimal" ]]; then
    compose+=(-f docker-compose.models.yml)
  fi
  compose+=(-f docker-compose.prod.yml)

  echo "==> Checking out $ref"
  git fetch --tags --prune origin
  git -c advice.detachedHead=false checkout --detach "$ref"

  echo "==> Building images"
  "${compose[@]}" build --pull

  # Dense indexes live in the tier-indexes volume and survive redeploys.
  if [[ "$expected_tier" != "minimal" ]] && { [[ "$reingest" == "--reingest" ]] ||
    ! "${compose[@]}" run --rm --no-deps backend test -f "/app/data/tiers/$expected_tier.json"; }; then
    echo "==> Building the $expected_tier tier index (one-time model download)"
    "${compose[@]}" run --rm --no-deps backend python -m researchlens.ingest --tier "$expected_tier"
  fi

  echo "==> Starting the stack"
  "${compose[@]}" up -d --wait --remove-orphans

  echo "==> Verifying /api/health"
  health="$("${compose[@]}" exec -T backend python -c \
    "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/health').read().decode())")"
  echo "$health"
  if [[ "$health" != *"\"retrieval_tier\":\"$expected_tier\""* ]]; then
    echo "Expected retrieval_tier $expected_tier. Check: ${compose[*]} logs backend" >&2
    exit 1
  fi
  docker image prune -f >/dev/null
  echo "==> Deployed $(git rev-parse --short HEAD)"
}

main "$@"
