# HomeLab — K3s + Incus + CAPN

<span class="tag tag-status">En construcción activa</span>

Clúster Kubernetes híbrido (x86_64 + ARM64) construido sobre Incus, con
Cluster API (CAPN) para provisionar clusters efímeros bajo demanda.

## Hardware

| Nodo | Modelo | CPU | RAM (medida) | IP (`br0`) | Rol |
|---|---|---|---|---|---|
| `invincible` | Lenovo M920q | i3-6100T x86_64 | 7.6 GB | 192.168.20.6 | Incus leader · K3s worker |
| `oliver` | Lenovo M700 | i7-8700T x86_64 | 15.5 GB | 192.168.20.7 | Incus quorum · K3s worker |
| `deborah` | Orange Pi 5 Plus | RK3588 ARM64 | 31 GB | 192.168.20.5 | K3s control-plane · Incus arm64 |

Detalle medido y presupuesto RAM: [Inventario de hardware](hardware/inventory.md).

> Hostnames de la serie *Invincible* — ver
> [personajes](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).

## Empieza por acá

**Guía principal — implementación paso a paso:**

- **[Implementación — visión general](implementacion/index.md)** — Fases 0→6, timeline, forks.
- **[Stack tecnológico](implementacion/stack-tecnologico.md)** — diagrama por capas + productos.

Contexto y profundización:

- [Arquitectura (C4 Nivel 1–4)](architecture/overview.md) · [Componentes](architecture/nivel-3-componentes.md) · [Despliegue](architecture/nivel-4-despliegue.md)
- [Inventario de hardware](hardware/inventory.md)
- [Catálogo GitOps](gitops/index.md) · [Storage](storage/index.md) · [Secretos](secrets/index.md)
- [Lab Cinc/Chef](labs/cinc/index.md)

!!! note "Repositorio"
    El código (Ansible, OpenTofu, manifiestos de Kubernetes) vive en el mismo
    repo, fuera de `docs/`. Este sitio es la documentación humana; el repo
    completo es la fuente ejecutable.
