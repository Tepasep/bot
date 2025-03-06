from telegram.ext import ContextTypes
from bot_stars.repository import Repository, SheetsRepository

def getRepository(context: ContextTypes.DEFAULT_TYPE):
    repository: Repository = context.bot_data.get("repository")
    return repository

def getSheetRepository(context: ContextTypes.DEFAULT_TYPE):
    repository: SheetsRepository = context.bot_data.get("sheet_repository")
    return repository