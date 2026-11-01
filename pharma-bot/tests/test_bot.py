import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.engine import PharmaBot  # noqa: E402

NOON_SUNDAY = datetime(2026, 11, 1, 12, 0)     # Sunday 12:00
LATE_NIGHT = datetime(2026, 11, 2, 2, 0)       # Monday 02:00
FRIDAY = datetime(2026, 11, 6, 12, 0)


class TestBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = PharmaBot()

    def ask(self, q, now=NOON_SUNDAY):
        return self.bot.ask(q, now)

    def test_medicine_in_stock(self):
        r = self.ask("هل بانادول متوفر؟")
        self.assertEqual(r.intent, "medicine")
        self.assertIn("صيدلية النخيل", r.text)
        self.assertIn("1.50", r.text)

    def test_english_name_and_typo(self):
        self.assertEqual(self.ask("panadol").intent, "medicine")
        self.assertEqual(self.ask("عندكم بنادول؟").intent, "medicine")

    def test_out_of_stock_everywhere(self):
        pharmacies_with_stock = [p for p in self.bot.stock.values() if p.get("ventolin")]
        self.assertEqual(pharmacies_with_stock, [])  # sanity: id is salbutamol, not ventolin
        r = self.ask("فنتولين")
        self.assertIn("صيدلية الليل", r.text)

    def test_zero_qty_is_not_listed(self):
        r = self.ask("انسولين")
        self.assertNotIn("صيدلية الأمل", r.text)  # qty 0 there
        self.assertIn("صيدلية الليل", r.text)

    def test_prescription_flag(self):
        self.assertIn("وصفة", self.ask("اموكسيسيلين").text)

    def test_open_pharmacies_at_night(self):
        r = self.ask("أي صيدلية مفتوحة هلأ؟", LATE_NIGHT)
        self.assertIn("صيدلية الليل", r.text)
        self.assertNotIn("صيدلية النخيل", r.text)

    def test_doctor_today(self):
        r = self.ask("في دكتور أطفال اليوم؟")  # Sunday: pediatrician works
        self.assertIn("ليلى حداد", r.text)

    def test_doctor_not_available(self):
        r = self.ask("دكتور اسنان اليوم", NOON_SUNDAY)  # dentist: no Sunday
        self.assertEqual(r.intent, "doctor_none")

    def test_doctor_named_day(self):
        self.assertIn("هاني الخطيب", self.ask("دكتور اسنان يوم الاثنين").text)

    def test_friday_no_doctors(self):
        self.assertEqual(self.ask("دكتور عام", FRIDAY).intent, "doctor_none")

    def test_dosage_refused(self):
        self.assertEqual(self.ask("كم حبة بانادول بياخد الطفل؟").intent, "advice")
        self.assertEqual(self.ask("شو اخذ للصداع").intent, "advice")

    def test_emergency(self):
        self.assertEqual(self.ask("ما بقدر اتنفس").intent, "emergency")

    def test_unknown(self):
        self.assertEqual(self.ask("شو الطقس؟").intent, "unknown")

    def test_empty(self):
        self.assertEqual(self.ask("   ").intent, "empty")


if __name__ == "__main__":
    unittest.main()
