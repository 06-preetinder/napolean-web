# Napoléon — AI‑Powered Intent‑Aware Web Crawler

**Napoléon** is a modular, CLI-first web crawler that combines classic crawling (requests + Selenium) with lightweight on-device AI for *intent-aware* crawling, semantic filtering, summarization and entity extraction. It is designed for research, OSINT, and reconnaissance workflows where targeted, relevant crawl results and structured output matter more than raw breadth.

---

## Features
- Hybrid fetching: `requests` for speed, `selenium` for JS-heavy pages.
- HTML parsing and structured extraction (title, meta, headings, text, forms, emails).
- Local Storage: JSON + optional SQLite for persistent datasets.
- AI Intelligence: semantic relevance scoring (chunked embeddings), entity extraction (spaCy), and summarization.
- Intent-aware crawling: provide an `--intent` to prioritize pages relevant to your goal.
- CLI interface with Napoléon-themed output for easy demos.

---

## Quick Install (recommended in a virtualenv)
```bash
# create venv (optional but recommended)
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\\Scripts\\activate       # Windows PowerShell

# install dependencies (CPU-only PyTorch recommended)
pip install -r requirements.txt

# Install spaCy English model
python -m spacy download en_core_web_sm
```

**CPU-only PyTorch hint:** If you don't have GPU, install CPU torch for compatibility before `sentence-transformers` (optional):
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

---

## Usage Examples

Basic crawl (requests-only):
```bash
python Napolean.py --url https://example.com --depth 1 --method requests --save-json output/results.json
```

Use Selenium (visible browser):
```bash
python Napolean.py --url https://example.com --method selenium --depth 2 --napoleon-mode
```

Intent-aware crawl (semantic filtering):
```bash
python Napolean.py --url https://www.mit.edu --intent "college university education" --depth 2 --napoleon-mode --save-json output/mit.json
```

Save to SQLite as well:
```bash
python Napolean.py --url https://towardsdatascience.com --intent "data science" --depth 2 --save-json output/data.json --save-sqlite output/crawled.db
```

Disable saving to disk (dry-run):
```bash
python Napolean.py --url https://example.com --no-save
```

---

## Output
- JSON file (`--save-json`) contains extracted page records with fields:
  - `url`, `title`, `meta_description`, `headings`, `text`, `emails`, `scripts`, `forms`
  - AI fields: `relevance_score`, `summary`, `entities` (if `--intent` provided or AI enabled)
- SQLite (optional) stores the same per-page data in a `pages` table for quick querying.

---

## Project Structure
```
Napoleon/
├─ Napolean.py            # CLI entrypoint + crawler
├─ core/ (or project root)
   ├─ data_extractor.py  # HTML ➜ structured content
   ├─ storage_manager.py # JSON + optional SQLite storage
   ├─ ai_engine.py       # Embeddings, relevance, entities, summarization
├─ output/                # default output path
└─ requirements.txt
```

---

## Troubleshooting & Notes
- If you hit rate limits or blocking, use polite crawling: lower depth, increase timeouts, add delays, respect robots.txt (not implemented by default).
- For very large pages, chunking is used to avoid semantic dilution; tune `chunk_size` in `ai_engine.py` if needed.
- If sentence-transformers raises errors, make sure `torch` (CPU) is installed before attempting heavy models.

---

## How to Contribute / Roadmap (short)
This project is designed to be modular. Next steps include:
- Better link prioritization (learned model)
- Reinforcement-based adaptive crawling (train agent on reward: info density)
- Security-oriented recon mode (form detection, tech fingerprinting)
- Conversational query interface (QA over crawl)

---

## License
MIT — use responsibly. If you build tools for recon/security, follow ethics and legal rules in your jurisdiction.

---
