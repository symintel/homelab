# incus_ovn

OVN para Incus (opcional, apagado por defecto): base de datos de OVN en alta disponibilidad en los tres nodos, red
*uplink* sobre `br0` y una red OVN. Con OVN, Incus puede crear balanceadores de red (`incus network load-balancer`).

## Playbook

Va dentro de [`playbook-incus-cluster.yml`](../../playbook-incus-cluster.yml) (tag `ovn`). Con `incus_ovn_enabled: false`
(el valor por defecto, en `group_vars/incus_cluster/ovn.yml`) ese playbook no lo toca.

```bash
cd ansible
# Preflight (solo lectura): nada se instala
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --tags ovn --skip-tags always -e incus_ovn_enabled=true
# Instalar y crear las redes
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --tags ovn --skip-tags always -e incus_ovn_enabled=true -e incus_ovn_confirm=true
```

`--skip-tags always` evita volver a pasar por los tramos de bootstrap y join del clúster.

## Fases (`incus_ovn_phase`)

| Fase | Hosts | Qué hace |
|---|---|---|
| `preflight` | todos los nodos | Versión de Incus, paquetes, memoria libre, bridge y que las IP reservadas no respondan |
| `install` | todos, `serial: 1` (el líder primero) | `ovn-central`, `ovn-host`, `openvswitch-switch`; la base de datos en clúster y `ovn-controller` |
| `networks` | `invincible` | Conexión de Incus a OVN, uplink sobre `br0` y red `ovn-lan` |

## Variables

En `group_vars/incus_cluster/ovn.yml` (las que se editan) y `defaults/main.yml` (el resto).

| Variable | Valor | Qué es |
|---|---|---|
| `incus_ovn_enabled` | `false` | Activa el rol |
| `incus_ovn_confirm` | `false` | `true` instala; `false` solo preflight |
| `incus_ovn_lb_routes` | `192.168.23.224/28` | Segmento LB: `ipv4.routes` de la uplink |
| `incus_ovn_external_ranges` | `192.168.23.240-192.168.23.249` | Segmento OVN externo: `ipv4.ovn.ranges` |
| `incus_ovn_internal_cidr` | `192.168.19.1/24` | Segmento OVN interno: `ipv4.address` (con NAT) |

Los dos primeros son de la LAN: deben quedar fuera del DHCP (`192.168.20.31-192.168.23.191`) y del pool de MetalLB
(`192.168.23.200-192.168.23.220`); el preflight falla si solapan.
La base de datos de OVN va por `tcp` sin cifrar (como en la guía de Incus).
