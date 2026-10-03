# k3s_os_hardening

Configura **`unattended-upgrades`** en todos los nodos: parches de seguridad
automáticos con reinicio escalonado por host.

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3 (opcional).

Con `k3s_install.os_hardening.enabled: true` en
[`group_vars/incus_cluster/k3s_install.yml`](../../group_vars/incus_cluster/k3s_install.yml)
(no con `-e`: Ansible no fusiona claves con puntos en un diccionario):

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags hardening
```

## Hosts

`incus_cluster` (los 3 nodos).

## Tags

`hardening`.

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.os_hardening.enabled` | `false` | Activa el rol |
| `k3s_install.os_hardening.reboot_schedule` | por host | Hora de reinicio automático |

Default en [`group_vars/incus_cluster/k3s_install.yml`](../../group_vars/incus_cluster/k3s_install.yml):

```yaml
reboot_schedule:
  deborah: "04:00"
  invincible: "04:20"
  oliver: "04:40"
```

## Qué hace

1. Instala `unattended-upgrades`.
2. Habilita actualización diaria de listas y upgrades automáticos.
3. Restringe a origen `-security` únicamente.
4. Programa `Automatic-Reboot` por nodo.

## Verificar

```bash
cat /etc/apt/apt.conf.d/50unattended-upgrades
systemctl is-enabled unattended-upgrades
```

## Documentación

- [Opciones del playbook](../../../docs/k3s/playbook-options.md)
