# k3s_cni

Instala el **CNI externo** tras el server K3s cuando `k3s_install.core.cni` no es
`flannel`. Requiere server con `--flannel-backend=none` y `--disable-network-policy`.

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — después del server, antes de agents. Tag `cni`.

## Hosts

`k3s_server` (control-plane).

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.core.cni` | `flannel` | `flannel`, `canal`, `calico`, `cilium` |
| `k3s_install.core.cluster_cidr` | `10.42.0.0/16` | Pool Calico en template |
| `k3s_cni_calico_version` | `v3.29.1` | Manifests Calico/Canal |
| `k3s_cni_cilium_version` | `v1.16.5` | Manifest Cilium quick-install |

## Qué hace

1. Salta si `cni == flannel` (Flannel embebido en K3s).
2. **Canal**: manifest oficial Calico/Canal.
3. **Calico**: Tigera operator + `custom-resources` con pod CIDR.
4. **Cilium**: quick-install manifest.
5. Espera pods Ready en `kube-system`.

Alternativa GitOps: Applications `calico-operator`, `calico-config`, `canal`, `cilium`
(sync manual) en [`gitops`](https://github.com/symintel/gitops/tree/main/argocd/apps).

## Verificar

```bash
k3s kubectl get pods -n calico-system -l k8s-app=calico-node   # calico (Tigera operator)
k3s kubectl get pods -n kube-system -l k8s-app=canal           # canal
k3s kubectl get pods -n kube-system -l k8s-app=cilium          # cilium
k3s kubectl get tigerastatus                                    # solo calico
```

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md)
- [playbook-options — CNI](../../../docs/k3s/playbook-options.md#cni)
- [K3s networking](https://docs.k3s.io/networking/basic-network-options)
