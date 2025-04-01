from telegram import Message
import gspread
from gspread import Worksheet
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
        self.spreadsheet = self.client.open(spreadsheetName)
        self.sheet1 = self.spreadsheet.sheet1  # Первый лист
        self.sheet2 = self.spreadsheet.worksheet("Лист2")  # Второй лист
    def get_next_loc_id(self) -> int:
        loc_ids = self.sheet1.col_values(8)

        if len(loc_ids) <= 1:
            return 1

        loc_ids = [int(id) for id in loc_ids[1:] if id.isdigit()]
        if not loc_ids:
            return 1

        return max(loc_ids) + 1
    
    def add_comment_to_sheet2(self, loc_id: int, operation: str, stars: int, comment: str):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Добавляем новую строку с данными
        self.sheet2.append_row([loc_id, operation, stars, comment, current_time])

    def saveNewUser(
        self,
        user_id: str,
        user_name: str,
        user_lastname: str,
        birthdate: str,
        phone: str,
        gender: str,
    ):
        if self.sheet1.acell("A1").value == None:
            self.sheet1.append_row(["Id", "Name", "Lastname", "Birthdate", "Phone", "Access", "Stars", "Gender"])
        self.sheet1.append_row([user_id, user_name, user_lastname, birthdate, phone, "","", gender])

    def get_last_comments(self, user_id: int, limit: int = 10) -> list:
        try:
            data = self.sheet2.get_all_values()
        except Exception as e:
            return []

        # Фильтруем строки по ID
        filtered_data = [row for row in data[1:] if row[0] == str(user_id)]
        # Возвращаем последние 10 операций
        return filtered_data[-limit:]

    def blockUser(self, user_id: str):
        cell = self.sheet1.find(str(user_id))  
        if cell:
            self.sheet1.update_cell(cell.row, 6, f"Запрет {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def unblockUser(self, user_id: str):
        cell = self.sheet1.find(str(user_id))
        if cell:
            self.sheet1.update_cell(cell.row, 6, "")

    def getUserAccess(self, user_id: str) -> str:

        cell = self.sheet1.find(str(user_id))
        if cell:
            return self.sheet1.cell(cell.row, 6).value
        return None
    def getUserGender(self, user_id: str) -> str:
        cell = self.sheet1.find(str(user_id))
        if cell:
            return self.sheet1.cell(cell.row, 8).value
