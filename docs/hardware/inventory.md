# Inventario de Hardware

> Los hostnames siguen la serie *Invincible* — ver
> [categoría de personajes](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).
> `deborah` fue antes `orangepi5plus`.

Datos **medidos** con [`playbook-discovery.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-discovery.yml)
(2026-07-10). Donde el valor nominal difiere del medido, la columna *Medido*
es la fuente de verdad para planificación.

<div class="option-grid">
  <div class="card">
    <div class="card-title"><code>invincible</code> <span class="tag tag-neutral">x86_64</span></div>
    <div class="text-muted">Lenovo M920q · i3-6100T 2c/4t</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">7.6 GB</span></div>
    <div class="card-body">IP actual: 192.168.23.162 · IP estática: <span class="card-highlight">192.168.20.6</span></div>
    <div class="card-meta">Incus: Bootstrap / leader (pendiente) · K3s: Worker (agent)</div>
  </div>
  <div class="card">
    <div class="card-title"><code>oliver</code> <span class="tag tag-neutral">x86_64</span></div>
    <div class="text-muted">Lenovo M700 · i7-8700T 6c/12t</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">15.5 GB</span></div>
    <div class="card-body">IP actual: 192.168.20.87 · IP estática: <span class="card-highlight">192.168.20.7</span></div>
    <div class="card-meta">Incus: Miembro (scheduler manual) · K3s: Worker (agent)</div>
  </div>
  <div class="card">
    <div class="card-title"><code>deborah</code> <span class="tag tag-accent">ARM64</span></div>
    <div class="text-muted">Orange Pi 5 Plus · RK3588 8c</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">31.0 GB</span></div>
    <div class="card-body">IP actual: 192.168.21.211 · IP estática: <span class="card-highlight">192.168.20.5</span></div>
    <div class="card-meta">Incus: Miembro (grupo arm64) · K3s: Control-plane (server)</div>
  </div>
</div>

!!! note "Specs nominales vs medidas"
    La documentación anterior intercambiaba RAM entre invincible (16 GB nominal → **7.6 GB** medidos) y oliver (8 GB nominal → **15.5 GB** medidos). Actualizar cualquier presupuesto que use los valores viejos.

## Esquema de IPs

| Concepto | invincible | oliver | deborah |
|---|---|---|---|
| IP SSH hoy (`ansible_host`) | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` |
| IP estática en `br0` | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` |
| Interfaz física → bridge | `eno2` | `eno1` | `enP4p65s0` |

Tras `playbook-set-static-ip.yml`, actualizar `ansible_host` en
[`inventory.ini`](https://github.com/symintel/homelab/blob/main/ansible/inventory.ini)
si la IP de conexión cambió.

## Almacenamiento e I/O (discovery 2026-07-10)

| Nodo | Disco principal | Escritura 4k (dd/fio) |
|---|---|---|
| invincible | TECLAST 120GB SSD | 85.5 MB/s |
| oliver | Kingston SA400 224GB | **1.8 GB/s** |
| deborah | mmcblk0 boot + NVMe WDC 250GB (`nvme0n1`) | pendiente (benchmark en `/srv` o NVMe) |

## Presupuesto de RAM (recalculado)

- **invincible (7.6 GB)**: K3s (distribución ligera de Kubernetes) agent + ArgoCD controller + futuro Incus leader. RAM ajustada — evitar CAPN (Cluster API Provider for Incus) management + Longhorn simultáneos sin límites de pods.
- **oliver (15.5 GB)**: K3s agent (CoreDNS, metrics-server) + Incus en `scheduler.instance manual`. Más margen del documentado; I/O superior a invincible.
- **deborah (31 GB)**: control-plane K3s + BIND (rol `bind_dns`). Root en eMMC; NVMe (disco SSD por PCIe) disponible para datos/etcd.

## Decisión: control-plane en deborah

**Estado:** el API (Application Programming Interface) server responde en `192.168.20.5:6443` (deborah).
Workers en invincible (`192.168.20.6`) y oliver (`192.168.20.7`). Se instala con
**K3s v1.36.2+k3s1** (`k3s_install.core.version`); después el SUC (System Upgrade Controller) lo actualiza solo
([Actualizar K3s](../operacion/actualizar-k3s.md)). Versión real: `kubectl get nodes`.

<div class="card">
  <div class="card-kicker">Análisis de trade-offs</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">A: deborah <span class="tag tag-accent">elegida</span></div>
      <div class="text-muted">31 GB RAM, ARM64, NVMe disponible</div>
      <div class="text-muted">SBC; throttling térmico; servicios extra en el mismo nodo</div>
    </div>
    <div class="card-col">
      <div class="card-title">B: oliver</div>
      <div class="text-muted">I/O 1.8 GB/s; 15.5 GB RAM; i7-8700T</div>
      <div class="text-muted">Reservado quorum Incus; migración CP costosa</div>
    </div>
    <div class="card-col">
      <div class="card-title">C: invincible</div>
      <div class="text-muted">Ya corre ArgoCD controller</div>
      <div class="text-muted">Solo 7.6 GB RAM; I/O lento</div>
    </div>
  </div>
</div>

**Pendiente:** ejecutar `fio` en deborah sobre NVMe (`/srv` o partición dedicada) para validar latencia fsync antes de considerar migración a oliver.

!!! warning "deborah tras reboot"
    El discovery detectó el binario k3s pero sin servicio `k3s` activo ni puerto `:6443` en un escaneo con uptime ~2.6 h. Verificar `systemctl enable --now k3s` y logs si el CP (control plane) no responde.

## Ver también

- [Discovery de hardware (Ansible)](discovery.md)
- [K3s — instalación y despliegue](../k3s/index.md)
