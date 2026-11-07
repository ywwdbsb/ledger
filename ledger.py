import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation


@dataclass
class Record:
    amount: Decimal
    doc: str
    id: int | None = field(default=None)
    created_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y %m %d %H:%M:%S"), init=False
    )


@dataclass
class User:
    name: str
    password: str
    balance: Decimal = field(default_factory=Decimal, init=False)
    next_id: int = field(default=1, init=False)
    records: list[Record] = field(default_factory=list, init=False)

    def add_record(self):
        while True:
            try:
                amount = Decimal(input("请输入金额:"))
                break
            except InvalidOperation:
                print("请输入有效数字")
        doc = input("请输入说明:")
        record = Record(amount, doc)
        record.id = self.next_id
        self.next_id += 1
        self.records.append(record)
        self.balance += amount
        print("添加成功")

    def remove_record(self):
        while True:
            try:
                id_ = int(input("请输入id:"))
            except ValueError:
                print("id必须为正整数")
                continue
            for record in self.records:
                if record.id == id_:
                    self.records.remove(record)
                    self.balance -= record.amount
                    print("删除成功")
                    return
            print("没有这个id,请重试")

    def print_info(self):
        for record in self.records:
            print(record)
        print(f"余额:{self.balance}")


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

    def __interface(self):
        if self.now_user is None:
            print("1.登录用户", "2.新建用户", "3.删除用户", "4.退出", sep="\n")
        else:
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

    def __login(self):
        while True:
            name = input("请输入用户名:")
            user = self.__get_user(name)
            if user is not None:
                while True:
                    password = input("请输入用户密码:")
                    if user.password == password:
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
        new_user = User(name, password)
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
        with open("ledger_data.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4, default=str)

    def __load(self):
        try:
            with open("ledger_data.json", encoding="utf-8") as file:
                data = json.load(file)
                for user in data:
                    records = []
                    for record in user["records"]:
                        record_res = Record(Decimal(record["amount"]), record["doc"])
                        record_res.id = record["id"]
                        record_res.created_at = record["created_at"]
                        records.append(record_res)
                    user_res = User(user["name"], user["password"])
                    user_res.balance = Decimal(user["balance"])
                    user_res.next_id = user.get("next_id", 1)
                    user_res.records = records
                    self.users.append(user_res)
        except FileNotFoundError:
            print("欢迎首次使用")
        except json.JSONDecodeError:
            print("警告:json已损坏,无法读取")
        except ValueError, KeyError:
            print("警告:json数据缺失或格式错误,部分数据可能无法读取")

    def start(self):
        self.__load()
        while self._if_running:
            self.__interface()
            choice = input()
            if self.now_user is None:
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
                match choice:
                    case "1":
                        self.now_user.print_info()
                    case "2":
                        self.now_user.add_record()
                    case "3":
                        self.now_user.remove_record()
                    case "4":
                        self.__save()
                    case "5":
                        self.now_user = None
                    case "6":
                        self.__quit()
                    case _:
                        print("输入有误,请重试")


if __name__ == "__main__":
    ledger = Ledger()
    ledger.start()
