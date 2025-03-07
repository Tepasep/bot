from telegram import Message
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime



class Repository:
    def __init__(self, token):
        self.token = token

class SheetsRepository:
    def __init__(self, credentialsFile: str, spreadsheetName: str):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentialsFile,
            [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        self.client = gspread.authorize(credentials)
        self.sheet = self.client.open(spreadsheetName).sheet1

    def saveNewUser(
        self,
        user_id: str,
        user_name: str,
        user_lastname: str,
        birthdate: str,
        phone: str,
    ):
        if self.sheet.acell("A1").value == None:
            self.sheet.append_row(["Id", "Name", "Lastname", "Birthdate", "Phone", "Access" ])
        self.sheet.append_row([user_id, user_name, user_lastname, birthdate, phone, "",])

    def blockUser(self, user_id: str):
        cell = self.sheet.find(str(user_id))  
        if cell:
            self.sheet.update_cell(cell.row, 6, f"Запрет {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def unblockUser(self, user_id: str):
        cell = self.sheet.find(str(user_id))
        if cell:
            self.sheet.update_cell(cell.row, 6, "")

    def getUserAccess(self, user_id: str) -> str:

        cell = self.sheet.find(str(user_id))
        if cell:
            return self.sheet.cell(cell.row, 6).value
        return None