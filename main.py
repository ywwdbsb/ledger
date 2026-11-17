"""程序入口"""

from ledger import Ledger


def main():
    ledger_obj = Ledger()
    try:
        ledger_obj.start()
    except KeyboardInterrupt:
        print("保存ing...")
        save_successfully = ledger_obj.save()
        if save_successfully:
            print("保存成功")
        else:
            print("保存失败,空悲切")


if __name__ == "__main__":
    main()
