---
title: Backup de n8n
sidebar_position: 4
---

# Backup y restore de n8n

n8n es un buen ejemplo de por qué “copiar un volumen” no siempre alcanza.

## Elementos

- DB PostgreSQL;
- encryption key;
- configuración Compose;
- archivos/volumen n8n si las features usadas guardan estado allí.

## Backup DB

Ejemplo conceptual desde el contenedor Postgres:

```bash
docker compose exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  > n8n-$(date +%F).sql
```

Verificar que el archivo no esté vacío y moverlo al destino de backup.

## Encryption key

Guardar la key en el gestor/backup de secretos. **No incluirla en el mismo repo público que el Compose.**

## Restore drill

1. crear stack n8n aislado;
2. usar DB vacía;
3. restaurar SQL;
4. configurar la misma encryption key;
5. iniciar n8n;
6. comprobar workflows;
7. comprobar que credenciales existentes se descifran;
8. ejecutar workflow no destructivo.

## RPO

Si n8n cambia workflows diariamente, backup diario es un punto inicial razonable. Ajustar según uso real.
