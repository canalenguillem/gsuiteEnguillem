import os
from decouple import config
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes,CallbackQueryHandler


from googleapiclient.discovery import build
from google.oauth2 import service_account

# # Configurar el logging para ver mensajes de error o información
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')

# Función para conectar con Google Workspace
def connectar_amb_google():
    credentials_file = config('GOOGLE_CREDENTIALS_FILE')  # Archivo de credenciales desde .env
    admin_email = config('ADMIN_EMAIL')  # Correo electrónico del administrador del dominio desde .env
    scopes = ['https://www.googleapis.com/auth/admin.directory.user']
    
    credentials = service_account.Credentials.from_service_account_file(
        credentials_file, scopes=scopes)
    delegated_credentials = credentials.with_subject(admin_email)
    service = build('admin', 'directory_v1', credentials=delegated_credentials)
    return service

# Función para cambiar la contraseña y forzar el cambio en el próximo inicio de sesión
def canviar_password(service, email, new_password):
    try:
        body = {
            'password': new_password,
            'changePasswordAtNextLogin': True
        }
        service.users().update(userKey=email, body=body).execute()
        logger.info(f"Contraseña actualizada para {email}.")
        return True
    except Exception as e:
        logger.error(f"No se ha podido actualizar la contraseña para {email}: {e}")
        return False

# Función que será llamada cuando el usuario envíe el comando /change_password
async def change_password_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service = connectar_amb_google()
    print("change pass")
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /change_password <email> <nueva_contraseña>")
        return

    email = context.args[0]
    new_password = context.args[1]

    # if canviar_password(service, email, new_password):
    #     await update.message.reply_text(f"Contraseña cambiada correctamente para {email}.")
    # else:
    #     await update.message.reply_text(f"Error al cambiar la contraseña para {email}.")

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    print("starting")

# Función para gestionar los errores
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # logger.warning(f'Error: {context.error}')
    print(f'Error: {context.error}')


# Función principal para iniciar el bot de Telegram
def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    # Agregar el handler para el comando /change_password
    application.add_handler(CommandHandler('change_password', change_password_command))

    # Registrar la función de manejo de errores
    application.add_error_handler(error_handler)


    print("bot iniciat")
    application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

