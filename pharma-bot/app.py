"""CLI chat:  python app.py   |   one-shot:  python app.py "هل بانادول متوفر؟" """
import sys

from bot.engine import PharmaBot


def main():
    bot = PharmaBot()
    if len(sys.argv) > 1:
        print(bot.ask(" ".join(sys.argv[1:])).text)
        return
    print("مساعد الصيدلية (Ctrl+C للخروج)")
    while True:
        try:
            q = input("\n❓ ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        print("\n🤖 " + bot.ask(q).text)


if __name__ == "__main__":
    main()
