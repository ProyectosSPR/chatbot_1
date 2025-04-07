from fastapi import FastAPI, Request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from db import init_db
from chatbot import chatbot_with_postgres
from logger import logger  # 👈 importamos nuestro logger personalizado
import os

# Eliminar TWILIO_WHATSAPP_NUMBER si existe
os.environ.pop("TWILIO_WHATSAPP_NUMBER", None)

# Cargar variables de entorno
load_dotenv()

# Obtener las variables de entorno para Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# Configuración del cliente de Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Función lifespan para inicializar base de datos
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando la aplicación y base de datos...")
    init_db()
    logger.info("✅ Base de datos inicializada correctamente.")
    yield
    logger.info("🛑 Finalizando lifespan...")

# Crear la aplicación FastAPI
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    logger.info("📥 Petición recibida en el endpoint root.")
    return {"message": "API de WhatsApp con Twilio"}

@app.post("/send_message")
async def send_and_receive_message(request: Request):
    logger.info("📩 Procesando solicitud de mensaje entrante...")

    # Obtener datos del mensaje
    form_data = await request.form()
    from_number = form_data.get('From')
    body = form_data.get('Body')

    logger.info(f"🗨️ Mensaje recibido de {from_number}: {body}")
    from_number = from_number.replace("whatsapp:", "")
    # Simular "escribiendo..." enviando un mensaje temporal
    try:
        logger.info("✍️ Enviando simulación de escritura...")
        client.messages.create(
            from_=f'whatsapp:{TWILIO_WHATSAPP_NUMBER}',
            body="💬 Despacho contable está escribiendo...",
            to=f'whatsapp:{from_number}'
        )
    except Exception as e:
        logger.error(f"❌ Error al enviar el mensaje 'escribiendo...': {e}")

    # Esperar 1.5 segundos antes de enviar la respuesta real
    import time
    time.sleep(1.5)


    # Llamar al chatbot
    chatbot_response = chatbot_with_postgres(
        thread_id=from_number,
        query=body,
        prompt="Eres un asistente virtual siempre inicia con hola te gusta las bananas y a luis le gustan más:",
    )

    # Preparar respuesta Twilio
    response = MessagingResponse()
    response.message(chatbot_response)

    # Enviar respuesta por Twilio
    try:
        logger.info("📤 Enviando mensaje a través de Twilio...")
        message = client.messages.create(
            from_=f'whatsapp:{TWILIO_WHATSAPP_NUMBER}',
            body=chatbot_response,
            to=f'whatsapp:{from_number}'
        )
        logger.info(f"✅ Mensaje enviado con SID: {message.sid}")
    except Exception as e:
        logger.error(f"❌ Error al enviar el mensaje: {e}")

    return str(response)
