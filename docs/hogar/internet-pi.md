---
title: Internet-Pi y probes
sidebar_position: 3
---

# Medición de Internet

Una Raspberry Pi separada del Dell es útil como punto independiente para medir conectividad.

## Métricas

- ping gateway;
- ping proveedor externo;
- DNS lookup;
- HTTP check;
- packet loss;
- velocidad con frecuencia razonable;
- Wi-Fi si la probe está conectada inalámbricamente.

## Diagnóstico

| Gateway | Internet | DNS | Interpretación probable |
|---|---|---|---|
| falla | falla | falla | LAN/router |
| ok | falla | falla | WAN/ISP |
| ok | ok | falla | DNS |
| ok | ok | ok | revisar servicio específico |
