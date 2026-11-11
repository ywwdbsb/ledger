"""程序主体"""

import json
import stat
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import utils

# 适用 pathlib 获取绝对路径
# 并将文件名替换 确保 ledger_data.json 在同级目录
DATA_FILE = Path(__file__).with_name("ledger_data.json")


@dataclass
class Record:
    """单次记录 包含金额 说明文档和时间"""

    amount: Decimal  # 使用 Decimal
    doc: str
    created_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y %m %d %H:%M:%S"),
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


@dataclass
class Ledger:
    """记账本 拥有不同用户"""

    now_user: User | None = field(default=None, init=False)
    users: list[User] = field(default_factory=list, init=False)

    def __post_init__(self):
        self._is_running = True

    def __get_user(self, name: str) -> User | None:
        for user in self.users:
            if user.name == name:
                return user

    @staticmethod
    def __is_password_correct(user: User) -> bool:
        times = 3
        while times > 0:
            password = input("请输入用户密码:")
            if utils.verify_password(password, user.password):
                return True
            times -= 1
            print(
                "密码不正确,请重试",
                f"还剩{times}次机会",
                sep="\n",
            )
        return False

    @staticmethod
    def __confirm(prompt: str) -> bool:
        choice = input(prompt)
        return choice.lower() == "y"

    @staticmethod
    def __login_page():
        print(
            "1.登录用户",
            "2.新建用户",
            "3.删除用户",
            "0.退出",
            sep="\n",
        )

    @staticmethod
    def __user_page():
        print(
            "1.查看记录",
            "2.增加记录",
            "3.删除记录",
            "4.保存记录",
            "5.退出登录",
            "0.退出",
            sep="\n",
        )

    def __quit(self):
        if self.__confirm("是否退出?(Y/N):"):
            self._is_running = False
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
                if self.now_user is None:
                    break
                if index <= 0 or index > len(self.now_user.records):
                    print("没有这个序号,请重试")
                    continue
                if self.__confirm("确认删除?(Y/N):"):
                    self.now_user.remove_record(index)
                    print("删除成功")
                    break
                else:
                    print("已取消删除")
            except ValueError:
                print("请输入数字")

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
            if user is None:
                if self.__confirm("没有这个用户,是否新建?(Y/N):"):
                    self.__create_(name)
                    break
                else:
                    continue
            if self.__is_password_correct(user):
                self.now_user = user
                print(f"欢迎回来,{user.name}")
                break
            print("密码错误,已退回主界面")

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
            if user is None:
                print("该用户不存在,请重试")
                continue
            if not self.__is_password_correct(user):
                print("你无权删除该用户")
                break
            if self.__confirm("确认删除?(Y/N):"):
                self.users.remove(user)
                print("删除成功")
            else:
                print("已取消删除")
            break

    def __save(self):
        try:
            # 解除文件只读
            if DATA_FILE.exists():
                DATA_FILE.chmod(stat.S_IWRITE | stat.S_IREAD)

            data = [asdict(user) for user in self.users]
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4, default=str)

        except PermissionError:
            print(f"无法保存到 {DATA_FILE.name} ,可能被其他程序占用,请退出重试")
        except OSError as error:
            print(f"保存到 {DATA_FILE.name} 失败:{error}")
        else:
            print(f"成功保存到 {DATA_FILE.name}")
            # 写入后立即恢复文件只读
            DATA_FILE.chmod(stat.S_IREAD)

    def __load(self):
        try:
            with open(DATA_FILE, encoding="utf-8") as file:
                data = json.load(file)
                self.users = [User.from_dict(user) for user in data]
        except FileNotFoundError:
            print("欢迎首次使用")
        except json.JSONDecodeError:
            print(f"警告: {DATA_FILE.name} 已损坏,无法读取")
        except (ValueError, KeyError, InvalidOperation):
            print(f"警告: {DATA_FILE.name} 数据缺失或格式错误,部分数据可能无法读取")
        else:
            print(f"成功从 {DATA_FILE.name} 中读取数据")

    def start(self):
        self.__load()
        while self._is_running:
            if self.now_user is None:
                self.__login_page()
                choice = input("请输入选择:")
                match choice:
                    case "1":
                        self.__login()
                    case "2":
                        self.__create()
                    case "3":
                        self.__remove()
                    case "0":
                        self.__quit()
                    case _:
                        print("输入有误,请重试")
            else:
                self.__user_page()
                choice = input("请输入选择:")
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
                    case "0":
                        self.__quit()
                    case _:
                        print("输入有误,请重试")
            print()  # 细节空行 更好看
