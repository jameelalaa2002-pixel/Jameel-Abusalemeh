"""Rule-based pharmacy assistant: medicine availability, pharmacies, doctors.

Flow: emergency -> medical-advice refusal -> doctor -> medicine -> pharmacy -> help.
The bot only reports data from the JSON files; it never gives medical advice.
"""
import difflib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .normalize import normalize

DATA = Path(__file__).resolve().parent.parent / "data"
KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]  # datetime.weekday() order
DAY_AR = {"mon": "الاثنين", "tue": "الثلاثاء", "wed": "الأربعاء", "thu": "الخميس",
          "fri": "الجمعة", "sat": "السبت", "sun": "الأحد"}
DAY_WORDS = {"mon": ["الاثنين", "الاتنين"], "tue": ["الثلاثاء", "التلاتاء"], "wed": ["الأربعاء"],
             "thu": ["الخميس"], "fri": ["الجمعة"], "sat": ["السبت"], "sun": ["الأحد"]}

EMERGENCY = ["طوارئ", "اسعاف", "مسمم", "تسمم", "ما بقدر اتنفس", "الم في الصدر", "الم صدر",
             "اغماء", "نزيف", "جرعه زايده", "جرعة زايدة"]
ADVICE = ["جرعه", "جرعة", "كم حبه", "كم حبة", "كم مره", "كم مرة", "تداخل", "يتعارض",
          "اعراض جانبيه", "شو اخذ", "ايش اخذ", "شو بياخد", "وصفلي", "انصحني", "حامل", "رضاعه",
          "بيضر", "امن ل", "آمن ل"]
DOCTOR = ["دكتور", "دكاتره", "طبيب", "اطباء", "عياده", "حكيم"]
PHARMACY = ["صيدليه", "صيدليات", "مناوبه", "مفتوح", "دوام", "ساعات", "وين"]
HELLO = ["مرحبا", "اهلا", "هلا", "السلام", "صباح", "مساء", "ساعدني", "مساعده", "شو بتعمل"]
DRUG_WORDS = ["دواء", "دوا", "علاج", "حبوب", "حبه", "شراب", "متوفر", "موجود", "عندكم"]

FOOTER = "\n\nℹ️ المعلومات حسب آخر تحديث، الأفضل تتصل قبل ما تروح 📞"


@dataclass
class Reply:
    text: str
    intent: str


def _n(words):
    return [normalize(w) for w in words]


def _has(q: str, words) -> bool:
    return any(w in q for w in _n(words))


def _mins(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class PharmaBot:
    def __init__(self, data_dir: Path | None = None):
        global DATA
        if data_dir:
            DATA = Path(data_dir)
        self.pharmacies = {p["id"]: p for p in _load("pharmacies.json")["pharmacies"]}
        self.medicines = _load("medicines.json")["medicines"]
        stock = _load("stock.json")
        self.stock, self.updated = stock["stock"], stock["updated"]
        self.doctors = _load("doctors.json")["doctors"]
        self.aliases = [(normalize(a), m) for m in self.medicines for a in m["aliases"]]

    # ---------- helpers ----------
    @staticmethod
    def is_open(ph: dict, now: datetime) -> bool:
        if ph.get("is_24h"):
            return True
        o, c, t = _mins(ph["open"]), _mins(ph["close"]), now.hour * 60 + now.minute
        return o <= t < c if o < c else (t >= o or t < c)

    def find_medicine(self, q: str):
        for alias, med in self.aliases:
            if len(alias) >= 3 and alias in q:
                return med
        names = [a for a, _ in self.aliases]
        for tok in q.split():
            if len(tok) >= 4:
                close = difflib.get_close_matches(tok, names, n=1, cutoff=0.8)
                if close:
                    return next(m for a, m in self.aliases if a == close[0])
        return None

    @staticmethod
    def target_day(q: str, now: datetime) -> str:
        for key, words in DAY_WORDS.items():
            if _has(q, words):
                return key
        if _has(q, ["بكرا", "غدا", "بكره"]):
            return KEYS[(now + timedelta(days=1)).weekday()]
        return KEYS[now.weekday()]

    # ---------- intents ----------
    def ask(self, question: str, now: datetime | None = None) -> Reply:
        now = now or datetime.now()
        q = normalize(question)
        if not q:
            return Reply("اكتب سؤالك أول 🙂", "empty")
        if _has(q, EMERGENCY):
            return Reply("🚨 هاي حالة طارئة. اتصل فوراً بالطوارئ على 911 أو روح لأقرب مستشفى، "
                         "ولا تستنى الرد مني.", "emergency")
        if _has(q, ADVICE):
            return Reply("ما بقدر أحكي عن الجرعات أو أنصح بدواء معيّن 🙏 هاد قرار الطبيب أو الصيدلاني. "
                         "بقدر أقولك وين الدواء متوفر أو متى الدكتور موجود.\n"
                         "اسأل الصيدلاني أو الدكتور مباشرة.", "advice")
        if _has(q, DOCTOR):
            return self.doctors_reply(q, now)
        med = self.find_medicine(q)
        if med:
            return self.medicine_reply(med, now)
        if _has(q, PHARMACY):
            return self.pharmacies_reply(q, now)
        if _has(q, DRUG_WORDS):
            return Reply("ما عرفت اسم الدواء 🤔 وما بقدر أنصح بدواء معيّن، هاد قرار الطبيب أو الصيدلاني.\n"
                         "إذا بتعرف الاسم التجاري اكتبه وبقولك وين متوفر.", "medicine_unknown")
        if _has(q, HELLO):
            return Reply(self.help_text(), "help")
        return Reply("ما فهمت سؤالك 🤷\n" + self.help_text(), "unknown")

    @staticmethod
    def help_text() -> str:
        return ("أهلين! 👋 بقدر أساعدك بـ:\n"
                "💊 توفر دواء (مثلاً: هل بانادول متوفر؟)\n"
                "🏥 الصيدليات المفتوحة ومواقعها (مثلاً: أي صيدلية مفتوحة هلأ؟)\n"
                "👨‍⚕️ الدكاتره ومواعيدهم (مثلاً: في دكتور أطفال اليوم؟)")

    def medicine_reply(self, med: dict, now: datetime) -> Reply:
        rows = []
        for pid, items in self.stock.items():
            item = items.get(med["id"])
            if item and item["qty"] > 0:
                rows.append((pid, item))
        head = f"💊 {med['name']} ({med['form']})"
        head += "\n⚠️ بدّه وصفة طبيب" if med["rx"] else "\n✅ بدون وصفة"
        if not rows:
            phones = "\n".join(f"📞 {p['name']}: {p['phone']}" for p in self.pharmacies.values())
            return Reply(f"{head}\n\n❌ مش متوفر حالياً بأي صيدلية بالمنطقة (تحديث {self.updated}).\n"
                         f"جرّب تتصل:\n{phones}", "medicine_out")
        rows.sort(key=lambda r: (not self.is_open(self.pharmacies[r[0]], now), r[1]["price"]))
        lines = [head, "\nمتوفر في:"]
        for pid, item in rows:
            ph = self.pharmacies[pid]
            state = "🟢 مفتوحة هلأ" if self.is_open(ph, now) else "🔴 مسكّرة هلأ"
            lines.append(f"• {ph['name']}: {item['price']:.2f} د.أ، {item['qty']} علبة، {state}\n"
                         f"   📍 {ph['address']} | 📞 {ph['phone']}")
        return Reply("\n".join(lines) + FOOTER + f"\n(آخر تحديث: {self.updated})", "medicine")

    def pharmacies_reply(self, q: str, now: datetime) -> Reply:
        want_open = _has(q, ["مفتوح", "هلا", "الان", "الحين", "مناوبه", "24"])
        items = [p for p in self.pharmacies.values()
                 if not want_open or self.is_open(p, now)]
        if _has(q, ["مناوبه", "24"]):
            items = [p for p in items if p.get("is_24h")] or items
        if not items:
            return Reply("🔴 ما في صيدلية مفتوحة هلأ حسب البيانات." + FOOTER, "pharmacy_none")
        lines = ["🏥 الصيدليات" + (" المفتوحة هلأ:" if want_open else " بالمنطقة:")]
        for p in items:
            hours = "24 ساعة" if p.get("is_24h") else f"{p['open']} - {p['close']}"
            state = "🟢" if self.is_open(p, now) else "🔴"
            lines.append(f"• {state} {p['name']}: {hours}\n   📍 {p['address']} | 📞 {p['phone']}")
        return Reply("\n".join(lines) + FOOTER, "pharmacy")

    def doctors_reply(self, q: str, now: datetime) -> Reply:
        day = self.target_day(q, now)
        spec = [d for d in self.doctors if any(normalize(k) in q for k in d["keys"])]
        pool = spec or self.doctors
        avail = [d for d in pool if day in d["days"]]
        label = "اليوم" if day == KEYS[now.weekday()] else f"يوم {DAY_AR[day]}"
        if not avail:
            lines = [f"❌ ما في دكتور {pool[0]['specialty'] if spec else ''} {label}.", "\nمواعيدهم:"]
            for d in pool:
                lines.append(f"• {d['name']} ({d['specialty']}): "
                             + "، ".join(DAY_AR[x] for x in d["days"]) + f" {d['from']}-{d['to']}")
            return Reply("\n".join(lines) + FOOTER, "doctor_none")
        lines = [f"👨‍⚕️ الدكاتره المتوفرين {label} ({DAY_AR[day]}):"]
        for d in avail:
            lines.append(f"• {d['name']} ({d['specialty']}): {d['from']} - {d['to']}\n"
                         f"   📍 {d['clinic']} | 📞 {d['phone']}")
        return Reply("\n".join(lines) + "\n\nℹ️ اتصل واحجز موعد قبل ما تروح 📞", "doctor")
