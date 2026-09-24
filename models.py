from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Barbero(Base):
    __tablename__ = "barberos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    activo = Column(Boolean, default=True)

    citas = relationship("Cita", back_populates="barbero")


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    telefono = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    rol = Column(String, default="cliente")

    citas = relationship("Cita", back_populates="cliente")


class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    duracion_minutos = Column(Integer)
    precio = Column(Float)

    citas = relationship("Cita", back_populates="servicio")


class Cita(Base):
    __tablename__ = "citas"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    barbero_id = Column(Integer, ForeignKey("barberos.id"))
    servicio_id = Column(Integer, ForeignKey("servicios.id"))
    fecha_hora = Column(DateTime)

    # Conexiones de vuelta (relaciones) que faltaban para evitar el error 500
    cliente = relationship("Cliente", back_populates="citas")
    barbero = relationship("Barbero", back_populates="citas")
    servicio = relationship("Servicio", back_populates="citas")