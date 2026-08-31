---
title: Requisitos mínimos
sidebar_position: 2
---

# Requisitos mínimos por componente

El [inventario](../hardware/inventario.md) de esta guía es el hardware real del autor (Dell OptiPlex 7060 Micro, Raspberry Pi 3/Zero W, rack GeeekPi, DVR Dahua). **No es una lista de compras.** Esta página separa lo que cada pieza de la arquitectura de O.S.C.A.R. necesita realmente, para que puedas dimensionar tu propio hardware — sea un mini PC de otra marca, un servidor de segunda mano o algo más grande — sin copiar SKUs específicos.

Los números son pisos técnicos razonables para un homelab de un solo operador, no benchmarks de producción. "Mínimo" significa que funciona de forma estable a esta escala, no que sea cómodo crecer mucho más allá sin tocar recursos.

## Host de virtualización (Proxmox u otro hypervisor)

| Recurso | Mínimo viable | Nota |
|---|---|---|
| CPU | 4 hilos, con VT-x/AMD-V | Sin virtualización asistida por hardware, ni arranca. |
| RAM | 16 GB | Con menos, apenas alcanza para 1-2 VMs livianas — no hay margen para el resto de esta guía. |
| Disco de sistema/VMs | 1 disco SSD/NVMe ≥250 GB | HDD mecánico funciona pero castiga la latencia de todas las VMs a la vez; evitarlo si es posible. |
| Red | 1 NIC gigabit | Segunda NIC es conveniente (separar management de tráfico), no obligatoria para empezar. |

Con 16 GB reales, contar con que Proxmox reserva ~2 GB y que el resto se reparte entre pocas VMs — ver la distribución de referencia en [Dell OptiPlex 7060](../hardware/dell-7060.md#distribución-inicial-orientativa), que aplica igual a cualquier host con esta RAM.

## Por VM/rol (sobre el hypervisor de arriba)

| Rol | vCPU mínimo | RAM mínima | Disco mínimo | Notas |
|---|---:|---:|---:|---|
| Docker Core (n8n, Uptime Kuma, dashboards livianos) | 2 | 2 GB | 40 GB | Crece rápido si se suman más contenedores; 4 GB es más realista apenas se agrega Postgres. |
| DevOps (Nexus + Git + runner) | 2 | 4 GB | 80 GB+ | Nexus solo ya quiere ~2 GB de heap; el disco depende de cuántos artefactos se alojan, no solo se proxean. |
| Nodo k3s (single-node) | 1 | 1 GB | 20 GB | Piso técnico de k3s; en la práctica, 2 vCPU / 2-4 GB es lo mínimo para correr algo más que pods de prueba sin OOM. |
| Observabilidad (Prometheus + Grafana + Loki) | 2 | 2 GB | 20 GB + crecimiento | El disco crece con retención/cardinalidad — ver [datos grandes](../proxmox/storage.md#datos-grandes). Con menos de 16 GB de RAM total en el host, conviene meter esto dentro de la VM Docker Core en vez de separarlo (ver nota de RAM abajo). |

**Sobre RAM total y cuándo separar servicios en su propia VM:** con 16 GB en el host, sumar 3-4 VMs con los mínimos de arriba ya deja poco margen — la recomendación es meter observabilidad dentro de la misma VM que Docker Core hasta tener más RAM disponible, no forzar una VM dedicada para cada función. Separar servicios en VMs propias es un lujo de RAM, no un requisito de arquitectura.

## Raspberry Pi (o equivalente ARM/SBC) por rol

| Rol | Mínimo viable | Notas |
|---|---|---|
| DNS secundario / Pi-hole | Pi Zero W o equivalente | Carga trivial, corre bien en el SBC más chico disponible. |
| Nodo de telemetría/sensor (MQTT) | Pi Zero W o equivalente | Igual que arriba. |
| Home Assistant | Pi 4 (2 GB+) o Pi 5 | Con muchas integraciones/automatizaciones se nota la diferencia; un Pi Zero/Pi 3 sirve para probar, no para uso diario cómodo. |

No hace falta un Pi 5 desde el día uno: cualquier SBC con Linux y red sirve para DNS/telemetría. La recomendación de Pi 4/5 aplica específicamente a Home Assistant si se le suman integraciones.

## Storage

- **Disco de VMs**: al menos 1 SSD/NVMe. Un solo disco sin redundancia es aceptable para empezar (ver [storage de Proxmox](../proxmox/storage.md)) siempre que exista backup real fuera de ese disco — la redundancia RAID no sustituye al backup.
- **Destino de backup**: **no es opcional a partir del momento en que existe una sola base de datos o configuración que no se puede recrear** (Postgres, Home Assistant, claves de cifrado). El mínimo viable es un segundo medio físico distinto al disco activo; el objetivo real es una copia fuera del sitio (ver [estrategia 3-2-1](../backup-dr/estrategia-321.md)). No hace falta NAS para empezar — alcanza con un segundo disco y, apenas sea posible, una cuenta de object storage barata (Backblaze B2 o similar) para la copia off-site.

## Red

| Pieza | Mínimo viable | Objetivo (no bloqueante) |
|---|---|---|
| Switch | Cualquier switch gigabit con suficientes puertos para los equipos actuales | Gestionable con VLAN 802.1Q — ver [VLAN y segmentación](../red/vlans.md) |
| Router/firewall | El router ISP o uno de consumo | Firewall dedicado (OPNsense u otro) — target state, no bloquea nada de lo anterior |
| Cableado | Cat5e/Cat6 según distancia | — |

Un switch no gestionado alcanza para arrancar Proxmox, VMs y Docker. VLAN/segmentación es una mejora de seguridad, no un prerequisito técnico — se agrega cuando el resto ya funciona (ver [migración a red segmentada](../red/migracion-a-red-segmentada.md)).

## Energía

Un UPS **no es un lujo** a partir del momento en que hay algo escribiendo en disco de forma continua (bases de datos, blobstores, el propio filesystem del hypervisor): un corte sin autonomía es un apagado sucio, con riesgo real de corrupción. El mínimo viable es un UPS line-interactive con capacidad (VA) suficiente para cubrir el consumo del host + switch + router el tiempo necesario para un apagado limpio (minutos, no horas) — no hace falta autonomía extendida, hace falta autonomía *predecible* y, idealmente, monitoreada (NUT u otro software de gestión) para que el apagado limpio pueda automatizarse en vez de depender de que alguien esté mirando.

## Resumen

Si tuvieras que arrancar O.S.C.A.R. con el hardware más chico posible que siga siendo *realmente* utilizable (no solo "bootea"): un mini PC con 16 GB de RAM y un SSD, un switch gigabit sin gestión, un UPS básico y un segundo disco para backup. Todo lo demás — VLANs, firewall dedicado, cluster multi-nodo, GPU para IA local — es escala, no prerequisito.
