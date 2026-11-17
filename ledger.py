"""记账本 拥有不同用户"""

import json
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

import utils
from models import User

# 适用 pathlib 获取绝对路径
# 并将文件名替换 确保 ledger_data.json 在同级目录
DATA_FILE = Path(__file__).with_name("ledger_data.json")


@dataclass
class Ledger:
    _now_user: User | None = field(default=None, init=False)
    _users: list[User] = field(default_factory=list, init=False)
    _is_running: bool = field(default=True, init=False)

    def _get_user(self, name: str) -> User | None:
        for user in self._users:
            if user.name == name:
                return user

    @staticmethod
    def _is_password_correct(user: User) -> bool:
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
    def _confirm(prompt: str) -> bool:
        choice = input(prompt)
        return choice.lower() == "y"

    @staticmethod
    def _login_page():
        print(
            "1.登录用户",
            "2.新建用户",
            "3.删除用户",
            "0.退出",
            sep="\n",
        )

    @staticmethod
    def _user_page():
        print(
            "1.查看记录",
            "2.增加记录",
            "3.删除记录",
            "4.退出登录",
            "0.退出",
            sep="\n",
        )

    def _quit(self):
        if not self._confirm("是否退出?(Y/N):"):
            return
        if not self.save() and not self._confirm(
            "保存失败,仍然退出?未保存的更改将丢失(Y/N)"
        ):
            return
        self._is_running = False
        print("拜拜")

    def _add_user_record(self):
        while True:
            try:
                amount = Decimal(input("请输入金额:"))
                if not amount.is_finite():
                    print("金额必须是有限数字")
                    continue
                break
            except InvalidOperation:
                print("请输入有效数字")
        doc = input("请输入说明:")
        if self._now_user is not None:
            self._now_user.add_record(amount, doc)
            print("添加成功")

    def _remove_user_record(self):
        while True:
            try:
                if self._now_user is None:
                    break
                index = int(input("请输入序号:"))
                if index <= 0 or index > len(self._now_user.records):
                    print("没有这个序号,请重试")
                    continue
                if self._confirm("确认删除?(Y/N):"):
                    self._now_user.remove_record(index)
                    print("删除成功")
                    break
                else:
                    print("已取消删除")
                    break
            except ValueError:
                print("请输入数字")

    def _print_info(self):
        if self._now_user is not None:
            enumeration = enumerate(self._now_user.records, start=1)
            for index, record in enumeration:
                print(
                    f"{index} | {record.amount:+.2f} | {record.doc} | {record.created_at}"
                )
            print(f"余额:{self._now_user.balance:.2f}")

    def _login(self):
        while True:
            name = input("请输入用户名:")
            user = self._get_user(name)
            if user is None:
                if self._confirm("没有这个用户,是否新建?(Y/N):"):
                    self._create_user(name)
                    break
                else:
                    continue
            if self._is_password_correct(user):
                self._now_user = user
                print(f"欢迎回来,{user.name}")
                break
            print("密码错误,已退回主界面")

    def _create_user(self, name: str):
        while True:
            password = input("请输入用户密码:")
            second_password = input("请再次输入:")
            if second_password != password:
                print("两次密码不一致")
            else:
                break
        password_hash = utils.hash_password(password)
        new_user = User(name, password_hash)
        self._users.append(new_user)
        self._now_user = new_user
        print(f"欢迎,{new_user.name}")

    def _create(self):
        while True:
            name = input("请输入用户名:")
            user = self._get_user(name)
            if user is None:
                self._create_user(name)
                break
            else:
                print("该用户已存在,请重试")

    def _remove(self):
        while True:
            name = input("请输入用户名:")
            user = self._get_user(name)
            if user is None:
                print("该用户不存在,请重试")
                continue
            if not self._is_password_correct(user):
                print("你无权删除该用户")
                break
            if self._confirm("确认删除?(Y/N):"):
                self._users.remove(user)
                print("删除成功")
            else:
                print("已取消删除")
            break

    def save(self) -> bool:
        # 先写入临时文件中 再存入 json
        # 不然写 json 时出错就炸了
        tmp = DATA_FILE.with_suffix(".json.tmp")
        try:
            data = [asdict(user) for user in self._users]
            with open(tmp, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4, default=str)
            tmp.replace(DATA_FILE)
        except PermissionError:
            print(f"无法保存到 {DATA_FILE.name} ,可能被其他程序占用,请退出重试")
        except OSError as error:
            print(f"保存到 {DATA_FILE.name} 失败:{error}")
        else:
            return True
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
        return False

    def _load(self):
        try:
            with open(DATA_FILE, encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            print("欢迎首次使用")
            return
        except json.JSONDecodeError:
            print(f"警告: {DATA_FILE.name} 已损坏,无法读取")
            return

        if not isinstance(data, list):
            print(f"警告: {DATA_FILE.name} 类型错误,无法读取")
            return

        _users = []
        failed_times = 0
        for user_data in data:
            try:
                user = User.from_dict(user_data)
                _users.append(user)
            except (ValueError, KeyError, InvalidOperation, TypeError) as error:
                print(
                    f"警告: {DATA_FILE.name} 数据缺失或格式错误:{error},部分数据可能无法读取"
                )
                failed_times += 1

        if failed_times:
            print(f"警告: {DATA_FILE.name}中共{failed_times}条数据损坏,无法读取")
            backup = DATA_FILE.with_suffix(".corrupted.json")
            DATA_FILE.replace(backup)
            print(f"损坏数据已备份至{backup.name}")
        else:
            print(f"成功从{DATA_FILE.name}中读取{len(_users)}条数据")

    def start(self):
        self._load()
        while self._is_running:
            if self._now_user is None:
                self._login_page()
                choice = input("请输入选择:")
                match choice:
                    case "1":
                        self._login()
                        self.save()
                    case "2":
                        self._create()
                        self.save()
                    case "3":
                        self._remove()
                        self.save()
                    case "0":
                        self._quit()
                    case _:
                        print("输入有误,请重试")
            else:
                self._user_page()
                choice = input("请输入选择:")
                match choice:
                    case "1":
                        self._print_info()
                    case "2":
                        self._add_user_record()
                        self.save()
                    case "3":
                        self._remove_user_record()
                        self.save()
                    case "4":
                        self._now_user = None
                    case "0":
                        self._quit()
                    case _:
                        print("输入有误,请重试")
            print()  # 细节空行 更好看
