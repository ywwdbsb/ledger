"""记账本 拥有不同用户"""

import json
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

import utils
from models import User

# 适用 pathlib 获取绝对路径
# 并将文件名替换 确保 ledger_data.json 在同级目录
DATA_FILE = Path(__file__).with_name("ledger_data.json")

_now_user: User | None = None
_users: list[User] = []
_is_running: bool = True


def _get_user(name: str) -> User | None:
    for user in _users:
        if user.name == name:
            return user


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


def _confirm(prompt: str) -> bool:
    choice = input(prompt)
    return choice.lower() == "y"


def _login_page():
    print(
        "1.登录用户",
        "2.新建用户",
        "3.删除用户",
        "0.退出",
        sep="\n",
    )


def _user_page():
    print(
        "1.查看记录",
        "2.增加记录",
        "3.删除记录",
        "4.退出登录",
        "0.退出",
        sep="\n",
    )


def _quit():
    global _is_running
    if not _confirm("是否退出?(Y/N):"):
        return
    if not save() and not _confirm("保存失败,仍然退出?未保存的更改将丢失(Y/N)"):
        return
    _is_running = False
    print("拜拜")


def _add_user_record():
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
    if _now_user is not None:
        _now_user.add_record(amount, doc)
        print("添加成功")


def _remove_user_record():
    while True:
        try:
            index = int(input("请输入序号:"))
            if _now_user is None:
                break
            if index <= 0 or index > len(_now_user.records):
                print("没有这个序号,请重试")
                continue
            if _confirm("确认删除?(Y/N):"):
                _now_user.remove_record(index)
                print("删除成功")
                break
            else:
                print("已取消删除")
                break
        except ValueError:
            print("请输入数字")


def _print_info():
    if _now_user is not None:
        enumeration = enumerate(_now_user.records, start=1)
        for index, record in enumeration:
            print(
                f"{index} | {record.created_at} | {record.doc} | {record.amount:+.2f}"
            )
        print(f"余额:{_now_user.balance:.2f}")


def _login():
    global _now_user
    while True:
        name = input("请输入用户名:")
        user = _get_user(name)
        if user is None:
            if _confirm("没有这个用户,是否新建?(Y/N):"):
                _create_user(name)
                break
            else:
                continue
        if _is_password_correct(user):
            _now_user = user
            print(f"欢迎回来,{user.name}")
            break
        print("密码错误,已退回主界面")


def _create_user(name: str):
    global _now_user
    while True:
        password = input("请输入用户密码:")
        second_password = input("请再次输入:")
        if second_password != password:
            print("两次密码不一致")
        else:
            break
    password_hash = utils.hash_password(password)
    new_user = User(name, password_hash)
    _users.append(new_user)
    _now_user = new_user
    print(f"欢迎,{new_user.name}")


def _create():
    while True:
        name = input("请输入用户名:")
        user = _get_user(name)
        if user is None:
            _create_user(name)
            break
        else:
            print("该用户已存在,请重试")


def _remove():
    while True:
        name = input("请输入用户名:")
        user = _get_user(name)
        if user is None:
            print("该用户不存在,请重试")
            continue
        if not _is_password_correct(user):
            print("你无权删除该用户")
            break
        if _confirm("确认删除?(Y/N):"):
            _users.remove(user)
            print("删除成功")
        else:
            print("已取消删除")
        break


def save() -> bool:
    # 先写入临时文件中 再存入 json
    tmp = DATA_FILE.with_suffix(".json.tmp")
    try:
        data = [asdict(user) for user in _users]
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


def _load():
    global _users
    try:
        with open(DATA_FILE, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("欢迎首次使用")
        return
    except json.JSONDecodeError:
        print(f"警告: {DATA_FILE.name} 已损坏,无法读取")
        return

    _users = []
    failed_times = 0
    for user_data in data:
        try:
            user = User.from_dict(user_data)
            _users.append(user)
        except (ValueError, KeyError, InvalidOperation, TypeError) as error:
            print(
                f"警告:{DATA_FILE.name} 数据缺失或格式错误:{error},部分数据可能无法读取"
            )
            failed_times += 1

    if failed_times:
        print(f"警告:{DATA_FILE.name}中共{failed_times}条数据损坏,无法读取")
    else:
        print(f"成功从{DATA_FILE.name}中读取{len(_users)}条数据")


def start():
    global _now_user
    _load()
    while _is_running:
        if _now_user is None:
            _login_page()
            choice = input("请输入选择:")
            match choice:
                case "1":
                    _login()
                case "2":
                    _create()
                    save()
                case "3":
                    _remove()
                    save()
                case "0":
                    _quit()
                case _:
                    print("输入有误,请重试")
        else:
            _user_page()
            choice = input("请输入选择:")
            match choice:
                case "1":
                    _print_info()
                case "2":
                    _add_user_record()
                    save()
                case "3":
                    _remove_user_record()
                    save()
                case "4":
                    _now_user = None
                case "0":
                    _quit()
                case _:
                    print("输入有误,请重试")
        print()  # 细节空行 更好看
