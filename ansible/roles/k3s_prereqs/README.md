# k3s_prereqs

Prepara el **sistema operativo** de todos los nodos antes de instalar K3s:
swap deshabilitado, módulos de kernel, `sysctl` para CNI y requisitos de Longhorn.

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3.

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags prereqs
```

## Hosts

`incus_cluster` (los 3 nodos).

## Tags

`prereqs`, `always` (se ejecuta en cada run del playbook K3s).

## Variables

Ninguna específica del rol.

## Qué hace

1. `swapoff -a` y comenta entradas `swap` en `/etc/fstab`.
2. Carga módulos `br_netfilter` y `overlay` (`/etc/modules-load.d/k3s.conf`).
3. Configura `net.bridge.bridge-nf-call-iptables` e `ip_forward` (`/etc/sysctl.d/k3s.conf`).
4. Aplica `sysctl --system`.
5. Instala `open-iscsi` y `nfs-common`, habilita `iscsid` y carga `iscsi_tcp` (Longhorn no arranca sin ellos).

## Verificar

```bash
swapon --show          # vacío
lsmod | grep br_netfilter
sysctl net.ipv4.ip_forward
```

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md)
- [Opciones del playbook](../../../docs/k3s/playbook-options.md)
