# k3s_cleanup_traefik

Elimina **restos de Traefik y svclb** en `kube-system` tras instalar K3s con
`--disable traefik` y `--disable servicelb`.

Evita conflictos con Ingress NGINX (MetalLB/GitOps en Fase 4).

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3.

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags traefik
```

## Hosts

`k3s_server` (deborah).

## Tags

`traefik`.

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.traefik_cleanup.enabled` | `true` | Activa el rol |

## Qué hace

1. Borra HelmCharts `traefik` y `traefik-crd` en `kube-system`.
2. Borra Service `traefik` residual.
3. Borra pods `svclb-traefik`.

## Verificar

```bash
sudo k3s kubectl get pods -n kube-system | grep -E 'traefik|svclb' || echo "limpio"
```

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md) (troubleshooting Traefik)
- [K3s manual](../../../docs/k3s/index.md)
