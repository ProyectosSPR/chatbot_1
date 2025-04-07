from fastapi import FastAPI, Request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os
from dotenv import load_dotenv
import logging
from db import init_db  # Importar la función de inicialización de la base de datos
from chatbot import chatbot_with_postgres  
from contextlib import asynccontextmanager


os.environ.pop("TWILIO_WHATSAPP_NUMBER", None)  # Eliminar TWILIO_WHATSAPP_NUMBER si existe


# Cargar variables de entorno
load_dotenv()

# Obtener las variables de entorno para Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# Configuración del cliente de Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# Función lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Inicializando la base de datos...")
    init_db()  # Aquí se inicializa la base de datos
    yield
    logging.info("Base de datos inicializada.")

# Crear la aplicación FastAPI con el evento lifespan
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    logging.info("Endpoint root accedido.")
    return {"message": "API de WhatsApp con Twilio"}

@app.post("/send_message")
async def send_and_receive_message(request: Request):
    """
    Este endpoint recibirá los mensajes de WhatsApp y responderá automáticamente utilizando el chatbot.
    """
    logging.info("Procesando solicitud de mensaje entrante.")

    # Obtener el cuerpo de la solicitud (form-data) enviada por Twilio
    form_data = await request.form()
    from_number = form_data.get('From')  # Número de quien envió el mensaje
    body = form_data.get('Body')  # Cuerpo del mensaje recibido

    logging.info(f"Mensaje recibido de {from_number}: {body}")
    from_number = from_number.replace("whatsapp:", "")

    # Llamar a la función del chatbot para generar la respuesta
    chatbot_response = chatbot_with_postgres(
        thread_id=from_number,  # Usamos el número de teléfono como identificador del hilo
        query=body,  # El cuerpo del mensaje recibido es la consulta
        prompt="Eres un asistente virtual siempre inicia con hola te gusta las bananas y a luis le gustan mas:",  # Puedes ajustar el prompt aquí
    )

    # Crear la respuesta de Twilio usando TwiML
    response = MessagingResponse()
    response.message(chatbot_response)

    # Intentar enviar un mensaje con la API de Twilio
    try:
        logging.info(f"Enviando mensaje a número de destino usando Twilio.")
        message = client.messages.create(
            from_=f'whatsapp:{TWILIO_WHATSAPP_NUMBER}',  # Número de WhatsApp aprobado en Twilio
            body=chatbot_response,  # Usamos la respuesta generada por el chatbot
            to=f'whatsapp:{from_number}'  # Número de teléfono de destino
        )
        logging.info(f"Mensaje enviado exitosamente con SID: {message.sid}")

    except Exception as e:
        logging.error(f"Error al enviar el mensaje: {e}, Número de WhatsApp: {TWILIO_WHATSAPP_NUMBER}")

    # Devolver la respuesta de Twilio en formato TwiML (usado para responder automáticamente)
    return str(response)  # Twilio espera el TwiML en formato string
