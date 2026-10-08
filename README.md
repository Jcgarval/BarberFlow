<p align="center">
  <img src="docs/logo.png" width="120" alt="Logo de BarberFlow">
</p>

<h1 align="center">BarberFlow API</h1>

<p align="center">
  API REST con FastAPI para gestionar citas, barberos y servicios de una barbería.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLAlchemy-Alembic-D71F00?logo=sqlalchemy&logoColor=white" alt="SQLAlchemy y Alembic">
  <img src="https://img.shields.io/badge/PostgreSQL-Neon-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL en Neon">
  <img src="https://img.shields.io/badge/Desplegada%20en-Render-46E3B7?logo=render&logoColor=white" alt="Desplegada en Render">
  <a href="https://github.com/Jcgarval/BarberFlow-Android"><img src="https://img.shields.io/badge/Cliente-Android-3DDC84?logo=android&logoColor=white" alt="Cliente Android"></a>
  <a href="https://github.com/Jcgarval/BarberFlow/actions/workflows/tests.yml"><img src="https://github.com/Jcgarval/BarberFlow/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <img src="https://img.shields.io/badge/cobertura-%E2%89%A590%25-brightgreen" alt="Cobertura de pruebas: al menos el 90 %">
</p>

## Descripción

Backend del ecosistema **BarberFlow**. Gestiona usuarios con roles (cliente y administrador), el catálogo de barberos y servicios y las reservas, con las reglas de negocio de una barbería real. Su cliente es la [app Android](https://github.com/Jcgarval/BarberFlow-Android).

Proyecto de portfolio personal para demostrar desarrollo backend con Python: arquitectura modular, autenticación con JWT, control de permisos por rol, validación de datos, migraciones de base de datos y despliegue en la nube.

## API en producción

La API está desplegada y se puede probar desde el navegador:

- **Documentación interactiva (Swagger):** https://barberflow-api-cko3.onrender.com/docs

> Se aloja en el plan gratuito de Render, que **duerme el servicio tras un rato sin uso**: la primera petición puede tardar hasta un minuto en responder y las siguientes van con normalidad.

## Funcionalidades y reglas de negocio

- **Autenticación JWT** (HS256, caducidad de 24 horas) y contraseñas cifradas con bcrypt.
- **Permisos por rol:** un cliente solo ve, reserva y cancela sus propias citas; el administrador gestiona todo. El rol nunca se acepta desde el registro.
- **Horas libres:** `GET /citas/disponibilidad` calcula las franjas de inicio (cada 30 minutos, de 09:00 a 20:00) teniendo en cuenta la duración del servicio y las citas del barbero.
- **Sin solapes:** un barbero no puede tener dos citas a la vez; la cita completa debe terminar dentro del horario y no se aceptan fechas pasadas.
- **Días de cierre:** los domingos no se puede reservar y no se ofrece ninguna franja (la regla vive en el servidor, no solo en la app).
- **Estados de cita:** `pendiente`, `confirmada`, `completada` y `cancelada`. Una cita cancelada libera su hueco. El cliente solo puede cancelar; el administrador puede cambiar a cualquier estado.
- **Baja lógica:** un barbero o servicio con citas asociadas se da de baja (`activo = false`) en lugar de borrarse, conservando el historial, y se puede reactivar.
- **Validación de datos** con Pydantic (nombres, duración entre 1 y 480 minutos, precio entre 0 y 1000).
- **Migraciones con Alembic:** al arrancar, la API crea el esquema o lo actualiza hasta la última versión, también en bases de datos anteriores a Alembic, sin perder datos.
- **Pruebas automáticas** con pytest (cobertura del 95 %) que se ejecutan en cada `push` mediante GitHub Actions.

## Tecnologías

- Python 3, FastAPI y Uvicorn
- SQLAlchemy y Alembic (SQLite en local, PostgreSQL en producción)
- Pydantic para esquemas y validación
- JWT (python-jose) y bcrypt
- pytest y GitHub Actions para las pruebas automáticas
- Render (servidor) y Neon (PostgreSQL) para el despliegue

## Estructura

```
├── main.py            # Aplicación y routers
├── migraciones.py     # Prepara la base de datos con Alembic al arrancar
├── database.py        # Conexión (SQLite o PostgreSQL según la URL)
├── models.py          # Modelos SQLAlchemy
├── schemas.py         # Esquemas Pydantic
├── security.py        # JWT, hashing y dependencias de autenticación y roles
├── crear_admin.py     # Script para crear o ascender administradores
├── alembic.ini        # Configuración de Alembic
├── alembic/           # Entorno y versiones de las migraciones
├── requirements.txt
├── requirements-dev.txt   # dependencias de desarrollo y pruebas
├── pytest.ini
├── .github/workflows/tests.yml   # integración continua
├── tests/             # pruebas de autenticación, catálogo, citas, administración y migración
└── routers/
    ├── auth.py        # Login
    ├── clientes.py    # Registro
    ├── barberos.py
    ├── servicios.py
    ├── citas.py       # Disponibilidad, reservas y estados
    └── admin.py       # Vista detallada de citas
```

## Instalación y ejecución en local

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/Jcgarval/BarberFlow.git
   cd BarberFlow
   ```

2. **Crea y activa un entorno virtual:**

   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux, WSL o macOS:
   source venv/bin/activate
   ```

3. **Instala las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Arranca el servidor** (crea `barberflow.db` y aplica las migraciones automáticamente):

   ```bash
   uvicorn main:app --reload
   ```

   Para usar la app desde un móvil físico en la misma red, añade `--host 0.0.0.0`.

5. **Crea un administrador:**

   ```bash
   python crear_admin.py "Tu Nombre" tu@correo.com
   ```

   La contraseña se pide por teclado. Si el correo ya existe, ese usuario pasa a ser administrador.

### Configuración

Todo se controla con variables de entorno:

| Variable | Para qué sirve | Si no existe |
|---|---|---|
| `BARBERFLOW_SECRET_KEY` | Clave que firma los tokens JWT | El servidor genera un archivo local `.secret_key` (excluido de Git) y lo reutiliza |
| `BARBERFLOW_DATABASE_URL` | Base de datos (SQLite o PostgreSQL) | Usa `barberflow.db` (SQLite, excluida de Git) |

Con PostgreSQL basta con pasar la URL tal cual la entrega el proveedor (`postgresql://usuario:contraseña@host/base?sslmode=require`); la aplicación añade el driver por su cuenta.

## Despliegue

La API corre en **Render** (plan gratuito) y guarda sus datos en **PostgreSQL en Neon** (plan gratuito), porque el disco de Render es efímero y un archivo SQLite se perdería en cada reinicio.

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Variables de entorno:** `BARBERFLOW_DATABASE_URL`, `BARBERFLOW_SECRET_KEY` y `PYTHON_VERSION`.
- Las migraciones se aplican solas al arrancar, así que no hace falta un paso aparte.
- Para crear el administrador en producción se ejecuta `crear_admin.py` desde un equipo local con `BARBERFLOW_DATABASE_URL` apuntando a la base de Neon.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest
```

La suite (más de 80 pruebas, en pocos segundos) usa una **base de datos temporal y su propia clave secreta**, así que no toca `barberflow.db` ni crea `.secret_key`. Cubre:

- **Autenticación:** registro, login, tokens manipulados, caducados o firmados con otra clave, y acceso por rol.
- **Catálogo:** permisos, validación de datos, baja lógica y reactivación.
- **Citas:** horas libres, reservas, solapes, horario de apertura, días de cierre, fechas pasadas, estados y quién puede ver o modificar cada cita.
- **Migración:** actualización de una base de datos antigua sin perder datos.
- **Administración:** el script `crear_admin.py`, la única forma de crear administradores.

Para ver qué porcentaje del código recorren las pruebas:

```bash
pytest --cov --cov-report=term-missing
```

La cobertura actual ronda el **95 %**. Cada `push` y cada pull request ejecutan las pruebas en GitHub Actions (`.github/workflows/tests.yml`) y **la ejecución falla si la cobertura baja del 90 %**; por eso la insignia indica «≥ 90 %». El resumen con la tabla aparece en la página de cada ejecución.

## Documentación interactiva

Con el servidor en marcha en local:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

En producción: https://barberflow-api-cko3.onrender.com/docs

## Endpoints

**Acceso:** 🌐 público · 🔑 requiere token · 🛡️ solo administrador

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| POST | `/login` | 🌐 | Inicia sesión y devuelve el token |
| POST | `/clientes/` | 🌐 | Registro de cliente |
| GET | `/barberos/` · `/barberos/{id}` | 🌐 | Barberos activos |
| POST · PUT · DELETE | `/barberos/` · `/barberos/{id}` | 🛡️ | Alta, edición y baja o borrado |
| GET | `/barberos/inactivos` | 🛡️ | Barberos dados de baja |
| POST | `/barberos/{id}/reactivar` | 🛡️ | Reactiva un barbero |
| GET | `/servicios/` · `/servicios/{id}` | 🌐 | Servicios activos |
| POST · PUT · DELETE | `/servicios/` · `/servicios/{id}` | 🛡️ | Alta, edición y baja o borrado |
| GET | `/servicios/inactivos` | 🛡️ | Servicios dados de baja |
| POST | `/servicios/{id}/reactivar` | 🛡️ | Reactiva un servicio |
| GET | `/citas/disponibilidad` | 🔑 | Horas libres (`barbero_id`, `servicio_id`, `fecha`) |
| POST | `/citas/` | 🔑 | Reserva una cita (el cliente, solo a su nombre) |
| GET | `/citas/` | 🔑 | Lista de citas (cliente: las suyas; admin: todas, con filtros) |
| GET · PUT · DELETE | `/citas/{id}` | 🔑 | Consulta, modifica o elimina (propietario o admin) |
| PATCH | `/citas/{id}/estado` | 🔑 | Cambia el estado (el cliente, solo cancelar) |
| GET | `/admin/citas/detalles` | 🛡️ | Citas con nombres de cliente, barbero y servicio |

## Próximas mejoras

- Paginación en los listados de citas.

## Autor

**José Carlos** · [@Jcgarval](https://github.com/Jcgarval)
