from datetime import datetime
from ..domain.models import User, Operation
from ..data.repositories import UserRepository, OperationRepository

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.op_repo = OperationRepository()

    def add_user(self, name, surname, chatID, telephone, dr):
        user = User(None, name, surname, chatID, telephone, 0.0, dr, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), None, None)
        self.user_repo.add_user(user)
        return f"Пользователь {name} {surname} успешно добавлен."

    def add_stars(self, user_id, stars, comment):
        datetime_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        operation = Operation(None, user_id, datetime_now, stars, 'пополнение', comment)
        self.op_repo.add_operation(operation)
        return f"Начислено {stars} звезд пользователю {user_id}."