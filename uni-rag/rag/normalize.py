"""Arabic text normalisation and light stemming (no external dependencies)."""
import re

_TASHKEEL = re.compile(r"[ً-ْٰـ]")
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_NON_WORD = re.compile(r"[^\w\s.%+\-]", re.UNICODE)

# Question words, dialect fillers and function words: they carry no topic.
STOPWORDS = {
    "في", "من", "على", "الى", "عن", "هل", "ما", "ماذا", "كم", "شو", "ايش", "كيف",
    "متى", "وين", "اذا", "لو", "ان", "انه", "هذا", "هاي", "هاد", "هذه", "ذلك",
    "بدي", "بدك", "بقدر", "بتقدر", "يمكن", "يحق", "لازم", "لي", "لك", "عندي",
    "هو", "هي", "ثم", "او", "و", "ب", "ل", "مع", "كل", "عشان", "لما", "يعني",
    "اللي", "الي", "التي", "الذي", "كان", "يكون", "صار", "يصير", "ممكن", "بس",
    "قد", "لا", "لم", "لن", "تم", "ضمن", "بعد", "قبل", "عند", "الطالب", "طالب",
}

_PREFIXES = ("وبال", "والل", "وال", "بال", "كال", "فال", "لل", "ال")


def normalize(text: str) -> str:
    text = text.translate(_ARABIC_DIGITS)
    text = _TASHKEEL.sub("", text)
    text = re.sub("[إأآٱ]", "ا", text)
    text = text.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    text = text.lower()
    text = _NON_WORD.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def stem(token: str) -> str:
    for p in _PREFIXES:
        if token.startswith(p) and len(token) - len(p) >= 3:
            token = token[len(p):]
            break
    if len(token) > 4 and token.endswith(("ات", "ون", "ين", "ان")):
        token = token[:-2]
    return token


def tokens(text: str, drop_stopwords: bool = True) -> list[str]:
    out = []
    for tok in normalize(text).split():
        if drop_stopwords and tok in STOPWORDS:
            continue
        out.append(stem(tok))
    return out


def analyze(text: str) -> str:
    """Normalised, stemmed, stop-word-free string (what the vectorisers see)."""
    return " ".join(tokens(text))
