---
title: Cheatsheet
sidebar_position: 4
---

# Comandos útiles

## Linux

```bash
ip addr
ip route
ss -tulpn
df -h
free -h
journalctl -p err -b
```

## Docker

```bash
docker compose ps
docker compose logs -f --tail=100
docker stats
docker system df
```

## Kubernetes

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get events -A --sort-by=.lastTimestamp
kubectl top nodes
kubectl top pods -A
```

## DNS/network

```bash
dig host @dns
curl -vk https://host
nc -vz host port
traceroute host
```
