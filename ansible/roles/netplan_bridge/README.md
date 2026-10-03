# netplan_bridge

Configura **IP estática en `br0`** con Netplan en Debian: bridge L2 sobre la NIC
física, ruta por defecto y DNS.

## Playbook

[`playbook-set-static-ip.yml`](../../playbook-set-static-ip.yml) — Fase 1.

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit invincible
```

Usa `serial: 1` en el playbook: un nodo a la vez (el cambio de IP puede cortar SSH).

## Hosts

`incus_cluster` (los 3 nodos).

## Variables (por host en `inventory.ini`)

| Variable | Ejemplo | Descripción |
|---|---|---|
| `ansible_host` | `192.168.20.6` | IP actual de conexión SSH |
| `static_ip` | `192.168.20.6` | IP fija destino en `br0` |
| `bridge_iface` | `eno1` | Interfaz física del bridge |

Global en [`group_vars/all.yml`](../../group_vars/all.yml):

| Variable | Default | Descripción |
|---|---|---|
| `gateway` | `192.168.20.1` | Gateway por defecto y segundo DNS |
| `dns_primary` | `192.168.20.5` | Primer DNS |
| `lan_prefix_length` | `22` | Prefijo de la LAN |

## Qué hace

1. Instala `netplan.io` y habilita `systemd-networkd`.
2. Resuelve conflictos con `ifupdown` en la NIC física (respaldo en `.ansible.bak`).
3. Genera `/etc/netplan/br0.yaml` desde [`templates/br0.yaml.j2`](templates/br0.yaml.j2).
4. Aplica `netplan apply`, espera SSH en `static_ip` y actualiza `ansible_host`.
5. DNS (antes de instalar paquetes): elimina `systemd-resolved` si existe y escribe `/etc/resolv.conf`
   estático con `search {{ dns_domain }}` y los `nameserver` `dns_primary` y
   `gateway`.

## Verificar

```bash
ip -br addr show br0
cat /etc/resolv.conf   # search mco.local, nameserver 192.168.20.5 y 192.168.20.1
```

## Documentación

- [Fase 1 — Red](../../../docs/implementacion/fase-1-red.md)
- [Red — netplan](../../../docs/networking/index.md)
