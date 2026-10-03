# wifi_failover

WiFi como respaldo del cable, solo en nodos con hardware WiFi
(`has_wifi: true` — hoy: oliver, deborah; invincible no tiene WiFi físico).

## Playbook

[`playbook-wifi-failover.yml`](../../playbook-wifi-failover.yml).

## Variables

| Variable | Host | Descripción |
|---|---|---|
| `has_wifi` | oliver, deborah | Gate del role |
| `wifi_iface` | oliver=`wlo1`, deborah=`wlP2p33s0` | Interfaz WiFi física |
| `wifi_ssid` / `wifi_psk` | — | Vía Vault (`group_vars/incus_cluster/vault.yml`), nunca en texto plano en el repo |

## Qué hace

1. Instala `network-manager` si falta (oliver).
2. Marca `br0` y la NIC física cableada como `unmanaged` para NetworkManager — sigue siendo `systemd-networkd`/netplan quien las gestiona.
3. `dns=none` — NetworkManager no toca `/etc/resolv.conf` (lo gestiona el rol `netplan_bridge`).
4. Crea el perfil `homelab-backup` con `route-metric 700` (mayor que la ruta cableada, ~100) — el cable manda cuando está disponible, WiFi solo toma tráfico si se cae.

## Verificar

```bash
ansible oliver -m command -a "nmcli connection show"
ansible oliver -m command -a "nmcli device status"
```
