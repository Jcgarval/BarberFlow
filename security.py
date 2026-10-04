import os
import secrets
from pathlib import Path

import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# Importamos la conexión y el modelo necesario
from database import get_db
from models import Cliente

def _cargar_secret_key() -> str:
    """Lee la clave de la variable de entorno BARBERFLOW_SECRET_KEY.
    Si no existe, usa (o crea) un archivo local .secret_key que NO se sube a GitHub."""
    clave = os.getenv("BARBERFLOW_SECRET_KEY")
    if clave:
        return clave
    ruta = Path(__file__).parent / ".secret_key"
    if ruta.exists():
        return ruta.read_text().strip()
    clave = secrets.token_urlsafe(48)
    ruta.write_text(clave)
    return clave

SECRET_KEY = _cargar_secret_key()
ALGORITHM = "HS256"

security = HTTPBearer()

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=int(os.getenv("BARBERFLOW_BCRYPT_ROUNDS", "12")))
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credenciales.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o caducado")
    
    usuario = db.query(Cliente).filter(Cliente.email == email).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return usuario

def verificar_admin(usuario: Cliente = Depends(get_usuario_actual)):
    if usuario.rol != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return usuario