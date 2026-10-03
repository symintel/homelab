# k3s_node_labels

Aplica **etiquetas de nodos Kubernetes** desde `host_vars` de cada máquina.
Útil para Longhorn, tier de carga y arquitectura (x86/ARM64).

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3.

Con `k3s_install.node_labels.enabled: true` en
[`group_vars/incus_cluster/k3s_install.yml`](../../group_vars/incus_cluster/k3s_install.yml)
(no con `-e`: Ansible no fusiona claves con puntos en un diccionario):

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags labels
```

## Hosts

`k3s_server` (ejecuta `kubectl label` contra todos los nodos del inventario).

## Tags

`labels`.

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.node_labels.enabled` | `false` | Activa el rol |
| `k3s_install.node_labels.at_join` | `false` | Si true, labels en join (rol `k3s_agent`) |
| `k3s_node_labels` | `{}` | Mapa `clave: valor` por host en `host_vars/` |

Ejemplo [`host_vars/deborah.yml`](../../host_vars/deborah.yml):

```yaml
k3s_node_labels:
  workload-tier: heavy
  kubernetes.io/arch: arm64
  node.longhorn.io/create-default-disk: "true"
```

## Qué hace

1. Recorre `groups['incus_cluster']` y lee `k3s_node_labels` de cada `host_vars`.
2. Ejecuta `k3s kubectl label node <nodo> <key>=<value> --overwrite`.

## Verificar

```bash
sudo k3s kubectl get nodes --show-labels
```

## Documentación

- [Opciones del playbook](../../../docs/k3s/playbook-options.md)
- [GitOps — Longhorn pending](../../../docs/gitops/index.md)
