# Esquema de partición recomendado — VMs de workload (CAPN)

Convención para las VMs/LXCMachine que CAPN (Cluster API Provider Incus) provisione como clústeres de
workload (ej. `demo`, ver `docs/architecture/nivel-3-componentes.md` §3.3). No hay ninguna VM (máquina virtual) corriendo
todavía — esto es una plantilla a seguir cuando se cree la primera, no un estado medido.

**Origen:** derivado de la revisión real de partición de los 3 nodos bare-metal del clúster de management
(ver `ansible/reports/<host>.md`, sección "Recomendaciones — esquema de partición del SO"), que encontró:
ningún nodo tiene `/var` separado del `/` del sistema, y el swap está dimensionado sin fórmula consistente
entre nodos (13%–94% de diferencia contra `min(RAM/2, 8GB)`). Este documento fija la convención que los
nodos bare-metal no pueden adoptar en vivo sin riesgo (repartición de una raíz montada), pero que sí se
puede aplicar limpio en una VM nueva desde el primer boot.

## Esquema

| Partición | Tamaño | Filesystem | Notas |
|---|---|---|---|
| `/boot` (o `/boot/efi` si UEFI) | 1 GB | vfat/ext4 | Igual que los 3 nodos bare-metal actuales |
| swap | `min(RAM/2, 8GB)` | swap | Fórmula fija — evita la inconsistencia encontrada en los nodos actuales |
| `/var` | ≥20% del disco, o 20GB mínimo | ext4 | Separado de `/` — aísla logs/imágenes de containerd y volúmenes locales de un runaway que llenaría la raíz |
| `/` | Resto del disco | ext4 | Sistema base |

## Por qué separar `/var`

Los workloads de K3s (containerd, logs, cache de imágenes, `local-path-provisioner`/OpenEBS si aplica
dentro de la VM) escriben todos bajo `/var`. Sin partición separada, un runaway ahí puede llenar `/` y
tumbar el nodo entero (no solo el workload). Ningún nodo bare-metal actual tiene esto separado —
diferencia intencional: en bare-metal ya instalado, separar `/var` requiere reinstalar; en una VM nueva
provisionada por CAPN (Cluster API Provider for Incus), es gratis definirlo en el template desde el día 1.

## Aplicación

Este esquema se aplica en la imagen/template base que CAPN use para provisionar VMs (máquinas virtuales), no vía Ansible
post-instalación — fuera de alcance de este repo hasta que exista un template de imagen real que editar.
