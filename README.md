# ✂️ BarberFlow API

BarberFlow es una API RESTful desarrollada con **FastAPI** diseñada para gestionar las citas y el flujo de trabajo de una barbería. Permite la administración ágil de reservas, gestión de personal, control de servicios y autenticación de usuarios.

Este proyecto ha sido desarrollado como parte de mi portfolio personal para demostrar mis habilidades en el desarrollo backend con Python. Recientemente ha sido refactorizado para seguir buenas prácticas de la industria, separando responsabilidades mediante una **arquitectura modular** e implementando **seguridad con tokens JWT**.

## 🚀 Tecnologías utilizadas

* **Lenguaje:** Python 3.x
* **Framework:** FastAPI
* **Servidor ASGI:** Uvicorn
* **Base de Datos & ORM:** SQLite + SQLAlchemy
* **Seguridad:** JWT (JSON Web Tokens) y Bcrypt (hashing de contraseñas)
* **Documentación interactiva:** Swagger UI y ReDoc

## 🏗️ Arquitectura Modular

El proyecto está diseñado para ser escalable y mantenible, dividiendo el monolito inicial en submódulos utilizando `APIRouter` de FastAPI:

* `database.py`: Gestión de la conexión a SQLite.
* `security.py`: Dependencias de autenticación, roles y encriptación.
* `routers/`: Directorio que aísla la lógica de cada dominio (Auth, Clientes, Barberos, Servicios, Citas, y Panel de Administración).

## ⚙️ Instalación y ejecución en local

Si quieres clonar este repositorio y probar la API en tu propio equipo, sigue estos pasos:

1. **Clona el repositorio:**
   ```bash
   git clone [https://github.com/Jcgarval/BarberFlow.git](https://github.com/Jcgarval/BarberFlow.git)
   cd BarberFlow
   ```

2. **Crea y activa un entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/WSL o macOS:
   source venv/bin/activate
   ```

3. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecuta el servidor de desarrollo:**
   ```bash
   uvicorn main:app --reload
   ```

## 📖 Documentación de la API

FastAPI autogenera la documentación del proyecto. Una vez que el servidor esté corriendo, puedes interactuar directamente con la API y probar los endpoints protegidos desde tu navegador:

* **Swagger UI:** http://127.0.0.1:8000/docs
* **ReDoc:** http://127.0.0.1:8000/redoc

## 🔗 Endpoints principales

La API cuenta con un sistema de roles (Cliente / Admin) y validaciones anti-solapamiento de horarios. Algunos de los bloques principales son:

* **🔐 Autenticación:** `/login` (Generación de Bearer Token), `/clientes` (Registro).
* **📅 Citas:** `/citas` (CRUD completo de reservas con validación de horario comercial).
* **💈 Catálogo (Protegido para Admin):** `/barberos` y `/servicios`.
* **👑 Administración:** `/admin/citas/detalles` (Cruce de datos relacionales para mostrar nombres reales en lugar de IDs).

---
*Desarrollado por José Carlos García Valdelvira - Buscando mi primera oportunidad como Programador Junior Backend o Técnico de Sistemas.*