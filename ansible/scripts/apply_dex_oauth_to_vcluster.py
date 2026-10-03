#!/usr/bin/env python3
"""Aplica VCLUSTER_CLIENT_SECRET en el release Helm de vCluster Platform.

Requiere release `vcluster-platform` ya desplegado (Fase 5).
Invocado por playbook-dex-oauth-secrets.yml --tags vcluster.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from onepassword_homelab import (  # noqa: E402
    config_summary,
    create_client,
    ensure_generated_oauth_fields,
    resolve_field,
)

RELEASE = "vcluster-platform"
NAMESPACE = "vcluster-platform"
CHART_REPO = "loft"
CHART_REPO_URL = "https://charts.loft.sh"
CHART = "loft/vcluster-platform"
HELM_SET_KEY = "config.auth.oidc.clientSecret"


def helm_release_exists() -> bool:
    result = subprocess.run(
        ["helm", "status", RELEASE, "-n", NAMESPACE],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


async def main() -> int:
    print(f"1Password {config_summary()}")
    client = await create_client()
    await ensure_generated_oauth_fields(client)
    secret = await resolve_field(client, "VCLUSTER_CLIENT_SECRET")

    if not helm_release_exists():
        print(
            f"Release Helm {RELEASE!r} no encontrado en {NAMESPACE}. "
            "Despliega vcluster-platform (Fase 5) antes de --tags vcluster.",
            file=sys.stderr,
        )
        return 1

    subprocess.run(
        ["helm", "repo", "add", CHART_REPO, CHART_REPO_URL],
        capture_output=True,
        check=False,
    )
    subprocess.run(["helm", "repo", "update", CHART_REPO], check=False)

    subprocess.run(
        [
            "helm",
            "upgrade",
            RELEASE,
            CHART,
            "-n",
            NAMESPACE,
            "--reuse-values",
            "--set-string",
            f"{HELM_SET_KEY}={secret}",
        ],
        check=True,
    )
    print(f"Helm {RELEASE}: {HELM_SET_KEY} actualizado.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001 — script CLI
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
