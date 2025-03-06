# from rushdb import RushDB
from telegram import Message
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# USERS_ENTITY = "users"

#


class Repository:
    def __init__(self, token):
        self.token = token


#         self.db = RushDB(token)

#     def __del__(self):
#         self.db.close()

#     def findUsersById(self, user_id: int):
#         return self.db.records.find(
#             {
#                 "labels": [USERS_ENTITY],
#                 "where": {"user_id": user_id},
#             }
#         )

#     def createUser(self, user_id: int, first_name: str, last_name: str, chat_id: int):
#         return self.db.records.create(
#             USERS_ENTITY,
#             {
#                 "user_id": user_id,
#                 "first_name": first_name,
#                 "last_name": last_name,
#                 "chat_id": chat_id,
#             },
#         )

#     def updateChatId(self, user_id: int, chat_id: int):
#         users = self.findUsersById(user_id)
#         if len(users) == 0:
#             return None
#         else:
#             return self.db.records.update(
#                 users[0].id,
#                 {
#                     "chat_id": chat_id,
#                 },
#             )


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
        self, user_id: str, user_name: str, user_lastname: str, birthdate: str
    ):
        if self.sheet.acell("A1").value == None:
            self.sheet.append_row(["Id", "Name", "Lastname", "Birthdate"])
        self.sheet.append_row([user_id, user_name, user_lastname, birthdate])
