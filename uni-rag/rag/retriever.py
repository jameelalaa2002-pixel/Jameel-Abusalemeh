"""Hybrid lexical retriever: word TF-IDF + character n-gram TF-IDF.

Character n-grams make the search robust to Arabic morphology and dialect
spelling; word TF-IDF keeps exact-term precision. No GPU, no model download.
"""
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .chunker import Chunk
from .normalize import analyze


@dataclass
class Hit:
    chunk: Chunk
    score: float


class HybridRetriever:
    def __init__(self, chunks: list[Chunk], w_word: float = 0.5):
        self.chunks = chunks
        self.w_word = w_word
        # the section heading is repeated so titles weigh more than body text
        corpus = [analyze(f"{c.section} {c.section} {c.text}") for c in chunks]
        self.word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        self.Xw = self.word.fit_transform(corpus)
        self.Xc = self.char.fit_transform(corpus)

    def _scores(self, query: str, Xw, Xc) -> np.ndarray:
        q = analyze(query)
        sw = (Xw @ self.word.transform([q]).T).toarray().ravel()
        sc = (Xc @ self.char.transform([q]).T).toarray().ravel()
        return self.w_word * sw + (1 - self.w_word) * sc

    def search(self, query: str, k: int = 3) -> list[Hit]:
        s = self._scores(query, self.Xw, self.Xc)
        order = np.argsort(-s)[:k]
        return [Hit(self.chunks[i], float(s[i])) for i in order]

    def score_texts(self, query: str, texts: list[str]) -> list[float]:
        """Similarity of the query to arbitrary texts (used to pick sentences)."""
        a = [analyze(t) for t in texts]
        return self._scores(query, self.word.transform(a), self.char.transform(a)).tolist()
