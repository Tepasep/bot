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
    
    def add_comment_to_sheet2(self, loc_id: int, comment: str):
        headers = self.sheet2.row_values(1)
        if str(loc_id) in headers:
            col_index = headers.index(str(loc_id)) + 1
        else:
            col_index = len(headers) + 1
            self.sheet2.update_cell(1, col_index, str(loc_id))
        next_row = len(self.sheet2.col_values(col_index)) + 1
        self.sheet2.update_cell(next_row, col_index, comment)

    def saveNewUser(
        self,
        user_id: str,
        user_name: str,
        user_lastname: str,
        birthdate: str,
        phone: str,
    ):
        if self.sheet1.acell("A1").value == None:
            self.sheet1.append_row(["Id", "Name", "Lastname", "Birthdate", "Phone", "Access", "LocID" ])
        loc_id = self.get_next_loc_id()
        self.sheet1.append_row([user_id, user_name, user_lastname, birthdate, phone, "","", str(loc_id),])
        self.sheet2.update_cell(1, len(self.sheet2.row_values(1)) + 1, str(loc_id))

    def get_last_comments(self, loc_id: int, limit: int = 10) -> list:
        headers = self.sheet2.row_values(1)
        if str(loc_id) not in headers:
            return []
        col_index = headers.index(str(loc_id)) + 1
        comments = self.sheet2.col_values(col_index)[1:]
        return comments[-limit:]

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
