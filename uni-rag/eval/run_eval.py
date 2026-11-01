"""Evaluate retrieval, answers, refusals and tools:  python eval/run_eval.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.agent import Assistant  # noqa: E402
from rag.normalize import normalize  # noqa: E402


def main() -> int:
    data = json.loads((ROOT / "eval" / "eval_set.json").read_text(encoding="utf-8"))
    bot = Assistant(use_llm=False)  # deterministic, reproducible numbers
    rows, hit1, hit3, rr, kw = [], 0, 0, 0.0, 0
    for item in data["answerable"]:
        hits = bot.retriever.search(item["q"], 3)
        secs = [h.chunk.section for h in hits]
        rank = secs.index(item["section"]) + 1 if item["section"] in secs else 0
        hit1 += rank == 1
        hit3 += rank > 0
        rr += 1 / rank if rank else 0
        ans = bot.ask(item["q"])
        ok = normalize(item["keyword"]) in normalize(ans.text)
        kw += ok
        rows.append({"q": item["q"], "rank": rank, "keyword_ok": ok, "mode": ans.mode})
        if rank != 1 or not ok:
            print(f"  ✗ {item['q']} | rank={rank} keyword_ok={ok} top={secs[0]}")

    refused = 0
    for q in data["out_of_scope"]:
        a = bot.ask(q)
        refused += a.mode == "refuse"
        if a.mode != "refuse":
            print(f"  ✗ should refuse: {q} -> {a.text[:60]}")

    tools_ok = 0
    for t in data["tools"]:
        a = bot.ask(t["q"])
        good = a.mode == "tool" and t["contains"] in a.text
        tools_ok += good
        if not good:
            print(f"  ✗ tool: {t['q']} -> {a.text}")

    n, m, p = len(data["answerable"]), len(data["out_of_scope"]), len(data["tools"])
    report = {
        "hit@1": hit1 / n, "hit@3": hit3 / n, "MRR": rr / n,
        "answer_keyword_accuracy": kw / n,
        "refusal_accuracy": refused / m, "tool_accuracy": tools_ok / p,
        "n_answerable": n, "n_out_of_scope": m, "n_tools": p,
    }
    print("\n=== Evaluation ===")
    for k, v in report.items():
        print(f"{k:26s} {v:.2%}" if isinstance(v, float) else f"{k:26s} {v}")
    (ROOT / "eval" / "results.json").write_text(
        json.dumps({"summary": report, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
