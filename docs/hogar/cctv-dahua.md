---
title: CCTV y DVR Dahua
sidebar_position: 2
---

# CCTV / DVR Dahua

El DVR de cuatro canales forma parte del rack y debe tratarse como una zona de red de menor confianza.

:::note Por qué está en el rack
El DVR no es un componente que O.S.C.A.R. "necesite" — ya lo tenía antes de armar el rack, y se integra ahí simplemente para no dejarlo suelto con cables colgando. Si no tenés un DVR/CCTV propio, esta sección entera es opcional y no bloquea nada del resto de la arquitectura.
:::

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

- cambiar credenciales por defecto;
- actualizar firmware cuando sea seguro y aplicable;
- no publicar interfaz web del DVR en Internet;
- aislar CCTV de clientes/IoT mediante firewall cuando existan VLAN.
