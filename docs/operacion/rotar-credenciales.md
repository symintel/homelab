# Rotar credenciales

Reemplaza una credencial por otra nueva: periódicamente, o de inmediato si
sospechas que se filtró. En todos los casos la credencial nueva se guarda
primero en 1Password (bóveda `HomeLab`) y después se lleva al clúster.

!!! info "Antes de empezar"
    La app de 1Password desbloqueada, con *Integrate with other apps*, y la
    cuenta en la variable de entorno:

    ```bash
    export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"  # tu cuenta
    ```

    Los comandos de Ansible se corren desde `ansible/` en `homelab`.

## Resumen

| Credencial | Item en 1Password | Se aplica con |
|---|---|---|
| Private key de una GitHub App (`symintel-terraform`, `symintel-arc-runners`, `symintel-argocd`) | el item con el nombre de la App | `playbook-platform-secrets.yml` |
| Credenciales FTP de un repo | `ftp-<repo>` | `playbook-platform-secrets.yml` + pipeline de `infra` |
| Client secret de Dex (login con GitHub) | `symintel-dex` | `playbook-dex-oauth-secrets.yml` |
| Contraseña de root de los nodos | `root@<nodo>` (la crea el playbook) | `playbook-rotate-root-passwords.yml` |
| Token de ArgoCD del pipeline de `gitops` (cuenta `ci`) | `argocd-ci` | `playbook-platform-secrets.yml` ([cómo generarlo](pipeline-gitops.md#activar-el-diff-contra-el-cluster-una-vez)) |

## Private key de una GitHub App

1. En GitHub: *symintel → Settings → Developer settings → GitHub Apps →*
   la App → *Private keys* → **Generate a private key**.
2. En 1Password, reemplaza el campo `private_key` del item de esa App por el
   contenido completo del `.pem` nuevo.
3. Comprueba y aplica:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

4. Si es la App de ARC (`symintel-arc-runners`), reinicia su *listener* para
   que tome la llave nueva: `kubectl -n arc-systems get pods` y borra el pod
   del listener (se recrea solo). Los runners nuevos ya usan la llave nueva.
5. Cuando todo funcione, borra la llave **vieja** en GitHub (misma página,
   *Delete* junto a la llave anterior) y el `.pem` descargado.

## Credenciales FTP de un repo

1. Cambia la contraseña en cPanel y actualiza el item `ftp-<repo>`.
2. Aplica y relanza el pipeline, que carga los secrets nuevos en los
   environments del repo:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

    Después, en `symintel/infra`: *Actions → tofu → Run workflow* sobre `main`.

## Client secret de Dex

1. En la OAuth App *Symintel Dex*: **Generate a new client secret**. GitHub
   lo muestra una sola vez.
2. Reemplaza `GITHUB_CLIENT_SECRET` en el item `symintel-dex`.
3. Aplica (actualiza `argocd-secret` y reinicia Dex):

    ```bash
    ansible-playbook -i inventory.ini playbook-dex-oauth-secrets.yml --tags argocd
    ```

4. Prueba el login con GitHub en ArgoCD y después borra el secret viejo en la
   OAuth App.

## Contraseña de root de los nodos

Cada corrida genera y aplica una contraseña nueva por nodo, y la guarda en el
item `root@<nodo>`. No afecta al SSH (Secure Shell): el login de root por SSH
ya está deshabilitado; esta contraseña es para la consola.

```bash
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml               # todos
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml --limit deborah
```

## Verificar

- `apply_platform_secrets.py --check` muestra todo en ✓.
- ArgoCD sigue sincronizando `gitops` (`kubectl get applications -n argocd`).
- El runner aparece *Online* en *symintel → Settings → Actions → Runners*.
- El login con GitHub funciona en ArgoCD.
