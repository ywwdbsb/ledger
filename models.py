"""Record 与 User 类"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Record:
    """单次记录 包含金额 说明文档和时间"""

    amount: Decimal  # 使用 Decimal
    doc: str
    created_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        init=False,
    )

    @classmethod
    def from_dict(cls, data: dict):
        record = cls(Decimal(data["amount"]), data["doc"])
        record.created_at = data["created_at"]
        return record


@dataclass
class User:
    """用户对象 每个用户拥有不同的记录"""

    name: str
    password: str

    # 这里也是 Decimal
    balance: Decimal = field(default_factory=Decimal, init=False)
    records: list[Record] = field(default_factory=list, init=False)

    @classmethod
    def from_dict(cls, data: dict):
        user = cls(data["name"], data["password"])
        user.balance = Decimal(data["balance"])
        user.records = [Record.from_dict(record) for record in data["records"]]
        return user

    def add_record(self, amount: Decimal, doc: str):
        record = Record(amount, doc)
        self.records.append(record)
        self.balance += amount

    def remove_record(self, index: int):
        record = self.records.pop(index - 1)
        self.balance -= record.amount
