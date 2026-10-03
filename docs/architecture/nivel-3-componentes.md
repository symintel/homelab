# C4 Nivel 3 — Componentes

Zoom dentro de cada **contenedor** del [Nivel 2](overview.md#nivel-2-contenedores):
componentes internos, tecnologías y relaciones. Para el mapa físico de nodos,
continúa en **[Nivel 4 — Despliegue](nivel-4-despliegue.md)**.

Volver a [Overview (Nivel 1–2)](overview.md).

## 3.1 — K3s Management

Desglose del clúster bare-metal de control: GitOps (Argo CD), identidad (Dex),
provisioning CAPI/CAPN, red de servicios (MetalLB, Ingress), operadores de
storage (OpenEBS, Longhorn), secretos (Sealed Secrets), upgrades (SUC) y
vCluster Platform opcional.

Detalle operativo: [Stack tecnológico](../implementacion/stack-tecnologico.md),
[GitOps](../gitops/index.md).

```mermaid
---
title: Componentes — K3s Management (C4 Nivel 3)
config:
  flowchart:
    wrappingWidth: 280
---
flowchart LR
    operador(["<span style='color:#fff'><b>Operador HomeLab</b><br/><small>[Person]</small><br/>kubectl / ArgoCD UI</span>"])
    git["<span style='color:#fff'><b>Git remoto</b><br/><small>[Software System]</small><br/>symintel/gitops</span>"]

    subgraph k3s_mgmt["K3s Management"]
        direction LR
        argocd["<span style='color:#000'><b>Argo CD</b><br/><small>[Component: Helm]</small><br/>GitOps controller + server</span>"]
        dex["<span style='color:#000'><b>Dex</b><br/><small>[Component: OIDC]</small><br/>SSO ArgoCD / vCluster / Incus UI</span>"]
        subgraph apps["Applications de Argo CD"]
            direction TB
            sealed["<span style='color:#000'><b>Sealed Secrets</b><br/><small>[Component: controller]</small><br/>Descifra SealedSecret</span>"]
            metallb["<span style='color:#000'><b>MetalLB</b><br/><small>[Component: controller]</small><br/>LoadBalancer L2 en LAN</span>"]
            ingress["<span style='color:#000'><b>Ingress NGINX</b><br/><small>[Component: Helm]</small><br/>HTTP(S) hacia apps</span>"]
            openebs["<span style='color:#000'><b>OpenEBS</b><br/><small>[Component: Helm]</small><br/>LocalPV provisioner</span>"]
            longhorn["<span style='color:#000'><b>Longhorn</b><br/><small>[Component: Helm]</small><br/>Storage replicado v1</span>"]
            suc["<span style='color:#000'><b>SUC</b><br/><small>[Component: Helm]</small><br/>Upgrades K3s escalonados</span>"]
            vcluster["<span style='color:#000'><b>vCluster Platform</b><br/><small>[Component: Helm]</small><br/>Sync manual opcional</span>"]
        end
        capi["<span style='color:#000'><b>Cluster API</b><br/><small>[Component: controllers]</small><br/>Core CAPI controllers</span>"]
        capn["<span style='color:#000'><b>CAPN</b><br/><small>[Component: provider]</small><br/>Incus provider controller</span>"]
    end

    incus["<span style='color:#fff'><b>Incus Cluster</b><br/><small>[Container: Incus]</small><br/>Sustrato LXCMachine</span>"]

    operador -->|"Administra<br/><small>[HTTPS]</small>"| argocd
    operador -->|"Accede<br/><small>[HTTPS]</small>"| ingress
    git -->|"Sincroniza<br/><small>[GitOps]</small>"| argocd
    argocd -->|"Despliega config<br/><small>[Helm]</small>"| dex
    argocd -->|"Despliega<br/><small>[Application]</small>"| apps
    dex -.->|"Emite tokens<br/><small>[OIDC]</small>"| operador
    capi -->|"Orquesta<br/><small>[CAPI]</small>"| capn
    capn -->|"Provisiona<br/><small>[API REST]</small>"| incus

    classDef person fill:#08427B,stroke:#073B6F,color:#fff
    classDef system fill:#1168BD,stroke:#0B4884,color:#fff
    classDef container fill:#438DD5,stroke:#3C7FC0,color:#fff
    classDef component fill:#85BBF0,stroke:#78A8D8,color:#000
    classDef external fill:#999999,stroke:#8A8A8A,color:#fff
    class operador person
    class git external
    class incus container
    class argocd,dex,sealed,metallb,ingress,openebs,longhorn,suc,vcluster,capi,capn component
    style k3s_mgmt fill:none,stroke:#888,stroke-dasharray:6 4
    style apps fill:none,stroke:#aaa,stroke-dasharray:2 3
```

## 3.2 — Incus Cluster

Internals del clúster HA (alta disponibilidad) Incus en los 3 nodos físicos: quorum dqlite, daemon
por miembro, pool `local` (driver `dir`), cluster groups, scheduler manual en
`oliver`, UI (interfaz de usuario) nativa en invincible y OIDC (OpenID Connect) Dex (Fase 4).

Detalle: [Clúster Incus](../incus/cluster-setup.md).

```mermaid
---
title: Componentes — Incus Cluster (C4 Nivel 3)
config:
  flowchart:
    wrappingWidth: 280
---
flowchart TB
    operador(["<span style='color:#fff'><b>Operador HomeLab</b><br/><small>[Person]</small><br/>incus CLI / UI</span>"])
    k3s_mgmt["<span style='color:#fff'><b>K3s Management</b><br/><small>[Container: Kubernetes]</small><br/>CAPN provider</span>"]
    subgraph incus["Incus Cluster"]
        dqlite["<span style='color:#000'><b>dqlite</b><br/><small>[Component: DB cluster]</small><br/>Quorum 3 miembros</span>"]
        incusd["<span style='color:#000'><b>incusd</b><br/><small>[Component: daemon]</small><br/>API REST en cada nodo</span>"]
        storage_pool["<span style='color:#000'><b>Pool local</b><br/><small>[Component: dir driver]</small><br/>Pool local por miembro</span>"]
        groups["<span style='color:#000'><b>Cluster groups</b><br/><small>[Component: Incus]</small><br/>x86-nodes / arm64-nodes</span>"]
        scheduler["<span style='color:#000'><b>Scheduler</b><br/><small>[Component: Incus]</small><br/>oliver manual</span>"]
        incus_ui["<span style='color:#000'><b>Incus UI</b><br/><small>[Component: HTTPS :8443]</small><br/>Solo en invincible</span>"]
        oidc["<span style='color:#000'><b>OIDC config</b><br/><small>[Component: Dex]</small><br/>Fase 4 SSO</span>"]
    end

    operador -->|"Administra<br/><small>[HTTPS]</small>"| incus_ui
    operador -->|"CLI<br/><small>[incus]</small>"| incusd
    k3s_mgmt -->|"CAPN API<br/><small>[REST]</small>"| incusd
    incusd -->|"Persiste estado<br/><small>[dqlite]</small>"| dqlite
    incusd -->|"Monta volúmenes<br/><small>[dir]</small>"| storage_pool
    groups -->|"Dirige instancias<br/><small>[cluster group]</small>"| scheduler
    incus_ui -->|"Proxy UI<br/><small>[local socket]</small>"| incusd
    oidc -->|"SSO<br/><small>[OIDC]</small>"| incus_ui

    classDef person fill:#08427B,stroke:#073B6F,color:#fff
    classDef system fill:#1168BD,stroke:#0B4884,color:#fff
    classDef container fill:#438DD5,stroke:#3C7FC0,color:#fff
    classDef component fill:#85BBF0,stroke:#78A8D8,color:#000
    classDef external fill:#999999,stroke:#8A8A8A,color:#fff
    class operador person
    class k3s_mgmt container
    class dqlite,incusd,storage_pool,groups,scheduler,incus_ui,oidc component
    style incus fill:none,stroke:#888,stroke-dasharray:6 4
```

## 3.3 — Workload Clusters

Estructura interna de un clúster **kubeadm** efímero provisionado por CAPN (Cluster API Provider for Incus)
(ej. `demo`): LXCMachine en Incus, control plane, workers y CNI (Container Network Interface) Flannel del
workload. No es K3s (distribución ligera de Kubernetes) anidado.

Detalle: [CAPN](../capn/index.md), [Fase 6](../implementacion/fase-6-capn.md).

```mermaid
---
title: Componentes — Workload Clusters (C4 Nivel 3)
config:
  flowchart:
    wrappingWidth: 280
---
flowchart TB
    k3s["<span style='color:#fff'><b>K3s Management</b><br/><small>[Container: Kubernetes]</small><br/>CAPN + CAPI</span>"]

    subgraph workload["Workload Cluster CAPN &nbsp;[kubeadm]"]
        direction TB
        machines["<span style='color:#000'><b>LXCMachine</b><br/><small>[Component: CAPN]</small><br/>Infra en Incus</span>"]
        cp["<span style='color:#000'><b>Control plane</b><br/><small>[Component: kubeadm]</small><br/>API + etcd + scheduler</span>"]
        workers["<span style='color:#000'><b>Workers</b><br/><small>[Component: kubelet]</small><br/>Nodos worker</span>"]
        cni["<span style='color:#000'><b>CNI</b><br/><small>[Component: Flannel]</small><br/>Red del workload cluster</span>"]
    end

    subgraph infra[" "]
        direction LR
        storage["<span style='color:#fff'><b>Storage</b><br/><small>[Container: OpenEBS + Longhorn]</small><br/>PVC del management</span>"]
        incus["<span style='color:#fff'><b>Incus Cluster</b><br/><small>[Container: Incus]</small><br/>Aloja LXCMachine</span>"]
    end

    k3s -->|"Provisiona<br/><small>[CAPN]</small>"| machines
    cp -->|"Orquesta<br/><small>[Kubernetes]</small>"| workers
    workers -->|"Red de pods<br/><small>[CNI]</small>"| cni
    workers -.->|"PVC opcional<br/><small>[CSI]</small>"| storage
    machines -->|"Instancia<br/><small>[LXC/VM]</small>"| incus

    classDef person fill:#08427B,stroke:#073B6F,color:#fff
    classDef system fill:#1168BD,stroke:#0B4884,color:#fff
    classDef container fill:#438DD5,stroke:#3C7FC0,color:#fff
    classDef component fill:#85BBF0,stroke:#78A8D8,color:#000
    classDef external fill:#999999,stroke:#8A8A8A,color:#fff
    class k3s,incus,storage container
    class machines,cp,workers,cni component
    style workload fill:none,stroke:#888,stroke-dasharray:6 4
    style infra fill:none,stroke:none
```

## 3.4 — Storage

Componentes lógicos del tier híbrido **OpenEBS LocalPV** (default, 3 nodos) +
**Longhorn v1** (réplica cross-arch entre `invincible` y `deborah`). Los pods
corren en K3s; aquí se modelan como contenedor L2 (capa 2 del modelo OSI) separado por claridad.

Detalle: [Storage](../storage/index.md).

```mermaid
---
title: Componentes — Storage (C4 Nivel 3)
config:
  flowchart:
    wrappingWidth: 280
---
flowchart TB
    workload["<span style='color:#fff'><b>Workload Clusters</b><br/><small>[Container: kubeadm]</small><br/>Pods con PVC</span>"]
    k3s_mgmt["<span style='color:#fff'><b>K3s Management</b><br/><small>[Container: Kubernetes]</small><br/>Pods del management</span>"]
    subgraph storage["Storage tier"]
        sc["<span style='color:#000'><b>StorageClasses</b><br/><small>[Component: GitOps]</small><br/>openebs-hostpath + longhorn-mixto</span>"]
        openebs_prov["<span style='color:#000'><b>OpenEBS LocalPV</b><br/><small>[Component: DaemonSet]</small><br/>Default 3 nodos</span>"]
        longhorn_mgr["<span style='color:#000'><b>Longhorn manager</b><br/><small>[Component: Deployment]</small><br/>Control de volúmenes</span>"]
        longhorn_eng["<span style='color:#000'><b>Longhorn engine</b><br/><small>[Component: DaemonSet]</small><br/>Réplicas v1 cross-arch</span>"]
        csi["<span style='color:#000'><b>CSI drivers</b><br/><small>[Component: CSI]</small><br/>OpenEBS + Longhorn</span>"]
    end

    k3s_mgmt -->|"Aplica<br/><small>[homelab-storage]</small>"| sc
    workload -->|"Monta PVC<br/><small>[CSI]</small>"| csi
    k3s_mgmt -->|"Monta PVC<br/><small>[CSI]</small>"| csi
    csi -->|"LocalPV<br/><small>[openebs-hostpath]</small>"| openebs_prov
    csi -->|"Réplica HA<br/><small>[longhorn-mixto]</small>"| longhorn_eng
    longhorn_mgr -->|"Gestiona<br/><small>[Longhorn API]</small>"| longhorn_eng

    classDef person fill:#08427B,stroke:#073B6F,color:#fff
    classDef system fill:#1168BD,stroke:#0B4884,color:#fff
    classDef container fill:#438DD5,stroke:#3C7FC0,color:#fff
    classDef component fill:#85BBF0,stroke:#78A8D8,color:#000
    classDef external fill:#999999,stroke:#8A8A8A,color:#fff
    class workload,k3s_mgmt container
    class sc,openebs_prov,longhorn_mgr,longhorn_eng,csi component
    style storage fill:none,stroke:#888,stroke-dasharray:6 4
```

## 3.5 — Cinc Lab

Sandbox de aprendizaje **Cinc/Chef** en VMs (máquinas virtuales) Incus (Ubuntu 24.04), una en
`@x86-nodes` y otra en `@arm64-nodes`. No es pieza de producción del HomeLab.

Detalle: [Lab Cinc/Chef](../labs/cinc/index.md).

```mermaid
---
title: Componentes — Cinc Lab (C4 Nivel 3)
config:
  flowchart:
    wrappingWidth: 280
---
flowchart TB
    operador(["<span style='color:#fff'><b>Operador HomeLab</b><br/><small>[Person]</small><br/>incus / chef</span>"])
    incus["<span style='color:#fff'><b>Incus Cluster</b><br/><small>[Container: Incus]</small><br/>Aloja VMs lab</span>"]
    omnitruck["<span style='color:#fff'><b>Omnitruck</b><br/><small>[Software System]</small><br/>Paquetes cinc-client</span>"]

    subgraph cinclab["Cinc Lab"]
        direction TB
        subgraph vms["VMs del lab"]
            direction LR
            vm_x86["<span style='color:#000'><b>cinc-lab-x86</b><br/><small>[Component: Incus VM]</small><br/>Ubuntu 24.04 @x86-nodes</span>"]
            vm_arm["<span style='color:#000'><b>cinc-lab-arm</b><br/><small>[Component: Incus VM]</small><br/>Ubuntu 24.04 @arm64-nodes</span>"]
        end
        cinc_client["<span style='color:#000'><b>cinc-client</b><br/><small>[Component: deb]</small><br/>Agente Cinc/Chef</span>"]
        cookbooks["<span style='color:#000'><b>Cookbooks</b><br/><small>[Component: Git local]</small><br/>cinc-lab/cookbooks</span>"]
    end

    operador -->|"SSH / chef<br/><small>[lab]</small>"| vms
    incus -->|"Aloja<br/><small>[VM]</small>"| vms
    omnitruck -->|"Instala<br/><small>[HTTPS]</small>"| cinc_client
    cookbooks -->|"Converge<br/><small>[chef-client]</small>"| cinc_client

    classDef person fill:#08427B,stroke:#073B6F,color:#fff
    classDef system fill:#1168BD,stroke:#0B4884,color:#fff
    classDef container fill:#438DD5,stroke:#3C7FC0,color:#fff
    classDef component fill:#85BBF0,stroke:#78A8D8,color:#000
    classDef external fill:#999999,stroke:#8A8A8A,color:#fff
    class operador person
    class omnitruck external
    class incus container
    class cookbooks,cinc_client,vm_x86,vm_arm component
    style cinclab fill:none,stroke:#888,stroke-dasharray:6 4
    style vms fill:none,stroke:#aaa,stroke-dasharray:2 3
```


## Siguiente

**[→ Nivel 4 — Despliegue](nivel-4-despliegue.md)** — mapa físico de los 3 nodos.
