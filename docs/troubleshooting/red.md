---
title: Problemas de red
sidebar_position: 2
---

# Troubleshooting de red

## Link

```bash
ip link
ip addr
ip route
```

## Camino

```bash
ping <gateway>
traceroute <destino>
```

## DNS

```bash
nslookup host <dns>
dig host @<dns>
```

## Puerto

```bash
nc -vz <host> <port>
curl -vk https://<host>/
```

## Regla útil

Si por IP funciona y por hostname no, mirar DNS antes de tocar Docker/Kubernetes.

Si desde localhost funciona y desde otra máquina no, mirar bind address, firewall, routing y proxy.
