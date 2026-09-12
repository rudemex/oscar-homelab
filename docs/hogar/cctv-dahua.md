---
title: CCTV y DVR Dahua
sidebar_position: 2
---

# CCTV / DVR Dahua

El DVR de cuatro canales forma parte del rack y debe tratarse como una zona de red de menor confianza.

:::note Por qué está en el rack
El DVR no es un componente que O.S.C.A.R. "necesite" — ya lo tenía antes de armar el rack, y se integra ahí simplemente para no dejarlo suelto con cables colgando. Si no tenés un DVR/CCTV propio, esta sección entera es opcional y no bloquea nada del resto de la arquitectura.
:::

## Estado actual

Ya tiene IP fija en la LAN (`192.168.0.224`) y la interfaz web responde (HTTP redirige a HTTPS, certificado propio del equipo). La tarjeta en [Homepage](../servicios/homepage.md) (grupo Hogar) es un link simple a esa interfaz nativa, con chequeo de estado (el puntito verde/rojo) — sin video ni preview dentro del dashboard.

Hubo dos intentos completos de tener video de las cámaras integrado en Homepage: primero un proxy HTTP propio ([DVR Proxy](../servicios/dvr-proxy.md), MJPEG casero, rompía al publicarse por Cloudflare — no sostiene streams de longitud indefinida), después [go2rtc](../servicios/go2rtc.md) (RTSP real, HD, todo LAN sin ninguna puerta pública — una decisión tomada a propósito para cámaras de seguridad). Este segundo intento resolvió casi todo, pero quedó un problema de orientación sin cerrar: 3 de las 4 cámaras graban en "modo pasillo" y ningún sentido de rotación en CSS coincidía con cómo las muestra el monitor real del DVR. En ese punto se decidió parar del todo — **no vale la pena seguir invirtiendo tiempo y recursos en tener video de las cámaras dentro de O.S.C.A.R.** — y las dos tarjetas volvieron a ser links simples. Se evaluó Frigate en el camino (grabación + detección con IA) pero ni siquiera llegó a intentarse: `core01` (2 vCPUs, sin GPU, 45GB libres compartidos con el resto de los servicios) no tiene margen para eso. Lo que sigue pendiente de la lista de objetivos de abajo: VLAN dedicada, bandeja física propia; video/Frigate queda descartado salvo que cambie sustancialmente el hardware disponible.

## Objetivos

- cableado ordenado mediante patch panel/balunera;
- VLAN CCTV futura;
- acceso desde clientes autorizados;
- evitar Internet saliente innecesario;
- integrar streams con Home Assistant/Frigate solo si el DVR expone protocolos compatibles y sin degradar grabación.

## Bandeja

Dimensiones conocidas del DVR: **197 × 192 × 41 mm**. La bandeja física debe contemplar:

- holgura;
- conectores traseros;
- ventilación;
- fijación;
- acceso a balunera/cables.

## Seguridad

- **el DVR reutiliza la misma contraseña que Proxmox, el router, Uptime Kuma y AdGuard Home** — quinto sistema confirmado con la contraseña repetida; sigue pendiente rotarla en todos lados;
- cambiar credenciales por defecto;
- actualizar firmware cuando sea seguro y aplicable;
- no publicar interfaz web del DVR en Internet;
- aislar CCTV de clientes/IoT mediante firewall cuando existan VLAN.
