"""CLI chat:  python app.py   |   one-shot:  python app.py "كم نسبة الغياب؟" """
import sys

from rag.agent import Assistant


def show(a):
    print(f"\n🤖 {a.text}")
    if a.sources:
        print("📚 " + " | ".join(a.sources))
    print(f"   [mode={a.mode} score={a.score:.2f}]\n")


def main():
    bot = Assistant()
    if len(sys.argv) > 1:
        show(bot.ask(" ".join(sys.argv[1:])))
        return
    print("مساعد دليل الطالب (Ctrl+C للخروج)")
    while True:
        try:
            q = input("❓ ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        show(bot.ask(q))


if __name__ == "__main__":
    main()
