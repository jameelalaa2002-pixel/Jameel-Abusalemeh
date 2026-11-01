"""Deterministic tools the agent calls instead of letting an LLM do arithmetic."""
import math
import re
from dataclasses import dataclass

from .normalize import normalize

GRADE_POINTS = {"A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
                "C+": 2.3, "C": 2.0, "D": 1.0, "F": 0.0}
PRICE_PER_HOUR = 60
REGISTRATION_FEE = 30
ABSENCE_LIMIT = 0.15
WEEKS_PER_SEMESTER = 16


@dataclass
class ToolResult:
    name: str
    answer: str


def gpa(pairs: list[tuple[str, int]]) -> float:
    total_hours = sum(h for _, h in pairs)
    return sum(GRADE_POINTS[g] * h for g, h in pairs) / total_hours


def tuition(hours: int) -> int:
    return hours * PRICE_PER_HOUR + REGISTRATION_FEE


def allowed_absences(hours_per_week: int) -> int:
    return math.floor(hours_per_week * WEEKS_PER_SEMESTER * ABSENCE_LIMIT)


_GRADE_PAIR = re.compile(r"(?<![A-Za-z])([ABCDF][+-]?)(?:\s*[:=]\s*|\s+)(\d{1,2})(?!\d)", re.I)
_HOURS = re.compile(r"(\d{1,2})\s*(?:ساعه|ساعات|ساعة|hours?|credits?)")


def try_tools(query: str) -> ToolResult | None:
    q = normalize(query)

    # GPA: "احسب معدلي A:3, B+:3, C:2"
    pairs = [(g.upper(), int(h)) for g, h in _GRADE_PAIR.findall(query)
             if g.upper() in GRADE_POINTS and int(h) > 0]
    if pairs and ("معدل" in q or "gpa" in q):
        value = gpa(pairs)
        hours = sum(h for _, h in pairs)
        status = "ممتاز، بتنزل بقائمة الشرف إذا سجلت 15 ساعة وما رسبت 🏅" if value >= 3.5 else (
            "تحت 2.00، يعني إنذار أكاديمي ⚠️" if value < 2.0 else "فوق حد الإنذار ✅")
        return ToolResult("gpa_calculator",
                          f"المعدل = {value:.2f} (على {hours} ساعة). {status}")

    m = _HOURS.search(q)
    if m:
        hours = int(m.group(1))
        if any(w in q for w in ("رسوم", "تكلفه", "كلفه", "قسط", "سعر", "ادفع", "دفع")):
            total = tuition(hours)
            return ToolResult("fee_calculator",
                              f"رسوم {hours} ساعة = {hours} × {PRICE_PER_HOUR} + {REGISTRATION_FEE} "
                              f"(رسوم التسجيل) = {total} دينار. "
                              f"بالتقسيط: {round(total * 0.6)} عند التسجيل و{round(total * 0.4)} قبل الامتحانات.")
        if any(w in q for w in ("غياب", "اغيب", "غيب")):
            n = allowed_absences(hours)
            return ToolResult("absence_calculator",
                              f"مادة {hours} ساعات بالأسبوع = {hours * WEEKS_PER_SEMESTER} محاضرة بالفصل، "
                              f"والحد المسموح 15%، يعني بتقدر تغيب {n} محاضرات بالكثير.")
    return None
