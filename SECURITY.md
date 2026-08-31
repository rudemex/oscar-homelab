# Seguridad

Este repositorio documenta infraestructura doméstica y por eso debe asumirse que puede contener información útil para un atacante si se publica sin cuidado.

## No versionar

- IP pública;
- tokens;
- passwords;
- claves privadas;
- kubeconfig administrativo;
- credenciales Cloudflare;
- secretos n8n;
- dumps reales;
- backups;
- configuraciones exportadas que contengan secretos.

## Reporte

Si se detecta un secreto publicado, rotarlo primero. Borrarlo solamente del último commit no lo elimina del historial ni invalida la credencial expuesta.
