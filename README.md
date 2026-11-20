# Alacena · Generador de recetas

Aplicación del proyecto final de Tecnologías Web (5916). Cada usuario administra su inventario y puede generar, consultar, calificar de 1 a 5 estrellas y eliminar sus recetas.

**Aplicación desplegada (Docker Compose + Cloudflare Tunnel):** <https://amplifier-improvements-workflow-cricket.trycloudflare.com> · **Documentación de la API:** <https://amplifier-improvements-workflow-cricket.trycloudflare.com/docs>

**Réplica alternativa (Vercel + Supabase):** <https://generadorderecetas.vercel.app>

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

## Despliegue con Docker y Cloudflare Tunnel

Es el despliegue de entrega. La aplicación y PostgreSQL corren en contenedores separados con Docker Compose en la máquina local, y un tercer contenedor, `cloudflared`, publica la aplicación en internet con HTTPS mediante [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/). No requiere abrir puertos del router ni pagar un servidor.

1. Instala y abre Docker Desktop.
2. Crea `.env` a partir de `.env.example` como se indica en "Ejecutar con Docker" y configura `OPENROUTER_API_KEY`.
3. Levanta los tres servicios:

   ```sh
   docker compose -f docker-compose.yml -f compose.tunnel.yml up -d --build
   ```

4. Consulta la URL pública HTTPS (`https://…trycloudflare.com`):

   ```sh
   docker compose -f docker-compose.yml -f compose.tunnel.yml logs cloudflared
   ```

5. Comprueba `/`, `/docs` y `/favicon.ico` en esa URL y prueba registro, inventario, generación, calificación y eliminación.

La URL del túnel rápido cambia cada vez que se reinicia el contenedor `cloudflared`. El equipo y Docker Desktop deben permanecer encendidos, sin suspensión, mientras la aplicación deba estar disponible. Si cambias `.env`, aplica los cambios con el mismo comando `up -d`: Compose recrea solo la aplicación y la URL del túnel se mantiene.

## Despliegue en VPS

1. Apunta el registro DNS A del dominio a la IP pública del VPS. Configura un registro AAAA solo si el servidor tiene IPv6 pública funcional.
2. Habilita TCP 80 y 443 en el firewall. Instala Docker Engine y Compose.
3. Clona el repositorio, crea `.env` en el servidor, restringe su acceso con `chmod 600 .env` y establece `DOMAIN` al nombre de host sin protocolo.
4. Ejecuta `docker compose -f docker-compose.yml -f compose.prod.yml up -d --build`. La configuración de producción publica 80 y 443 mediante Caddy y conecta el proxy con FastAPI por la red de Compose. Caddy obtiene y renueva el certificado automáticamente. [Documentación de Caddy](https://caddyserver.com/docs/quick-starts/https)
5. Comprueba `curl --fail --show-error https://TU_DOMINIO/openapi.json` y prueba en el navegador el flujo de registro, inventario, generación, calificación y eliminación.

Los secretos se configuran en `.env` en cada entorno. El repositorio incluye únicamente `.env.example`.

## Publicación alternativa en Vercel con Supabase

La réplica publicada en <https://generadorderecetas.vercel.app> usa esta opción: FastAPI en Vercel con HTTPS y PostgreSQL administrado en Supabase, donde se crearon las tablas `usuarios`, `ingredientes`, `recetas` y `calificaciones`. La generación usa `openai/gpt-4.1-mini` a través de OpenRouter. El enunciado pide un VPS con Docker Compose para el criterio de despliegue; la configuración para VPS de la sección anterior está lista para usarse.

Antes de entregar la URL, ábrela en una ventana de incógnito: las URL de vista previa de Vercel (`*-git-main-*.vercel.app`) exigen iniciar sesión en Vercel. Entrega la URL de producción.

1. Crea un proyecto de Supabase dedicado a Alacena. Desactiva **Data API** en los ajustes de Supabase, ya que todas las consultas pasan por FastAPI y su JWT.
2. En **Connect → Transaction pooler**, copia la URI de PostgreSQL y sustituye la contraseña. Si contiene caracteres reservados de URL, codifícalos. Conserva el puerto `6543`. [Conexión PostgreSQL en Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres)
3. Importa el repositorio público en Vercel. Selecciona **FastAPI** y la raíz del repositorio. Vercel detecta `app/main.py`. [FastAPI en Vercel](https://vercel.com/docs/frameworks/backend/fastapi)
4. En las variables de entorno de producción, configura `DATABASE_URL` con la URI de Supabase, `DATABASE_TRANSACTION_POOLER=1`, `JWT_SECRET` con un valor aleatorio de 32 caracteres o más, `OPENROUTER_API_KEY` y `OPENROUTER_MODEL`. El modo pooler exige SSL y desactiva la preparación automática de sentencias.
5. Despliega, abre la URL HTTPS y verifica que `/`, `/docs` y `/favicon.ico` cargan. Prueba registro, inventario, generación, calificación y eliminación con una cuenta de prueba.
