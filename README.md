# Alacena · Generador de recetas

Aplicación del proyecto final de Tecnologías Web (5916). Cada usuario administra su inventario y puede generar, consultar, calificar de 1 a 5 estrellas y eliminar sus recetas.

## Arquitectura

FastAPI sirve la interfaz HTML/CSS/JS y la API REST. PostgreSQL persiste usuarios, ingredientes, recetas y calificaciones. El servicio interno de generación envía el inventario a [OpenRouter](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request) y valida la respuesta JSON con Pydantic antes de guardarla. Las contraseñas se almacenan como hashes Argon2id. Los endpoints privados requieren JWT Bearer y filtran datos por propietario.

## Ejecutar con Docker

Requisitos: Docker Engine con Compose v2.24.4 o posterior y una cuenta de OpenRouter con acceso a un modelo que acepte JSON mode.

1. Copia `.env.example` a `.env` (en PowerShell, `Copy-Item .env.example .env`).
2. Genera dos valores distintos con `python -c "import secrets; print(secrets.token_hex(32))"`. Ponlos en `POSTGRES_PASSWORD` y `JWT_SECRET`. Usa la contraseña hexadecimal para que sea compatible con la URL de conexión. Conserva el nombre y usuario de base de datos de ejemplo o usa identificadores alfanuméricos.
3. Configura `OPENROUTER_API_KEY` y `OPENROUTER_MODEL`. El inventario y las cuentas funcionan aunque la generación esté sin configurar.
4. Ejecuta `docker compose up -d --build`.
5. Abre <http://localhost:8000>. Swagger está en <http://localhost:8000/docs> y OpenAPI en `/openapi.json`.

El volumen `postgres` conserva los datos al recrear los contenedores. La API crea las tablas al arrancar con una base vacía. Para logs, usa `docker compose logs -f app`. Para detener los servicios y conservar los datos, usa `docker compose down`.

## Pruebas

```sh
python -m venv .venv
# Activa el entorno en Linux/macOS con source .venv/bin/activate
# En PowerShell usa .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

La suite usa una base SQLite temporal por prueba de API y simula OpenRouter en el flujo de generación. Cubre validación, prompt, parseo, autenticación, aislamiento entre cuentas, inventario, historial, calificación y eliminación.

## Endpoints

| Método y ruta | Operación |
| --- | --- |
| POST `/api/auth/register` | Crear cuenta y emitir JWT |
| POST `/api/auth/login` | Iniciar sesión y emitir JWT |
| GET / POST `/api/ingredients` | Listar o crear ingredientes |
| GET / PUT / DELETE `/api/ingredients/{id}` | Consultar, editar o eliminar un ingrediente |
| POST `/api/recipes/generate` | Generar y guardar a partir del inventario |
| GET `/api/recipes` | Consultar el historial personal |
| PUT `/api/recipes/{id}/rating` | Crear o actualizar la calificación |
| DELETE `/api/recipes/{id}` | Eliminar una receta y su calificación |

## Despliegue en VPS

1. Apunta el registro DNS A del dominio a la IP pública del VPS. Configura un registro AAAA solo si el servidor tiene IPv6 pública funcional.
2. Habilita TCP 80 y 443 en el firewall. Instala Docker Engine y Compose.
3. Clona el repositorio, crea `.env` en el servidor, restringe su acceso con `chmod 600 .env` y establece `DOMAIN` al nombre de host sin protocolo.
4. Ejecuta `docker compose -f docker-compose.yml -f compose.prod.yml up -d --build`. La configuración de producción publica 80 y 443 mediante Caddy y conecta el proxy con FastAPI por la red de Compose. Caddy obtiene y renueva el certificado automáticamente. [Documentación de Caddy](https://caddyserver.com/docs/quick-starts/https)
5. Comprueba `curl --fail --show-error https://TU_DOMINIO/openapi.json` y prueba en el navegador el flujo de registro, inventario, generación, calificación y eliminación.

Los secretos se configuran en `.env` en cada entorno. El repositorio incluye únicamente `.env.example`.
