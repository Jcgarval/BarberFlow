"""Envío de correos con la API HTTP de Brevo.

Render (plan gratis) bloquea los puertos SMTP, así que se envía por HTTPS.
Variables de entorno:
  BREVO_API_KEY       clave de la API de Brevo
  BREVO_SENDER_EMAIL  remitente (debe estar validado en Brevo)
  BREVO_SENDER_NAME   nombre visible del remitente (opcional, por defecto "BarberFlow")
  BARBERFLOW_MOSTRAR_CODIGO_EN_LOG=1   solo para probar en local sin Brevo: escribe el código en el log
"""
import logging
import os

import httpx

logger = logging.getLogger("barberflow.correo")

URL_BREVO = "https://api.brevo.com/v3/smtp/email"


def enviar_codigo_recuperacion(destino: str, codigo: str, minutos: int) -> None:
    """Envía el código de recuperación. Nunca lanza excepciones: se ejecuta en segundo plano
    y un fallo de envío no debe revelar si la cuenta existe; queda registrado en el log."""
    api_key = os.getenv("BREVO_API_KEY")
    remitente = os.getenv("BREVO_SENDER_EMAIL")
    if not api_key or not remitente:
        logger.error("Faltan BREVO_API_KEY o BREVO_SENDER_EMAIL: no se ha enviado el correo de recuperación")
        if os.getenv("BARBERFLOW_MOSTRAR_CODIGO_EN_LOG") == "1":
            logger.warning("Código de recuperación para %s: %s", destino, codigo)
        return

    cuerpo = {
        "sender": {"name": os.getenv("BREVO_SENDER_NAME", "BarberFlow"), "email": remitente},
        "to": [{"email": destino}],
        "subject": "Tu código de recuperación de BarberFlow",
        "textContent": (
            f"Tu código para recuperar la contraseña de BarberFlow es: {codigo}\n\n"
            f"Caduca en {minutos} minutos. Si no lo has pedido tú, ignora este correo: "
            "tu contraseña no ha cambiado."
        ),
        "htmlContent": (
            "<p>Tu código para recuperar la contraseña de BarberFlow es:</p>"
            f"<p style=\"font-size:28px;font-weight:bold;letter-spacing:6px\">{codigo}</p>"
            f"<p>Caduca en {minutos} minutos. Si no lo has pedido tú, ignora este correo: "
            "tu contraseña no ha cambiado.</p>"
        ),
    }
    try:
        respuesta = httpx.post(
            URL_BREVO,
            json=cuerpo,
            headers={"api-key": api_key, "accept": "application/json"},
            timeout=15,
        )
        respuesta.raise_for_status()
    except httpx.HTTPError as error:
        logger.error("Brevo no ha podido enviar el correo de recuperación: %s", error)