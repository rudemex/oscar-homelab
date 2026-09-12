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

Ya tiene IP fija en la LAN (`192.168.0.224`) y la interfaz web responde (HTTP redirige a HTTPS, certificado propio del equipo). La tarjeta en [Homepage](../servicios/homepage.md) (grupo Hogar) no lleva a la app nativa del DVR — lleva a una grilla propia con las 4 cámaras **en vivo de verdad**, servida por [go2rtc](../servicios/go2rtc.md): habla RTSP con el DVR (su protocolo nativo) y reempaqueta el video en un formato que el navegador reproduce directo, sin que la contraseña del DVR viaje nunca al navegador. La tarjeta también trae un preview en vivo de un canal, directo en Homepage (un `iframe`, no código propio). A diferencia del resto de los servicios de esta cuenta, **esto no tiene ninguna puerta hacia internet** — ni dominio público ni Cloudflare Access — cámaras de seguridad quedaron afuera de ese criterio a propósito: solo cargan estando conectado a la LAN de casa (ver [go2rtc](../servicios/go2rtc.md#por-qué-solo-lan)).

Antes de go2rtc hubo un proxy HTTP propio ([DVR Proxy](../servicios/dvr-proxy.md), hoy retirado) que llegó a tener video MJPEG real, y llegó incluso a publicarse por el Tunnel con Access adelante — se dio de baja del todo, no solo porque Cloudflare no sostiene un stream HTTP de longitud indefinida (el motivo técnico original), sino porque después se decidió que las cámaras no van a tener ninguna puerta pública, punto. Se evaluó Frigate para tener video HD (grabación + detección con IA), pero `core01` (2 vCPUs, sin GPU, 45GB libres compartidos con el resto de los servicios) no tiene margen para eso sin afectar todo lo demás que corre ahí — go2rtc da el mismo video fluido, en la resolución completa del DVR, sin esa carga. Lo que sigue pendiente de la lista de objetivos de abajo: VLAN dedicada, bandeja física propia, y evaluar Frigate más adelante si algún día se suma más CPU/GPU dedicada.

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
