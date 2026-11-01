"""Agent: route -> tool | retrieve -> answer (LLM if configured, else extractive) | refuse."""
from dataclasses import dataclass, field
from pathlib import Path

from . import llm
from .chunker import load_chunks, split_sentences
from .normalize import normalize, tokens
from .retriever import HybridRetriever
from .tools import try_tools

ROOT = Path(__file__).resolve().parent.parent
REFUSAL = "ما لقيت جواب لهاد السؤال بالمستندات المتوفرة 🤷 جرّب تسأل عن الحضور، الامتحانات، العلامات، أو التسجيل والرسوم."
MIN_SCORE = 0.10   # below this the best chunk is considered unrelated
MIN_COVERAGE = 0.4  # share of query terms that must appear in the best chunk


def coverage(query: str, text: str) -> float:
    """Share of query content-words found (exactly or via any 4-letter piece) in the text."""
    terms = [t for t in tokens(query) if len(t) >= 3]
    if not terms:
        return 1.0
    body = normalize(text)
    found = sum(1 for t in terms if t in body
                or any(t[i:i + 4] in body for i in range(len(t) - 3)))
    return found / len(terms)


@dataclass
class Answer:
    text: str
    mode: str                      # tool | rag | refuse
    sources: list[str] = field(default_factory=list)
    score: float = 0.0
    contexts: list[str] = field(default_factory=list)


class Assistant:
    def __init__(self, docs_dir: str | Path = ROOT / "data" / "docs", use_llm: bool = True):
        self.retriever = HybridRetriever(load_chunks(docs_dir))
        self.use_llm = use_llm and llm.available() is not None

    def ask(self, question: str, k: int = 3) -> Answer:
        question = question.strip()
        if not question:
            return Answer("اكتب سؤالك أول 🙂", "refuse")

        tool = try_tools(question)
        if tool:
            return Answer(tool.answer, "tool", [f"أداة: {tool.name}"], 1.0)

        hits = self.retriever.search(question, k)
        if (not hits or hits[0].score < MIN_SCORE
                or coverage(question, hits[0].chunk.section + " " + hits[0].chunk.text) < MIN_COVERAGE):
            return Answer(REFUSAL, "refuse", [], hits[0].score if hits else 0.0)

        contexts = [h.chunk.text for h in hits]
        sources = [h.chunk.title for h in hits]
        if self.use_llm:
            try:
                return Answer(llm.generate(question, contexts), "rag", sources, hits[0].score, contexts)
            except Exception:
                pass  # fall back to extractive answer
        return Answer(self._extract(question, hits[0].chunk.text), "rag",
                      sources[:1], hits[0].score, contexts)

    def _extract(self, question: str, text: str) -> str:
        sents = split_sentences(text)
        if len(sents) <= 2:
            return text
        scores = self.retriever.score_texts(question, sents)
        best = sorted(sorted(range(len(sents)), key=lambda i: -scores[i])[:2])
        return " ".join(sents[i] for i in best)
