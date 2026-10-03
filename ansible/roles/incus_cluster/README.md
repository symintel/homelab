# incus_cluster

Bootstrap, join y post-configuración del **clúster Incus** (3 nodos) con
`incus admin init --preseed`. Storage default: driver `dir`, pool `local`.

## Playbook

[`playbook-incus-cluster.yml`](../../playbook-incus-cluster.yml) — Fase 2 (tras `incus_install`).

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-incus-cluster.yml
```

Tags: `bootstrap`, `join`, `groups`, `scheduler`, `ui` (UI en rol `incus_ui`).

## Hosts

| Play | Hosts | Fase |
|---|---|---|
| Bootstrap | `invincible` | `incus_cluster_phase: bootstrap` |
| Join | `oliver`, `deborah` (`serial: 1`) | `incus_cluster_phase: join` |
| Post | `invincible` | groups, scheduler + `incus_ui` |

## Variables

Global: [`group_vars/incus_cluster.yml`](../../group_vars/incus_cluster.yml).

| Variable | Default | Descripción |
|---|---|---|
| `incus_storage_driver` | `dir` | Backend del pool local |
| `incus_storage_pool` | `local` | Nombre del pool |
| `incus_storage_path` | `/var/lib/incus/storage-pools/local` | Ruta (dir); override en deborah/NVMe |
| `incus_storage_min_free_gb` | `20` | Espacio libre mínimo antes del init (solo aplica con driver `dir`, se salta si `incus_storage_device` está definido) |
| `incus_storage_device` | _(sin default — solo host_var explícito)_ | Dispositivo de bloque dedicado (ej. `/dev/nvme0n1`) para drivers `zfs`/`btrfs`/`lvm`. Se valida que exista antes del init. En bootstrap se pasa como `config.source`; en join, como `member_config` (cada miembro puede tener un dispositivo distinto). |
| `incus_storage_loop_size` | _(sin default — solo host_var explícito)_ | Alternativa a `incus_storage_device`: tamaño de un archivo loop-backed (ej. `20GB`) cuando no hay disco dedicado. Solo se usa en bootstrap si `incus_storage_device` no está definido. |
| `incus_bridge` | `br0` | Parent del NIC en perfil `default` |
| `incus_cluster_leader` | `invincible` | Nodo que emite tokens de join |
| `incus_cluster_group_assignments` | ver group_vars | Asignación de groups por host |

Por host: `incus_cluster_role` (`bootstrap` | `member`) en `host_vars/`.

## Qué hace

1. Valida espacio en disco en `incus_storage_path` (driver `dir`; el directorio lo crea Incus durante el preseed).
2. **Bootstrap** en invincible: preseed con clustering, pool `local`, perfil `br0`.
3. **Join** en oliver/deborah: `incus cluster add` (delegado al leader) + preseed join.
4. **Post** en invincible: cluster groups (`x86-nodes`, `arm64-nodes`), scheduler manual en oliver.

Idempotente: salta init si el host ya aparece en `incus cluster list`.

## Verificar

```bash
incus cluster list
incus cluster group list
incus storage list
incus profile show default
```

## Documentación

- [Fase 2 — Incus](../../../docs/implementacion/fase-2-incus.md)
- [Clúster Incus](../../../docs/incus/cluster-setup.md)
