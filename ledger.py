import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import utils

DATA_FILE = Path(__file__).with_name("ledger_data.json")


@dataclass
class Record:
    amount: Decimal
    doc: str
    created_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y %m %d %H:%M:%S"), init=False
    )

    @classmethod
    def from_dict(cls, data: dict):
        record = cls(Decimal(data["amount"]), data["doc"])
        record.created_at = data["created_at"]
        return record


@dataclass
class User:
    name: str
    password: str
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


@dataclass
class Ledger:
    now_user: User | None = field(default=None, init=False)
    users: list[User] = field(default_factory=list, init=False)

    def __post_init__(self):
        self._if_running = True

    def __get_user(self, name: str) -> User | None:
        for user in self.users:
            if user.name == name:
                return user

    @staticmethod
    def __login_page():
        print("1.登录用户", "2.新建用户", "3.删除用户", "4.退出", sep="\n")

    @staticmethod
    def __user_page():
        print(
            "1.查看记录",
            "2.增加记录",
            "3.删除记录",
            "4.保存记录",
            "5.退出登录",
            "6.退出",
            sep="\n",
        )

    def __quit(self):
        choice = input("是否退出?(Y/N):")
        if choice.lower() == "y":
            self._if_running = False
            print("拜拜")
            self.__save()

    def __add_user_record(self):
        while True:
            try:
                amount = Decimal(input("请输入金额:"))
                break
            except InvalidOperation:
                print("请输入有效数字")
        doc = input("请输入说明:")
        if self.now_user is not None:
            self.now_user.add_record(amount, doc)
        print("添加成功")

    def __remove_user_record(self):
        while True:
            try:
                index = int(input("请输入序号:"))
                if index <= 0:
                    raise ValueError
                if self.now_user is not None:
                    self.now_user.remove_record(index)
                print("删除成功")
                break
            except ValueError:
                print("序号必须为正整数")
            except IndexError:
                print("没有这个序号,请重试")

    def __print_info(self):
        if self.now_user is not None:
            enumeration = enumerate(self.now_user.records, start=1)
            for index, record in enumeration:
                print(
                    f"{index} | {record.created_at} | {record.doc} | {record.amount:+.2f}"
                )
            print(f"余额:{self.now_user.balance:.2f}")

    def __login(self):
        while True:
            name = input("请输入用户名:")
            user = self.__get_user(name)
            if user is not None:
                while True:
                    password = input("请输入用户密码:")
                    if utils.verify_password(password, user.password):
                        self.now_user = user
                        print(f"欢迎回来,{user.name}")
                        return
                    else:
                        print("密码不正确,请重试")
            else:
                print("没有这个用户,是否新建?")
                user_input = input("(Y/N):")
                if user_input.lower() == "y":
                    self.__create_(name)
                    return

    def __create_(self, name: str):
        password = input("请输入用户密码:")
        password_hash = utils.hash_password(password)
        new_user = User(name, password_hash)
        self.users.append(new_user)
        self.now_user = new_user
        print(f"欢迎,{new_user.name}")

    def __create(self):
        while True:
            name = input("请输入用户名:")
            user = self.__get_user(name)
            if user is None:
                self.__create_(name)
                break
            else:
                print("该用户已存在,请重试")

    def __remove(self):
        while True:
            name = input("请输入用户名:")
            user = self.__get_user(name)
            if user is not None:
                self.users.remove(user)
                break
            else:
                print("该用户不存在,请重试")

    def __save(self):
        data = [asdict(user) for user in self.users]
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4, default=str)

    def __load(self):
        try:
            with open(DATA_FILE, encoding="utf-8") as file:
                data = json.load(file)
                self.users = [User.from_dict(user) for user in data]
        except FileNotFoundError:
            print("欢迎首次使用")
        except json.JSONDecodeError:
            print("警告:json已损坏,无法读取")
        except (ValueError, KeyError):
            print("警告:json数据缺失或格式错误,部分数据可能无法读取")

    def start(self):
        self.__load()
        while self._if_running:
            if self.now_user is None:
                self.__login_page()
                choice = input()
                match choice:
                    case "1":
                        self.__login()
                    case "2":
                        self.__create()
                    case "3":
                        self.__remove()
                    case "4":
                        self.__quit()
                    case _:
                        print("输入有误,请重试")
            else:
                self.__user_page()
                choice = input()
                match choice:
                    case "1":
                        self.__print_info()
                    case "2":
                        self.__add_user_record()
                    case "3":
                        self.__remove_user_record()
                    case "4":
                        self.__save()
                    case "5":
                        self.now_user = None
                    case "6":
                        self.__quit()
                    case _:
                        print("输入有误,请重试")
            print()
