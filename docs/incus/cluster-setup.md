# Clúster Incus

!!! info "Parte de la guía de implementación"
    Sigue **[Fase 2 — Incus](../implementacion/fase-2-incus.md)** para el orden
    completo. **Ansible** ejecuta bootstrap, join, cluster groups, scheduler y UI (interfaz de usuario)
    vía [`playbook-incus-cluster.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-incus-cluster.yml).
    Los bloques manuales siguientes son referencia.

## Automatización (Ansible)

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-bootstrap.yml
ansible-playbook -i inventory.ini playbook-incus-cluster.yml
```

Roles: [`incus_cluster`](https://github.com/symintel/homelab/blob/main/ansible/roles/incus_cluster/README.md),
[`incus_ui`](https://github.com/symintel/homelab/blob/main/ansible/roles/incus_ui/README.md).

## Almacenamiento

Default HomeLab: driver **`dir`**, pool **`local`**, ruta
`/var/lib/incus/storage-pools/local`. Ansible valida ≥ **20 GB** libres antes del
init (`incus_storage_min_free_gb` en
[`group_vars/incus_cluster/vars.yml`](https://github.com/symintel/homelab/blob/main/ansible/group_vars/incus_cluster/vars.yml)).

| Aspecto | Default |
|---|---|
| Driver | `dir` |
| Pool | `local` (uno por miembro) |
| Ruta | `/var/lib/incus/storage-pools/local` |
| Perfil `default` | root en `local`, NIC bridged a `br0` |

### Por nodo

| Nodo | Nota |
|---|---|
| invincible | 120 GB SSD; leader + UI |
| oliver | Pool local obligatorio; scheduler manual |
| deborah | eMMC boot; override opcional a NVMe: `incus_storage_path: /srv/incus/storage-pools/local` |

### Limitaciones de `dir`

- Sin CoW a nivel de pool; snapshots de instancia y export tarball sí.
- VMs (máquinas virtuales) más lentas que con `zfs`/`btrfs`.
- Cada miembro tiene pool local; no hay Ceph por defecto.

### Alternativas

| Driver | Cuándo | Variable |
|---|---|---|
| `dir` | **Default** HomeLab | `incus_storage_driver: dir` |
| `btrfs` | Snapshots eficientes | `incus_storage_driver: btrfs` + disco/subvolumen |
| `zfs` | VMs + snapshots avanzados | `incus_storage_driver: zfs` |
| `lvm` | Thin LVM para VMs | `incus_storage_driver: lvm` |

<div class="card">
  <div class="card-kicker">Análisis de trade-offs</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Ansible (<code>playbook-incus-cluster.yml</code>)</div>
      <div class="text-muted">Bootstrap/join/UI idempotente</div>
      <div class="text-muted">Requiere playbook previo (<code>incus_install</code>)</div>
    </div>
    <div class="card-col">
      <div class="card-title">Manual</div>
      <div class="text-muted">Depuración nodo a nodo</div>
      <div class="text-muted">Tokens de un solo uso</div>
    </div>
    <div class="card-col">
      <div class="card-title"><code>dir</code></div>
      <div class="text-muted">Sin disco dedicado</div>
      <div class="text-muted">VMs lentas; sin CoW de pool</div>
    </div>
    <div class="card-col">
      <div class="card-title"><code>btrfs</code> / <code>zfs</code></div>
      <div class="text-muted">Snapshots eficientes</div>
      <div class="text-muted">Disco/loop; migración si ya clusterizado</div>
    </div>
    <div class="card-col">
      <div class="card-title">UI vía Ansible</div>
      <div class="text-muted">Mismo playbook que el clúster</div>
      <div class="text-muted">Solo en invincible (daemon nativo)</div>
    </div>
  </div>
</div>

!!! warning "Clúster ya inicializado"
    Cambiar driver requiere migración manual; elige antes del primer playbook.

Docs: [Storage pools](https://linuxcontainers.org/incus/docs/main/explanation/storage/)

## Bootstrap (invincible) — manual

```bash
curl https://pkgs.zabbly.com/get/incus-stable | sudo bash -x
sudo incus admin init
# clustering=yes, no te unes (bootstrap), storage backend dir
```

## Join (oliver y deborah) — manual

```bash
incus cluster add oliver           # ejecutar en invincible; genera token de un solo uso
incus cluster add deborah   # otro token distinto
```
En cada nodo: instalar Incus y `incus admin init`, respondiendo que sí te unes, con el token correspondiente.

## Cluster groups (arquitectura)

```bash
incus cluster group create x86-nodes
incus cluster group create arm64-nodes

incus cluster group assign invincible x86-nodes,default
incus cluster group assign oliver x86-nodes,default
incus cluster group assign deborah arm64-nodes,default
```

## Proteger la RAM de oliver (scheduler manual)

Aunque oliver tiene 15.5 GB medidos, se mantiene como nodo ligero para quorum
Incus sin instancias automáticas:

```bash
incus cluster set oliver scheduler.instance manual
```
Excluye a `oliver` del scheduling automático; solo recibe instancias si se apunta
explícitamente con `--target=oliver`. Sigue contando como voto de quorum.

## UI de administración

Incus expone una **interfaz web nativa** (`incus-ui-canonical`) para gestionar
instancias, perfiles, redes y el clúster. No usa kubeconfig; la autenticación
inicial es por **certificado de cliente** y, tras Fase 4, por **OIDC (OpenID Connect)** (Dex → GitHub).

### Instalación (Ansible o manual)

Ansible instala la UI en **invincible** (`incus_ui`, tag `ui`). La UI **no** es
un contenedor: la sirve el daemon de Incus en `core.https_address`.

=== "Ansible (recomendado)"

    Incluido en `playbook-incus-cluster.yml` (tag `ui`).

=== "Manual"

    En **invincible**:

    ```bash
    sudo apt install incus-ui-canonical
    sudo incus config set core.https_address=:8443
    ```

`/etc/hosts` en tu estación — bloque completo en
[Resumen del HomeLab](../implementacion/resumen-homelab.md#etchosts-en-tu-estacion-de-trabajo):

Acceso inicial: `https://incus.homelab.local:8443` → certificado de cliente.

<div class="card">
  <div class="card-kicker">UI</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Ansible (tag <code>ui</code>)</div>
      <div class="text-muted">Incluido en <code>playbook-incus-cluster.yml</code></div>
      <div class="text-muted">Solo en invincible</div>
    </div>
    <div class="card-col">
      <div class="card-title">Manual (<code>apt</code> + <code>config set</code>)</div>
      <div class="text-muted">Sin Ansible</div>
      <div class="text-muted">Fácil desalinear con el resto del clúster</div>
    </div>
  </div>
</div>

### OIDC vía Dex (Fase 4)

Tras [Fase 4 — Incus UI OIDC](../implementacion/fase-4-gitops.md#incus-ui-oidc):

```bash
incus config set oidc.issuer=https://argocd.homelab.local/api/dex
incus config set oidc.client.id=incus-ui
incus config set oidc.client.secret=<INCUS_CLIENT_SECRET>
incus config set oidc.groups.claim=groups
```

`INCUS_CLIENT_SECRET` **no** se genera en GitHub. Ansible lo genera en
1Password si falta y lo aplica en Dex e Incus (`--tags incus`).

### Permisos OIDC: denegar por defecto

Con fine-grained auth (`incus auth`), un usuario OIDC **no tiene permisos** tras
el primer login hasta que lo vincules a un grupo. Sin grupo mapeado, la UI carga
pero no muestra instancias, proyectos ni configuración del clúster.

```bash
incus auth group create homelab-admins
incus auth group permission add homelab-admins server admin
# Nombre = valor exacto del claim groups de Dex/GitHub (<org>:<team>)
incus auth identity-provider-group create symintel:devops
incus auth identity-provider-group group add symintel:devops homelab-admins
```

| Escenario | Resultado |
|---|---|
| Login SSO, sin grupo IdP mapeado | Autenticado, **sin acceso** a recursos |
| Miembro del team `devops` de la org `symintel` (grupo `symintel:devops` → `homelab-admins`) | Admin del clúster Incus |
| Operador en proyecto concreto | Crear grupo con permisos `project` y mapear equipo GitHub |

Comprobar permisos efectivos de un usuario: `incus auth identity info` (como ese usuario).

Referencias:

- [Incus OIDC](https://linuxcontainers.org/incus/docs/main/authentication/#openid-connect-oidc-authentication)
- [Autorización LXD/Incus](https://canonical.com/lxd/docs/default/explanation/authorization/) (`incus auth`)

## Backup y snapshots (opcional)

No forman parte del bootstrap por defecto. Actívalos cuando quieras proteger
instancias o el estado del clúster.

| Método | Alcance | Cuándo usarlo |
|---|---|---|
| **Snapshots de instancia** | Una instancia, mismo storage pool | Rollback rápido; no sustituye backup offsite |
| **Export tarball** | Instancia o volumen portable | Copia restaurable en otro pool o servidor |
| **Volcado BD** | Metadatos Incus (redes, perfiles) | Complemento ligero en cron |
| **Tar de `/var/lib/incus`** | Servidor completo | DR del nodo bootstrap |

### Snapshots programados (por instancia)

```bash
# Diario a las 06:00; expira a los 7 días
incus config set <instancia> snapshots.schedule="0 6 * * *"
incus config set <instancia> snapshots.expiry=7d
incus config set <instancia> snapshots.pattern="{{ creation_date|date:'2006-01-02' }}"
```

Snapshot manual: `incus snapshot create <instancia> <nombre>`

### Export y volcado de metadatos

```bash
incus export <instancia> /backup/<instancia>.tar.gz
incus admin sql local .dump > /backup/incus-local.sql
incus admin sql global .dump > /backup/incus-global.sql
```

### Limitaciones

- Los snapshots viven en el **mismo storage pool** que la instancia; si pierdes
  el disco, pierdes snapshots y datos.
- En clúster, programa backups en el nodo que aloja la instancia o usa
  `incus copy --refresh` hacia otro servidor Incus para copias offsite.
- Para CAPN/workloads críticos, combina snapshots con export periódico o réplica.

Docs oficiales: [Backup instancias](https://linuxcontainers.org/incus/docs/main/howto/instances_backup/),
[Backup servidor](https://linuxcontainers.org/incus/docs/main/backup/).
