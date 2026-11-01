# Student Handbook Assistant: Arabic RAG + Tools

A complete "Query Engineering" project: an Arabic question-answering assistant that
retrieves from documents, calls tools for calculations, refuses out-of-scope questions,
and ships with an evaluation suite.

> **Important:** the documents in `data/docs/` are **sample data written for this project**
> (invented rules and numbers). They are not the official regulations of any university.
> Replace them with real documents before using the assistant for anything real.

## Architecture

```
question -> [tool router] --match--> GPA / fees / absence calculator
               |
               no match
               v
        [hybrid retriever]  word TF-IDF + char n-gram TF-IDF (Arabic-normalised)
               |
        [guards] score threshold + query-term coverage  --fail--> refusal
               |
        [answer] LLM (optional) with <context> delimiting  |  extractive sentences
```

| Course topic | Where |
|---|---|
| Tokens / Arabic text handling | `rag/normalize.py` |
| Chunking, retrieval | `rag/chunker.py`, `rag/retriever.py` |
| Tools / agents | `rag/tools.py`, `rag/agent.py` |
| Evaluation | `eval/run_eval.py`, `eval/eval_set.json` |
| Safety / prompt injection | `rag/llm.py` (data-delimited context), refusal guards, `tests/` |

## Run

```bash
pip install -r requirements.txt
python app.py                         # interactive CLI
python app.py "كم نسبة الغياب المسموحة؟"
python web.py                         # web UI at http://localhost:8000
python eval/run_eval.py               # evaluation report
python -m unittest discover -s tests  # unit tests
```

## Optional LLM generation

By default answers are extractive (deterministic, no model needed). To let an LLM write the
answer from the retrieved context, set one of:

```bash
export ANTHROPIC_API_KEY=...        # optional: ANTHROPIC_MODEL
export OLLAMA_MODEL=qwen2.5:7b      # local open-weight model, optional OLLAMA_URL
```

The LLM path was not run in the build environment (no key or GPU there); it falls back to
extractive answers if the call fails.

## Evaluation results (extractive mode)

18 answerable questions, 5 out-of-scope, 3 tool queries:
hit@1 = hit@3 = MRR = 100%, answer-keyword accuracy 100%, refusal 100%, tools 100%.

Caveat: the eval set was written by the same author as the documents, and the refusal guard
was tuned while looking at it, so these numbers are optimistic. For your report, add questions
written by classmates and report the results separately.

## AI-use disclosure

This project was developed with the assistance of Claude (Anthropic). Claude was used to
propose the project structure and to write the first version of the code, the sample
documents, the evaluation set and the tests. The author is responsible for reviewing,
running and understanding the code, and for any later changes.

<!-- Author: edit this section to say exactly what you reviewed, changed and added yourself. -->

## Extending it (ideas for the report)

- Swap TF-IDF for multilingual embeddings (e.g. bge-m3, multilingual-e5) and compare in `run_eval.py`.
- Add a reranker and measure the change in hit@1.
- Add a text-to-SQL tool over a courses table.
- Add a prompt-injection test set (documents containing hidden instructions).
