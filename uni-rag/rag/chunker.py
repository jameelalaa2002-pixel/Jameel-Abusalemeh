"""Load markdown documents and split them into section-based chunks."""
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    id: str
    doc: str        # document title
    section: str    # section heading
    text: str
    source: str     # file name

    @property
    def title(self) -> str:
        return f"{self.doc} › {self.section}"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?؟۔])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def load_chunks(docs_dir: str | Path, max_chars: int = 500) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(Path(docs_dir).glob("*.md")):
        doc_title, section, buf = path.stem, "", []

        def flush():
            body = " ".join(buf).strip()
            if not body:
                return
            # long sections are split by sentences into windows of <= max_chars
            windows, cur = [], ""
            for s in split_sentences(body):
                if cur and len(cur) + len(s) > max_chars:
                    windows.append(cur)
                    cur = s
                else:
                    cur = f"{cur} {s}".strip()
            if cur:
                windows.append(cur)
            for i, w in enumerate(windows):
                chunks.append(Chunk(
                    id=f"{path.stem}:{len(chunks)}", doc=doc_title,
                    section=section + (f" ({i + 1})" if len(windows) > 1 else ""),
                    text=w, source=path.name))

        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                doc_title = line[2:].strip()
            elif line.startswith("## "):
                flush()
                buf, section = [], line[3:].strip()
            elif line.strip():
                buf.append(line.strip())
        flush()
    return chunks
