"""程序入口"""

import ledger


def main():
    try:
        ledger.start()
    except KeyboardInterrupt:
        print("保存ing...")
        is_successful = ledger.save()
        if is_successful:
            print("保存成功")
        else:
            print("保存失败,空悲切")


if __name__ == "__main__":
    main()
