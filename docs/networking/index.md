# Red

!!! info "Parte de la guía de implementación"
    Ejecuta esta fase con **[Fase 1 — Red](../implementacion/fase-1-red.md)** y
    `playbook-set-static-ip.yml`.

## Bridge L2 hacia la LAN física

Los **3 nodos** usan un bridge Linux (`br0`) sobre la interfaz física,
para que las instancias Incus reciban IP directa de la LAN (red local) y sean
alcanzables entre hosts sin necesitar OVN (Open Virtual Network).

| Nodo | Interfaz física | IP en br0 (estática) |
|---|---|---|
| invincible | `eno2` | 192.168.20.6 |
| oliver | `eno1` | 192.168.20.7 |
| deborah | `enP4p65s0` | 192.168.20.5 |

> Confirmá con `ip -br link` en el nodo antes de aplicar — el nombre de la
> interfaz física puede diferir de esta tabla tras una actualización de OS.

Ejemplo netplan — invincible:

```yaml
# /etc/netplan/br0.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eno2:
      dhcp4: no
  bridges:
    br0:
      interfaces: [eno2]
      addresses: [192.168.20.6/22]
      routes:
        - to: default
          via: 192.168.20.1
      nameservers:
        addresses: [192.168.20.5, 192.168.20.1]
```

Ejemplo netplan — deborah (misma subred, distinta interfaz y último octeto):

```yaml
# /etc/netplan/br0.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enP4p65s0:
      dhcp4: no
  bridges:
    br0:
      interfaces: [enP4p65s0]
      addresses: [192.168.20.5/22]
      routes:
        - to: default
          via: 192.168.20.1
      nameservers:
        addresses: [192.168.20.5, 192.168.20.1]
```

```bash
ip -br link
sudo apt install -y netplan.io   # Debian no lo trae instalado por defecto
sudo netplan apply              # corta SSH si cambias de IP
```

El playbook Ansible instala `netplan.io`, habilita `systemd-networkd` y migra
la NIC (tarjeta de red) fuera de ifupdown antes de escribir `/etc/netplan/br0.yaml`.

```bash
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit deborah
```

Perfil de Incus para usar el bridge en las instancias:

```bash
incus profile device add default eth0 nic nictype=bridged parent=br0
```

## IP fija — por qué es obligatoria aquí

1. **Incus cluster**: `cluster.https_address` queda grabada por IP al hacer join.
2. **K3s (distribución ligera de Kubernetes)**: kubelet usa la IP del nodo como identidad.
3. **CAPN (Cluster API Provider for Incus)**: el `Secret` `lxc-secret` apunta a `https://<IP>:8443` como string fijo.

## Esquema de IPs

| Nodo | IP actual (DHCP/pre-bridge) | IP en br0 |
|---|---|---|
| invincible | 192.168.23.162 | 192.168.20.6 |
| oliver | 192.168.20.87 | 192.168.20.7 |
| deborah | 192.168.21.211 | 192.168.20.5 |

> La LAN es un `/22` (`192.168.20.0`–`192.168.23.255`), no un `/24` — las
> IPs "actuales" de esta tabla son leases DHCP dentro de ese mismo rango
> (no subredes distintas). La fuente de verdad en todo momento es
> `ansible_host` en `inventory.ini`.

IPs fijas y reservadas de la LAN:

| Uso | IP / rango | Dónde se configura |
|---|---|---|
| deborah, invincible, oliver | `192.168.20.5`, `.6`, `.7` | `static_ip` en `inventory.ini` |
| VIP del API de K3s (kube-vip, opcional) | `192.168.20.4` | `kube_vip.address` en `k3s_install.yml` |
| Pool de MetalLB (`LoadBalancer`, Gateway) | `192.168.23.200–192.168.23.220` | [`gitops/metallb/ipaddresspool.yaml`](https://github.com/symintel/gitops/blob/main/metallb/ipaddresspool.yaml) |

!!! warning "Fuera del DHCP"
    Como el DHCP del router reparte en toda la `/22`, estas IPs y el pool de
    MetalLB tienen que quedar **reservados o fuera del rango del DHCP** en el
    router. Si no, el router puede dárselas a otro equipo y chocar.

Tras `playbook-set-static-ip.yml`, actualizar `ansible_host` en
[`inventory.ini`](https://github.com/symintel/homelab/blob/main/ansible/inventory.ini)
al valor de `static_ip` si la IP de conexión cambió.
