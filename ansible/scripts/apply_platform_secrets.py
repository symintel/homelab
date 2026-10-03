#!/usr/bin/env python3
"""Secretos de plataforma de la org symintel: 1Password -> clúster.

Crea (o actualiza) los namespaces y Secrets que tienen que existir ANTES de
GitOps, y que no pueden vivir en git:

  argocd/repo-gitops                       App symintel-argocd: ArgoCD lee symintel/gitops (privado)
  arc-runners/arc-runners-github-app       App de ARC (registro del runner)
  arc-runners/symintel-terraform-app       App de OpenTofu, como TF_VAR_github_app_*
  arc-runners/tofu-vars                    TF_VAR_ftp (credenciales FTP por repo)
  arc-runners/argocd-ci                    ARGOCD_AUTH_TOKEN (opcional: diff del pipeline de gitops)
  kube-system/sealed-secrets-key-homelab   llave de Sealed Secrets (opcional, ver abajo)
  namespace terraform                      state de OpenTofu (lo escribe el runner)

El único scale set (arc-runners, desplegado por ArgoCD desde symintel/gitops)
monta los dos últimos Secrets como variables de entorno.

Items esperados en la bóveda (ONEPASSWORD_VAULT, default HomeLab); ver
docs/symintel/github.md:

  symintel-argocd       app_id, installation_id, private_key
  sealed-secrets        (opcional) certificate, private_key: el par de Sealed Secrets
  symintel-arc-runners  app_id, installation_id, private_key
  symintel-terraform    app_id, installation_id, private_key
  ftp-<repo>            (uno por repo con deploy) dev_host, dev_user,
                        dev_password, dev_remote_dir, prod_host, prod_user,
                        prod_password, prod_remote_dir

Uso:
  python3 ansible/scripts/apply_platform_secrets.py            # aplica
  python3 ansible/scripts/apply_platform_secrets.py --dry-run  # imprime manifiestos sin secretos
  python3 ansible/scripts/apply_platform_secrets.py --check    # qué campos tiene cada item y qué falta
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from onepassword_homelab import VAULT_NAME, create_client, find_vault_id  # noqa: E402

# Tiene que coincidir con el repoURL de las Applications de symintel/gitops.
GITOPS_REPO_URL = "https://github.com/symintel/gitops.git"
RUNNER_NAMESPACE = "arc-runners"
STATE_NAMESPACE = "terraform"
FTP_ITEM_PREFIX = "ftp-"
# Token de la cuenta "ci" de ArgoCD (solo lectura). Opcional: se genera recién
# cuando ArgoCD funciona; mientras no exista el item, el Secret no se crea.
ARGOCD_CI_ITEM = "argocd-ci"
# Par de llaves de Sealed Secrets, generado por el operador (docs/symintel/github.md).
# El controlador usa un Secret tls de kube-system con la etiqueta "active" en vez de
# generar su propia llave: así los SealedSecret de git sobreviven a reinstalar K3s.
# Opcional: hasta la Fase 6 (CAPN) nada lo necesita.
SEALED_ITEM = "sealed-secrets"
SEALED_NAMESPACE = "kube-system"
SEALED_SECRET_NAME = "sealed-secrets-key-homelab"
SEALED_LABEL = "sealedsecrets.bitnami.com/sealed-secrets-key"
FTP_FIELDS = ("host", "user", "password", "remote_dir")


def normalize_pem(value: str) -> str:
    """Rearma un PEM cuyo cuerpo perdió los saltos de línea (campo de una línea en 1Password)."""
    m = re.search(r"-----BEGIN ([A-Z ]+)-----(.*?)-----END \1-----", value, re.S)
    if not m:
        raise ValueError("el campo no contiene un bloque PEM (-----BEGIN ...-----)")
    label, body = m.group(1), re.sub(r"\s+", "", m.group(2))
    return f"-----BEGIN {label}-----\n" + "\n".join(textwrap.wrap(body, 64)) + f"\n-----END {label}-----\n"


async def resolve(client, ref: str) -> str:
    """client.secrets.resolve, pero el error dice qué referencia falló."""
    try:
        return await client.secrets.resolve(ref)
    except Exception as exc:  # noqa: BLE001 — se re-lanza con contexto
        raise RuntimeError(f"{ref}: {exc} (revisa con --check)") from exc


def namespace(name: str, *, baseline: bool = False) -> dict:
    labels = {"pod-security.kubernetes.io/enforce": "baseline"} if baseline else {}
    return {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": name, "labels": labels}}


def secret(ns: str, name: str, data: dict[str, str], labels: dict[str, str] | None = None, type_: str = "Opaque") -> dict:
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": name, "namespace": ns, "labels": labels or {}},
        "type": type_,
        "stringData": data,
    }


def check_pem(pem: str, ref: str) -> str:
    """Valida que la private key de una GitHub App se pueda leer (sin mostrarla)."""
    from cryptography.hazmat.primitives import serialization

    try:
        serialization.load_pem_private_key(pem.encode(), password=None)
    except Exception as exc:  # noqa: BLE001 — error con contexto
        raise RuntimeError(f"{ref}: no es una private key PEM válida (empieza con {pem.splitlines()[0]!r}): {exc}") from exc
    return pem


def check_sealed_pair(cert_pem: str, key_pem: str) -> None:
    """El certificado tiene que ser X.509 y corresponder a la llave privada."""
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode())
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"op://{VAULT_NAME}/{SEALED_ITEM}/certificate: no es un certificado X.509 PEM válido: {exc}") from exc
    try:
        key = serialization.load_pem_private_key(key_pem.encode(), password=None)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"op://{VAULT_NAME}/{SEALED_ITEM}/private_key: no es una llave privada PEM válida: {exc}") from exc
    fmt = (serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    if cert.public_key().public_bytes(*fmt) != key.public_key().public_bytes(*fmt):
        raise RuntimeError(
            f"op://{VAULT_NAME}/{SEALED_ITEM}: el certificado y la llave privada NO son un par "
            "(la llave no corresponde a ese certificado). Revisa que copiaste tls.crt y tls.key del mismo par."
        )


async def read_optional(client, ref: str) -> str:
    """Como resolve(), pero devuelve "" si el item o el campo no existen."""
    try:
        return await client.secrets.resolve(ref)
    except Exception:  # noqa: BLE001 — opcional
        return ""


async def read_app(client, item: str) -> dict[str, str]:
    ref = f"op://{VAULT_NAME}/{item}"
    return {
        "app_id": (await resolve(client, f"{ref}/app_id")).strip(),
        "installation_id": (await resolve(client, f"{ref}/installation_id")).strip(),
        "private_key": check_pem(normalize_pem(await resolve(client, f"{ref}/private_key")), f"{ref}/private_key"),
    }


async def read_ftp(client) -> dict[str, dict]:
    """{repo: {dev: {...}, prod: {...}}} desde los items ftp-<repo> de la bóveda."""
    vault_id = await find_vault_id(client)
    result: dict[str, dict] = {}
    for overview in await client.items.list(vault_id):
        if not overview.title.startswith(FTP_ITEM_PREFIX):
            continue
        repo = overview.title[len(FTP_ITEM_PREFIX):]
        ref = f"op://{VAULT_NAME}/{overview.title}"
        result[repo] = {
            env: {f: (await resolve(client, f"{ref}/{env}_{f}")).strip() for f in FTP_FIELDS}
            for env in ("dev", "prod")
        }
    return result


async def build_manifests() -> list[dict]:
    client = await create_client()

    argocd = await read_app(client, "symintel-argocd")
    arc = await read_app(client, "symintel-arc-runners")
    tf = await read_app(client, "symintel-terraform")
    ftp = await read_ftp(client)

    manifests: list[dict] = [
        namespace("argocd"),
        namespace(RUNNER_NAMESPACE, baseline=True),
        namespace(STATE_NAMESPACE),
    ]

    manifests.append(
        secret(
            "argocd",
            "repo-gitops",
            {
                "type": "git",
                "url": GITOPS_REPO_URL,
                "githubAppID": argocd["app_id"],
                "githubAppInstallationID": argocd["installation_id"],
                "githubAppPrivateKey": argocd["private_key"],
            },
            labels={"argocd.argoproj.io/secret-type": "repository"},
        )
    )
    manifests.append(
        secret(
            RUNNER_NAMESPACE,
            "arc-runners-github-app",
            {
                "github_app_id": arc["app_id"],
                "github_app_installation_id": arc["installation_id"],
                "github_app_private_key": arc["private_key"],
            },
        )
    )
    manifests.append(
        secret(
            RUNNER_NAMESPACE,
            "symintel-terraform-app",
            {
                "TF_VAR_github_app_id": tf["app_id"],
                "TF_VAR_github_app_installation_id": tf["installation_id"],
                "TF_VAR_github_app_private_key": tf["private_key"],
            },
        )
    )
    manifests.append(secret(RUNNER_NAMESPACE, "tofu-vars", {"TF_VAR_ftp": json.dumps(ftp)}))
    token = await read_optional(client, f"op://{VAULT_NAME}/{ARGOCD_CI_ITEM}/token")
    if token:
        manifests.append(secret(RUNNER_NAMESPACE, "argocd-ci", {"ARGOCD_AUTH_TOKEN": token.strip()}))
    else:
        print(f"Aviso: sin item {ARGOCD_CI_ITEM!r} en 1Password: el pipeline de gitops omitirá el diff de ArgoCD.", file=sys.stderr)

    sealed_cert = await read_optional(client, f"op://{VAULT_NAME}/{SEALED_ITEM}/certificate")
    sealed_key = await read_optional(client, f"op://{VAULT_NAME}/{SEALED_ITEM}/private_key")
    if sealed_cert and sealed_key:
        cert_pem, key_pem = normalize_pem(sealed_cert), normalize_pem(sealed_key)
        check_sealed_pair(cert_pem, key_pem)
        manifests.append(
            secret(
                SEALED_NAMESPACE,
                SEALED_SECRET_NAME,
                {"tls.crt": cert_pem, "tls.key": key_pem},
                labels={SEALED_LABEL: "active"},
                type_="kubernetes.io/tls",
            )
        )
    elif sealed_cert or sealed_key:
        raise RuntimeError(f"El item {SEALED_ITEM!r} tiene solo uno de los campos: hacen falta 'certificate' y 'private_key'.")
    else:
        print(f"Aviso: sin item {SEALED_ITEM!r} en 1Password: Sealed Secrets generará su propia llave (se pierde si reinstalas K3s).", file=sys.stderr)
    return manifests


def redact(manifest: dict) -> dict:
    if manifest["kind"] != "Secret":
        return manifest
    return {**manifest, "stringData": {k: "<redacted>" for k in manifest["stringData"]}}


# Items y campos que el script espera (ver docs/symintel/github.md).
EXPECTED = {
    "symintel-terraform": ["app_id", "installation_id", "private_key"],
    "symintel-arc-runners": ["app_id", "installation_id", "private_key"],
    "symintel-argocd": ["app_id", "installation_id", "private_key"],
}
FTP_EXPECTED = [f"{env}_{f}" for env in ("dev", "prod") for f in FTP_FIELDS]


async def check() -> int:
    """Muestra, sin valores, qué campos tiene cada item esperado y qué falta."""
    client = await create_client()
    vault_id = await find_vault_id(client)
    by_title = {o.title.lower(): o for o in await client.items.list(vault_id)}
    expected = dict(EXPECTED)
    expected.update({t: FTP_EXPECTED for t in by_title if t.startswith(FTP_ITEM_PREFIX)})
    ok = True
    print(f"Bóveda {VAULT_NAME!r}:")
    for title, fields in expected.items():
        if title not in by_title:
            print(f"  ✗ {title}: NO EXISTE el item")
            ok = False
            continue
        item = await client.items.get(vault_id, by_title[title].id)
        sections = {sec.id: sec.title for sec in (item.sections or [])}
        found = {f.title: sections.get(f.section_id) for f in item.fields}
        found_ci = {k.lower(): k for k in found}
        print(f"  {title}  (tipo: {item.category})")
        for name in fields:
            real = found_ci.get(name.lower())
            if real is not None and real != name:
                print(f"    ✗ {name}: existe como {real!r} (el nombre tiene que ser exacto)")
                ok = False
                continue
            if name not in found:
                print(f"    ✗ {name}: falta")
                ok = False
            elif found[name]:
                print(f"    ✗ {name}: está dentro de la sección {found[name]!r} (sácalo de la sección)")
                ok = False
            else:
                print(f"    ✓ {name}")
        extra = sorted(set(found) - set(fields))
        if extra:
            print(f"    · otros campos en el item: {', '.join(repr(x) for x in extra)}")
    if not any(t.startswith(FTP_ITEM_PREFIX) for t in by_title):
        print(f"  · ningún item {FTP_ITEM_PREFIX}<repo> (solo hace falta para repos con deploy)")
    # Opcional: token de solo lectura de ArgoCD para el diff del pipeline de gitops.
    if ARGOCD_CI_ITEM in by_title:
        item = await client.items.get(vault_id, by_title[ARGOCD_CI_ITEM].id)
        has = any(f.title.lower() == "token" for f in item.fields)
        print(f"  {ARGOCD_CI_ITEM}  (opcional)\n    {'✓' if has else '✗'} token")
        ok = ok and has
    else:
        print(f"  · sin item {ARGOCD_CI_ITEM} (opcional: el pipeline de gitops omite el diff de ArgoCD)")
    # Opcional: el par de llaves de Sealed Secrets.
    if SEALED_ITEM in by_title:
        item = await client.items.get(vault_id, by_title[SEALED_ITEM].id)
        found = {f.title: f.value for f in item.fields}
        print(f"  {SEALED_ITEM}  (opcional)")
        for name in ("certificate", "private_key"):
            good = bool(found.get(name))
            print(f"    {'✓' if good else '✗'} {name}")
            ok = ok and good
        if found.get("certificate") and found.get("private_key"):
            try:
                check_sealed_pair(normalize_pem(found["certificate"]), normalize_pem(found["private_key"]))
                print("    ✓ el certificado corresponde a la llave privada")
            except RuntimeError as exc:
                print(f"    ✗ {exc}")
                ok = False
    else:
        print(f"  · sin item {SEALED_ITEM} (opcional: Sealed Secrets generará su propia llave)")
    return 0 if ok else 1


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="imprime los manifiestos (sin valores) y no aplica")
    parser.add_argument("--check", action="store_true", help="lista los campos de cada item esperado (sin valores) y qué falta")
    args = parser.parse_args()

    if args.check:
        return await check()

    manifests = await build_manifests()
    if args.dry_run:
        print(json.dumps([redact(m) for m in manifests], indent=2))
        return 0

    doc = {"apiVersion": "v1", "kind": "List", "items": manifests}
    subprocess.run(["kubectl", "apply", "-f", "-"], input=json.dumps(doc), text=True, check=True)
    tofu_vars = next(m for m in manifests if m["metadata"]["name"] == "tofu-vars")
    ftp_repos = sorted(json.loads(tofu_vars["stringData"]["TF_VAR_ftp"]))
    print(f"Secretos de plataforma aplicados (FTP para: {', '.join(ftp_repos) or 'ninguno'}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001 — script CLI
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
