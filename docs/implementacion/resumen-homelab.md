# Resumen del HomeLab

Cierre de la [guía de implementación](index.md): checklist de lo desplegado,
URLs, `/etc/hosts`, nodos, secretos y verificación global. Consulta esta página
al terminar la Fase 4 como mínimo; las fases 5 y 6 son opcionales.

## Recorrido completado (por fase)

| Fase | Qué quedó listo | Herramienta |
|---|---|---|
| [0 — Preparación](fase-0-preparacion.md) | Repo, Ansible, `inventory.ini`, discovery opcional | `playbook-discovery.yml` |
| [1 — Red](fase-1-red.md) | IP fija en `br0` (`192.168.20.5`, `.6`, `.7`) | `playbook-set-static-ip.yml` |
| [2 — Incus](fase-2-incus.md) | Clúster HA, groups, UI, storage `dir` | `playbook-bootstrap.yml` + `playbook-incus-cluster.yml` |
| [3 — K3s](fase-3-k3s.md) | Management cluster + ArgoCD controller; CNI **Flannel** (default) | `playbook-k3s.yml` |
| [4 — GitOps](fase-4-gitops.md) | MetalLB, Gateway API, storage, Dex/GitHub SSO | Argo CD + `playbook-dex-oauth-secrets.yml` |
| [5 — vCluster](fase-5-vcluster.md) *(opc.)* | Platform, kubeconfig web (connected cluster) | Application ArgoCD |
| [6 — CAPN](fase-6-capn.md) *(opc.)* | Workload clusters sobre Incus | `clusterctl` + `capn-demo.yaml` |

## URLs y accesos web

| Servicio | URL | Auth | Fase |
|---|---|---|---|
| **ArgoCD** | `https://argocd.homelab.local` | SSO GitHub vía Dex | 4 |
| **Dex** (issuer) | `https://argocd.homelab.local/api/dex` | — | 4 |
| **vCluster Platform** | `https://vcluster.homelab.local` | SSO Dex → GitHub | 5 |
| **Incus UI** | `https://incus.homelab.local:8443` | SSO Dex (o cert cliente antes Fase 4) | 2 / 4 |
| **K3s API** | `https://192.168.20.5:6443` | kubeconfig | 3 |

### Kubeconfig

| Clúster | Cómo obtenerlo |
|---|---|
| Management K3s | vCluster Platform (connected cluster) o `playbook-k3s.yml` con `fetch_kubeconfig` |
| vClusters | UI [vCluster Platform](fase-5-vcluster.md) |
| Workload CAPN | `clusterctl get kubeconfig` (Fase 6) |

## `/etc/hosts` en tu estación de trabajo

Bloque completo tras Fase 4+ (`<IP-del-Gateway>` = IP que MetalLB le da al
Gateway `homelab`; `incus` siempre apunta a invincible):

```
<IP-del-Gateway>  argocd.homelab.local vcluster.homelab.local
192.168.20.6      incus.homelab.local
```

Obtén `<IP-del-Gateway>`:

```bash
kubectl get gateway homelab -n gateway -o jsonpath='{.status.addresses[0].value}'
```

Verificación:

```bash
curl -kI https://argocd.homelab.local
curl -kI https://vcluster.homelab.local
curl -kI https://incus.homelab.local:8443
```

## Nodos del HomeLab

| Hostname | IP `br0` | Incus | K3s | Notas |
|---|---|---|---|---|
| invincible | 192.168.20.6 | Leader + UI | agent | RAM ajustada; Longhorn disk |
| oliver | 192.168.20.7 | Quorum, scheduler manual | agent | Sin instancias automáticas |
| deborah | 192.168.20.5 | arm64-nodes | **server** (CP) | 31 GB RAM |

Storage Incus: pool `local`, driver `dir`, perfil `default` → NIC (tarjeta de red) `br0`.

Detalle hardware: [Inventario](../hardware/inventory.md).

## Red del clúster (CNI)

| Decisión | Default HomeLab | Alternativa |
|---|---|---|
| CNI | **Flannel** `vxlan` (embebido en K3s) | Canal, Calico o Cilium vía rol `k3s_cni` o apps GitOps manuales |

Variable Ansible: `k3s_install.core.cni` en [`group_vars/incus_cluster/k3s_install.yml`](https://github.com/symintel/homelab/blob/main/ansible/group_vars/incus_cluster/k3s_install.yml).
Detalle y trade-offs: [Fase 3 — CNI](fase-3-k3s.md#cni) · [playbook-options](../k3s/playbook-options.md#cni).

Verificación:

```bash
kubectl get pods -n kube-system -l k8s-app=flannel
# o calico-node / canal / cilium según el CNI elegido
```

## Secretos y SSO (1Password)

| Campo 1Password | Uso |
|---|---|
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | Dex → GitHub OAuth (manual en GitHub + 1Password) |
| `VCLUSTER_CLIENT_SECRET` | Dex + Helm Platform (Ansible genera si falta) |
| `INCUS_CLIENT_SECRET` | Dex + `incus config set oidc.*` (Ansible genera si falta) |

Cuenta **Personal**, bóveda **`HomeLab`** (configurable vía env vars).
Playbook: `playbook-dex-oauth-secrets.yml`.

!!! important "Permisos por defecto"
    Usuarios SSO (inicio de sesión único) **no ven nada** hasta asignar acceso en vCluster Platform o
    `incus auth`. Ver [Fase 4](fase-4-gitops.md) y [Fase 5](fase-5-vcluster.md).

Documentación: [Secretos OAuth](https://github.com/symintel/gitops/blob/main/argocd/secrets/1password.md)

## GitOps (Argo CD)

Apps típicas en `Healthy` tras Fase 4:

- `argocd`, `argocd-route`, `metallb`, `homelab-storage`, `kong`, …
- Opcionales (sync manual): `vcluster-platform`, `capn-demo`
- CNI (solo si no usas Flannel embebido): `calico-operator` + `calico-config`, `canal` o `cilium` — **una** a la vez

Repo: [`gitops`](https://github.com/symintel/gitops) · [`bootstrap/root-appset.yaml`](https://github.com/symintel/gitops/blob/main/bootstrap/root-appset.yaml)

## Verificación global

```bash
# Incus
incus cluster list
incus cluster group list

# K3s
kubectl get nodes
kubectl get applications -n argocd

# SSO — login GitHub en ArgoCD, vCluster e Incus UI

# CAPN (si Fase 6)
kubectl get clusters,machines
```

## Enlaces oficiales del stack

- [Incus](https://linuxcontainers.org/incus/docs/main/) · [K3s](https://docs.k3s.io/) · [Argo CD](https://argo-cd.readthedocs.io/)
- [vCluster Platform](https://www.vcluster.com/docs/platform/) · [Cluster API](https://cluster-api.sigs.k8s.io/) · [CAPN](https://capn.linuxcontainers.org/)
- [1Password SDK](https://github.com/1Password/onepassword-sdk-python)

## Mantenimiento y profundización

- [Stack tecnológico](stack-tecnologico.md)
- [Catálogo Ansible](../ansible/index.md)
- [GitOps](../gitops/index.md)
- [Backup Incus (opcional)](../incus/cluster-setup.md#backup-y-snapshots-opcional)
- [Desinstalar K3s](apendice-desinstalar.md)
