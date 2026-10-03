# storage_provision

Formatea y monta un disco libre, y lo wirea a Longhorn (disco dedicado) o a
un pool nuevo de Incus, según se decida leyendo el reporte de discovery
(`reports/<host>.md`, sección "Recomendaciones de almacenamiento").

**DESTRUCTIVO** — `mkfs` borra cualquier dato existente en el disco. No
correr sin confirmar antes qué disco y qué consumidor usar.

## Playbook

[`playbook-storage-provision.yml`](../../playbook-storage-provision.yml).

## Variables (host_vars)

```yaml
storage_provision_disks:
  - device: /dev/nvme0n1
    consumer: longhorn   # o "incus"
    mount_path: /var/lib/longhorn-nvme0n1
    filesystem: ext4
    # solo si consumer == incus:
    incus_pool_name: nvme-pool
```

Sin esta variable definida en el host, `playbook-storage-provision.yml` no hace nada en ese host (ver el `when` a nivel de role en el playbook).

## Qué hace

1. Pausa de seguridad (igual que `netplan_bridge`) — confirma antes de tocar el disco.
2. `blkid` para chequear si ya tiene filesystem (idempotente — no reformatea si ya tiene uno).
3. Formatea con `ansible.builtin.filesystem` si hace falta.
4. Monta y persiste en `/etc/fstab` por UUID (`ansible.posix.mount`).
5. Según `consumer`:
   - `longhorn`: anota el nodo K8s (`node.longhorn.io/default-disks-config`).
   - `incus`: crea un storage pool nuevo (`incus storage create ... dir source=...`), separado del pool `local` del bootstrap — no toca `preseed-bootstrap.yml.j2`.

## Ejecutar

```bash
ansible-playbook -i inventory.ini playbook-storage-provision.yml --limit deborah
```

## Verificar

```bash
ansible deborah -m command -a "df -h /var/lib/longhorn-nvme0n1"
ansible deborah -m command -a "k3s kubectl get node deborah -o jsonpath='{.metadata.annotations}'"  # si consumer=longhorn
ansible deborah -m command -a "incus storage list"  # si consumer=incus
```
