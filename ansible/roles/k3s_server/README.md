# k3s_server

Instala el **K3s control-plane** (server) en el nodo designado como `k3s_server`.

En el homelab: **deborah** (`k3s_role: server`).

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3.

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags server
```

## Hosts

`k3s_server` (lista explícita en `inventory.ini`: deborah). `serial: 1`.

## Tags

`server`, `core`.

## Variables

Desde [`group_vars/incus_cluster/k3s_install.yml`](../../group_vars/incus_cluster/k3s_install.yml):

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.core.version` | `v1.36.2+k3s1` | Versión K3s |
| `k3s_install.core.disable_components` | traefik, servicelb | `--disable` en install |
| `k3s_install.core.cluster_cidr` | `10.42.0.0/16` | Pod CIDR |
| `k3s_install.core.service_cidr` | `10.43.0.0/16` | Service CIDR |
| `k3s_install.core.cni` | `flannel` | `flannel`, `canal`, `calico`, `cilium` |
| `k3s_install.core.flannel_backend` | `vxlan` | Solo si `cni: flannel` |
| `k3s_install.core.tls_sans_extra` | `[]` | SANs extra en cert API |
| `k3s_install.core.embedded_registry` | `false` | `--embedded-registry` |
| `k3s_install.kube_vip.enabled` | `false` | Si true, añade VIP a TLS SANs |
| `k3s_server_tls_sans` | — | SANs adicionales por host (`host_vars`) |

## Qué hace

1. Calcula TLS SANs (IP, hostname, kube-vip opcional).
2. Instala K3s server vía `get.k3s.io` si no está activo (`--flannel-backend=none` si `cni` ≠ flannel).
3. Espera API en `:6443`.
4. Publica `k3s_token` en facts para el play de agents (siguiente).

Siguiente play opcional: rol [`k3s_cni`](../k3s_cni/README.md) si `cni` es canal/calico/cilium.

## Verificar

```bash
sudo systemctl status k3s
sudo k3s kubectl get nodes
```

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md)
- [K3s manual (legacy)](../../../docs/k3s/index.md)
