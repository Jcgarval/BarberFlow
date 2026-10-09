"""Crea un administrador, convierte en admin a un usuario existente o le cambia la contraseña.

Uso:   python crear_admin.py "Nombre Apellido" correo@ejemplo.com
       python crear_admin.py "Nombre Apellido" correo@ejemplo.com --cambiar-password

Con --cambiar-password, si el usuario ya existe se le pide una contraseña nueva.
(la contraseña se pide por teclado y no se queda en el historial del terminal)
"""
import sys
import getpass

from database import SessionLocal
from migraciones import preparar_base_de_datos
from models import Cliente
from security import get_password_hash

preparar_base_de_datos()

OPCION_CAMBIAR = "--cambiar-password"


def pedir_password(mensaje: str) -> str:
    password = getpass.getpass(mensaje)
    if len(password) < 8:
        print("La contraseña debe tener al menos 8 caracteres.")
        sys.exit(1)
    return password


def main():
    argumentos = [a for a in sys.argv[1:] if a != OPCION_CAMBIAR]
    cambiar_password = OPCION_CAMBIAR in sys.argv[1:]
    if len(argumentos) != 2:
        print(__doc__)
        sys.exit(1)

    nombre, email = argumentos
    db = SessionLocal()
    try:
        usuario = db.query(Cliente).filter(Cliente.email == email).first()
        if usuario:
            usuario.rol = "admin"
            if cambiar_password:
                password = pedir_password("Nueva contraseña: ")
                usuario.hashed_password = get_password_hash(password)
                db.commit()
                print(f"Contraseña de {email} cambiada. El usuario es admin.")
            else:
                db.commit()
                print(f"El usuario {email} ahora es admin (su contraseña no ha cambiado).")
            return

        password = pedir_password("Contraseña para el nuevo admin: ")
        db.add(Cliente(nombre=nombre, email=email, hashed_password=get_password_hash(password), rol="admin"))
        db.commit()
        print(f"Admin {email} creado correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    main()