"""Crea un administrador (o convierte en admin a un usuario existente).

Uso:   python crear_admin.py "Nombre Apellido" correo@ejemplo.com
(la contraseña se pide por teclado y no se queda en el historial del terminal)
"""
import sys
import getpass

from database import SessionLocal, engine
from models import Base, Cliente
from security import get_password_hash

Base.metadata.create_all(bind=engine)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    nombre, email = sys.argv[1], sys.argv[2]
    db = SessionLocal()
    try:
        usuario = db.query(Cliente).filter(Cliente.email == email).first()
        if usuario:
            usuario.rol = "admin"
            db.commit()
            print(f"El usuario {email} ahora es admin (su contraseña no ha cambiado).")
            return

        password = getpass.getpass("Contraseña para el nuevo admin: ")
        if len(password) < 8:
            print("La contraseña debe tener al menos 8 caracteres.")
            sys.exit(1)
        db.add(Cliente(nombre=nombre, email=email, hashed_password=get_password_hash(password), rol="admin"))
        db.commit()
        print(f"Admin {email} creado correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
