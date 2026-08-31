---
title: DNS y Pi-hole
sidebar_position: 4
---

# DNS con Pi-hole

Pi-hole puede prestar bloqueo DNS, resolución de nombres locales y visibilidad de consultas.

## Diseño recomendado

Evitar que toda la casa dependa de una única Raspberry o VM. El objetivo es disponer de dos resolvers cuando la arquitectura madure.

```text
DNS1 -> Pi-hole principal
DNS2 -> Pi-hole secundario / resolver alternativo
```

## Qué podemos hacer

- bloquear dominios de tracking conocidos;
- crear registros locales para servicios del homelab;
- observar qué dispositivos generan consultas;
- aplicar grupos/listas diferentes;
- detectar clientes con comportamiento anormal.

## Qué no debe hacer Pi-hole por sí solo

Pi-hole no reemplaza firewall, autenticación, filtrado TLS ni controles de acceso. Bloquear un dominio por DNS tampoco impide necesariamente que un cliente alcance una IP directamente.

## Validación

```bash
nslookup grafana.oscar.home <IP_DNS>
nslookup example.com <IP_DNS>
```

Registrar latencia, errores y volumen de consultas en observabilidad.
