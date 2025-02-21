from rushdb import RushDB
from telegram import Message


# USERS_ENTITY = "users"

#
""" 
class Repository:
    def __init__(self, token):
        self.db = RushDB(token)

    def __del__(self):
        self.db.close()

    def findUsersById(self, user_id: int):
        return self.db.records.find(
            {
                "labels": [USERS_ENTITY],
                "where": {"user_id": user_id},
            }
        )

    def createUser(self, user_id: int, first_name: str, last_name: str, chat_id: int):
        return self.db.records.create(
            USERS_ENTITY,
            {
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "chat_id": chat_id,
            },
        )

    def updateChatId(self, user_id: int, chat_id: int):
        users = self.findUsersById(user_id)
        if len(users) == 0:
            return None
        else:
            return self.db.records.update(
                users[0].id,
                {
                    "chat_id": chat_id,
                },
            )
""" 
#