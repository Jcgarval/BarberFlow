from sqlalchemy import String, Integer, Float, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Cliente(Base):
    __tablename__ = "clientes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))
    telefono: Mapped[str] = mapped_column(String(20))

class Barbero(Base):
    __tablename__ = "barberos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))
    activo: Mapped[bool] = mapped_column(default=True)

class Servicio(Base):
    __tablename__ = "servicios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))
    duracion_minutos: Mapped[int] = mapped_column()
    precio: Mapped[float] = mapped_column()

class Cita(Base):
    __tablename__ = "citas"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    barbero_id: Mapped[int] = mapped_column(ForeignKey("barberos.id"))
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios.id"))
    fecha_hora: Mapped[datetime] = mapped_column()


motor = create_engine("sqlite:///barberia.db", echo=True)
Base.metadata.create_all(motor)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)