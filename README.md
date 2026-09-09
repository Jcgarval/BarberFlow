# ✂️ BarberFlow API

BarberFlow es una API RESTful desarrollada con **FastAPI** diseñada para gestionar las citas y el flujo de trabajo de una barbería. Permite la administración ágil de reservas, optimizando la agenda y facilitando la gestión del negocio.

Este proyecto ha sido desarrollado como parte de mi portfolio personal para demostrar mis habilidades en el desarrollo de backend con Python.

## 🚀 Tecnologías utilizadas

* **Lenguaje:** Python 3.x
* **Framework:** FastAPI
* **Servidor ASGI:** Uvicorn
* **Base de Datos:** SQLite
* **Documentación interactiva:** Swagger UI (integrado en FastAPI)

## ⚙️ Instalación y ejecución en local

Si quieres clonar este repositorio y probar la API en tu propio equipo, sigue estos pasos:

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/Jcgarval/BarberFlow.git
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
   *(Nota: Asegúrate de que el archivo principal se llama `main.py`. Si se llama diferente, cámbialo en el comando).*

## 📖 Documentación de la API

Una de las grandes ventajas de FastAPI es que autogenera la documentación. Una vez que el servidor esté corriendo, puedes interactuar directamente con la API desde tu navegador:

* **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 🔗 Endpoints principales

Aquí tienes algunos ejemplos de las rutas disponibles en la API:

* `GET /citas` - Obtiene la lista de todas las citas programadas.
* `POST /citas` - Crea una nueva reserva.
* `GET /citas/{id}` - Obtiene los detalles de una cita específica.
* `DELETE /citas/{id}` - Cancela una reserva.

---
*Desarrollado por José Carlos - Buscando mi primera oportunidad como Programador Junior Backend.*
