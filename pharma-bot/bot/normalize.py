"""Arabic text normalisation (no external dependencies)."""
import re

_TASHKEEL = re.compile(r"[ً-ْٰـ]")
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_NON_WORD = re.compile(r"[^\w\s]", re.UNICODE)


def normalize(text: str) -> str:
    text = text.translate(_DIGITS)
    text = _TASHKEEL.sub("", text)
    text = re.sub("[إأآٱ]", "ا", text)
    text = text.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    text = _NON_WORD.sub(" ", text.lower())
    return re.sub(r"\s+", " ", text).strip()
