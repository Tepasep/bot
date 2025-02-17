from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: Optional[int]
    name: str
    surname: str
    chatID: str
    telephone: str
    balance: float
    dr: str
    dcreate: str
    dupdate: Optional[str]
    ddelete: Optional[str]

@dataclass
class Operation:
    id: Optional[int]
    user_id: int
    datetime: str
    stars: int
    type: str
    comment: Optional[str]