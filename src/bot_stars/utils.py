from telegram.ext import ContextTypes
from bot_stars.repository import Repository

def getRepository(context: ContextTypes.DEFAULT_TYPE):
    repository: Repository = context.bot_data.get("repository")
    return repository