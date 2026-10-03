# Discovery de hardware (Ansible)

Playbook que escanea los 3 nodos y genera una ficha Markdown por nodo, para
confirmar (o contradecir) con datos medidos los roles asignados en el
[Inventario de hardware](inventory.md) — en particular, si `deborah`
sigue siendo el mejor candidato a control-plane K3s (distribución ligera de Kubernetes).

Código: [`ansible/playbook-discovery.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-discovery.yml)
(dos plays en un mismo archivo: escaneo por nodo + consolidado).

## Uso

```bash
cd ansible/
ansible-playbook -i inventory.ini playbook-discovery.yml
```

El segundo play (consolidado) lee los facts recolectados por el primero
desde `hostvars`, que solo están disponibles en memoria durante la misma
invocación de `ansible-playbook` -- por eso viven en el mismo archivo en
vez de en un playbook aparte que habría que recordar pasar junto al otro.

## Qué recolecta por nodo

- **CPU** — arquitectura, modelo, núcleos físicos/lógicos.
- **Memoria** — RAM total y swap.
- **Almacenamiento** — cada disco (rotacional o no, tamaño, modelo) +
  benchmark de escritura 4k (`fio`, o `dd` como fallback) para estimar
  aptitud para etcd.
- **Red** — interfaces con su velocidad negociada.
- **Sistema operativo** — distro, kernel, uptime, temperatura (sensor
  `vcgencmd` en SBC o `thermal_zone0` genérico).
- **Stack instalado** — si `/dev/kvm` está disponible, versión de Incus y
  de K3s.
- **Paquetes clave** — versión (o "no instalado") de docker, containerd,
  python3, git, qemu-img, virsh.
- **Instancias Incus** — nombre/tipo/estado de cada container o VM (máquina virtual).
- **K3s** — `kubectl get nodes` y `get pods -A` (si el nodo tiene acceso al
  API server).
- **Contenedores sueltos** — `crictl ps -a` / `docker ps -a`, para detectar
  drift fuera de K3s/Incus.
- **Servicios systemd** — estado active/enabled de k3s, k3s-agent, incus,
  docker, containerd.
- **Puertos en escucha** (`ss -tlnp`), **uso de disco por filesystem**
  (`df -h`), **módulos de kernel** (overlay/br_netfilter/veth) y **estado
  de firewall** (ufw o nftables, el que exista).

## Salida

```
ansible/reports/            (gitignored -- datos de un escaneo en vivo)
├── invincible.md
├── oliver.md
├── deborah.md
└── summary.md
```

`summary.md` pone los 3 nodos lado a lado y lista los 4 criterios usados
para decidir el rol de control-plane:

1. Menor latencia de escritura (fsync) — el factor decisivo para etcd.
2. Fuente de alimentación estable (NVMe + alimentación dedicada, no USB).
3. Margen de RAM por encima del uso normal del clúster (no es el factor
   decisivo por sí solo).
4. Temperatura bajo carga sostenida — throttling térmico en una SBC (Single Board Computer).

Si algún resultado contradice el rol asignado en
[Inventario de hardware](inventory.md), ese documento es el que se
actualiza — los reportes de `ansible/reports/` no se versionan.
