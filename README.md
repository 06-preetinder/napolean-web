# Napoléon — AI-Powered Intelligent Web Crawler

*It doesn't just collect pages — it understands them.*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/status-active-brightgreen.svg" alt="Status">
</p>

---

## Welcome to Napoléon! 👑

**Napoléon** is an intelligent, AI-powered web crawler that doesn't just collect web pages—it understands them. Think of it as a research assistant that can crawl websites, understand their content, extract meaningful information, and present you with exactly what you're looking for.

### But What Does That Actually Mean?

Imagine you want to research everything about a company or topic. A regular crawler would:
1. Visit many web pages
2. Save all the content
3. Leave you to figure out what's important

Napoléon does things differently:
1. **It understands your intent** - You tell it what you're looking for (e.g., "cybersecurity research")
2. **It filters intelligently** - It scores each page based on how relevant it is to your goal
3. **It extracts knowledge** - It finds important entities (people, places, organizations), generates summaries, and identifies key topics
4. **It visualizes connections** - It creates graphs showing how pages and entities are related

---

## Table of Contents

1. [Features Overview](#features-overview)
2. [Quick Start Guide](#quick-start-guide)
3. [Installation](#installation)
4. [Usage Examples](#usage-examples)
5. [Understanding the Output](#understanding-the-output)
6. [Module Breakdown](#module-breakdown)
7. [Project Structure](#project-structure)
8. [Recent Hardening](#recent-hardening)
9. [Troubleshooting](#troubleshooting)
10. [License](#license)

---

## Features Overview

| Feature | Description |
|---------|-------------|
| **Hybrid Crawling** | Uses both fast HTTP requests and browser automation (Selenium) for JavaScript-heavy sites |
| **Intent-Aware Filtering** | Tell Napoléon what you're looking for, and it prioritizes relevant pages |
| **AI-Powered Analysis** | Uses state-of-the-art NLP models to understand content |
| **Entity Extraction** | Automatically finds people, organizations, locations, and more |
| **Summarization** | Generates concise summaries of each page |
| **Security Scanning** | Identifies potential vulnerabilities and sensitive data exposure |
| **Research Reports** | Creates comprehensive research reports from crawled data |
| **Network Visualization** | Generates interactive graphs showing page and entity relationships |

---

## Quick Start Guide

### 👑 The Imperial Web Suite (Recommended)

Launch the full-fledged, vintage classic Napoleonic web application with embedded live terminal, visual campaign launcher, and lightweight 60 FPS interactive graphs:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download the English language model
python -m spacy download en_core_web_sm

# 3. Launch the Imperial Web Suite!
python app.py
```
*Your default browser will automatically open to `http://localhost:5000`. You never need to remember or type CLI commands! Simply paste the target URL, select your battle formation, and watch the campaign unfold in real-time.*

---

### 💻 Standalone Command-Line Tool (CLI)

Prefer the classic terminal? Napoléon remains 100% functional via command line:

```bash
python Napolean.py --url https://example.com --depth 2 --scan-security --generate-report --generate-graph
```

---

## Installation

### Prerequisites

- **Python 3.8 or higher**
- **Google Chrome** (required for Selenium/browsers)

### Step-by-Step Installation

#### 1. Create a Virtual Environment (Recommended)

```bash
# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# On Linux/MacOS
python -m venv venv
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Download the Language Model

```bash
python -m spacy download en_core_web_sm
```

#### 4. (Optional) Install CPU-Only PyTorch

If you don't have a GPU and want a lighter installation:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

---

## Usage Examples

### Basic Crawl (Simple & Fast)

Crawl a website using only HTTP requests (fastest method):

```bash
python Napolean.py --url https://example.com --depth 2 --save-json output/results.json
```

### Using Selenium (For JavaScript Sites)

Some websites load content dynamically with JavaScript. Use Selenium to render the full page:

```bash
python Napolean.py --url https://example.com --method selenium --depth 2
```

### Intent-Aware Crawling (The Smart Way)

This is Napoléon's superpower! Tell it what you're researching, and it will score and filter pages based on relevance:

```bash
python Napolean.py --url https://www.mit.edu --intent "college university education research" --depth 2 --napoleon-mode --save-json output/mit.json
```

### Full-Featured Research Pipeline

Run crawling, security scanning, report generation, and graph visualization all at once:

```bash
python Napolean.py \
  --url https://example.com \
  --intent "your research topic" \
  --depth 2 \
  --save-json output/results.json \
  --scan-security \
  --generate-report \
  --generate-graph
```

### Other Useful Options

| Option | Description | Example |
|--------|-------------|---------|
| `--no-save` | Run without saving to disk (testing) | `--no-save` |
| `--save-sqlite` | Also save to SQLite database | `--save-sqlite output/crawled.db` |
| `--headless` | Run browser in background (no visible window) | `--headless` |
| `--timeout` | Request timeout in seconds | `--timeout 10` |

---

## Understanding the Output

### JSON Output Structure

When you save to JSON, each crawled page includes:

```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "meta_description": "Brief description from meta tags",
  "headings": ["Heading 1", "Heading 2", "Heading 3"],
  "text": "Main content of the page...",
  "emails": ["email@example.com"],
  "scripts": ["/path/to/script.js"],
  "forms": [{"action": "/submit", "method": "post", "inputs": ["name", "email"]}],
  "relevance_score": 0.85,
  "entities": [
    {"text": "John Doe", "type": "PERSON"},
    {"text": "New York", "type": "GPE"}
  ],
  "keywords": ["keyword1", "keyword2"],
  "summary": "A brief summary of the page content...",
  "links": ["https://example.com/other-page"]
}
```

### What Do These Fields Mean?

- **relevance_score**: A number from 0 to 1 indicating how relevant the page is to your search intent (1 = most relevant)
- **entities**: Things the AI found in the text - people, places, organizations, dates, etc.
- **keywords**: Key topics and phrases identified in the content
- **summary**: A short AI-generated summary of the page
- **links**: Other pages this page links to (useful for graph visualization)

---

## Module Breakdown

Napoléon is built as a modular system. Here's what each component does:

### 1. Napolean.py (Main Entry Point)

**What it does:** This is the brain of the operation. It:
- Parses command-line arguments
- Manages the crawling queue
- Coordinates all other modules
- Displays the Napoléon-themed banner and progress messages

**Think of it as:** The conductor of an orchestra

---

### 2. data_extractor.py

**What it does:** Extracts structured information from raw HTML:
- Page title
- Meta descriptions
- Headings (h1, h2, h3)
- Main text content
- Email addresses
- Script references
- Form details (actions, methods, input fields)

**Think of it as:** A translator that converts messy HTML into organized data

---

### 3. ai_engine.py (NapoléonAI)

**What it does:** The "intelligence" layer with multiple capabilities:

| Function | Description |
|----------|-------------|
| **Relevance Scoring** | Scores pages based on how well they match your search intent using semantic embeddings |
| **Entity Extraction** | Identifies named entities (people, places, organizations) using spaCy |
| **Keyword Extraction** | Finds important topics using KeyBERT |
| **Summarization** | Generates brief summaries of long content |
| **Link Scoring** | Predicts which links are worth following before visiting them |

**Think of it as:** The research analyst who reads and understands every page

---

### 4. storage_manager.py

**What it does:** Handles saving and organizing crawled data:
- Saves to JSON format (human-readable, easy to share)
- Optionally saves to SQLite (faster queries, better for large datasets)
- Manages buffering for efficient writing

**Think of it as:** The archivist who organizes all the collected information

---

### 5. security_scanner.py

**What it does:** Analyzes pages for security concerns:

| Scan Type | What It Finds |
|-----------|---------------|
| **Technology Detection** | Identifies CMS, frameworks, libraries (WordPress, React, etc.) |
| **Sensitive Files** | Finds links to potentially sensitive files (.env, config.php) |
| **SQL Injection Vectors** | Identifies possible SQL injection points in forms |
| **XSS Vectors** | Finds potential cross-site scripting vulnerabilities |
| **Admin Panels** | Discovers login/management pages |
| **Sensitive Data** | Looks for exposed API keys, passwords, tokens |
| **Email Extraction** | Collects email addresses for OSINT |
| **API Endpoints** | Finds potential API endpoints |

**Think of it as:** The security consultant who audits the website

---

### 6. report_generator.py

**What it does:** Creates comprehensive research reports:
- Summary statistics (pages crawled, relevance scores)
- Important entities analysis
- Key insights generation
- Top relevant pages ranking
- Topic/keyword analysis
- URL pattern analysis

**Think of it as:** The research writer who compiles findings into a report

---

### 7. graph_builder.py

**What it does:** Creates interactive visualizations:
- **Crawl Graph**: Shows how pages link to each other
- **Entity Graph**: Shows relationships between pages and extracted entities

The output is an interactive HTML file you can open in a browser and explore!

**Think of it as:** The cartographer who draws maps of the discovered information

---

### 8. serve_frontend.py

**What it does:** A simple HTTP server that:
- Serves the output files
- Enables JavaScript to load JSON data (browsers block file:// access)
- Opens the visualization in your browser

**Think of it as:** The tour guide who helps you explore the results

---

## Project Structure

```
napolean-web/
├── Napolean.py              # Main entry point
├── data_extractor.py        # HTML parsing
├── ai_engine.py            # AI/NLP processing
├── storage_manager.py      # Data storage
├── security_scanner.py     # Security analysis
├── report_generator.py     # Report generation
├── graph_builder.py        # Graph visualization
├── serve_frontend.py       # Local web server
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
├── output/                 # Default output folder
│   ├── crawled.json       # Crawled data
│   ├── security_report.json
│   ├── research_report.json
│   ├── network_graph.html  # Interactive graph
│   └── entity_graph.html   # Entity visualization
└── lib/                    # Frontend libraries
    ├── bindings/
    ├── tom-select/         # Dropdown component
    └── vis-9.1.2/          # Network visualization
```

---

## Recent Hardening

A few correctness and security fixes have been made to the crawler core:

- **Domain validation** — link filtering now compares actual URL hosts rather than checking whether the base domain appears anywhere in the URL string, closing a bypass where a crafted redirect URL could slip past the same-domain restriction.
- **`--method selenium` now leads, not just falls back** — previously, Selenium only engaged if a plain HTTP request returned completely empty HTML, so JS-rendered sites with a non-empty-but-content-poor shell (e.g. a bare `<div id="root">`) could silently skip Selenium even when explicitly requested.
- **`--timeout` is now actually respected** — the flag was previously parsed but never passed through to the request layer.
- **Local server CORS scoped to localhost** — `serve_frontend.py` no longer serves crawl and security-scan output with a wildcard `Access-Control-Allow-Origin`, which could otherwise let any other open browser tab read that data cross-origin while the server was running.

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "No module named 'spacy'"

**Solution:** Run `pip install -r requirements.txt` and then `python -m spacy download en_core_web_sm`

#### 2. "ChromeDriver not found"

**Solution:** The webdriver-manager should handle this automatically. If not, install ChromeDriver manually or ensure Chrome is installed.

#### 3. "Sentence transformers error"

**Solution:** Install PyTorch before sentence-transformers: `pip install torch --index-url https://download.pytorch.org/whl/cpu`

#### 4. Rate limiting or blocking

**Solution:** 
- Reduce crawl depth
- Increase timeout: `--timeout 10`
- Add delays between requests (edit the code if needed)
- Use `--headless` for Selenium

#### 5. "Permission denied" on output folder

**Solution:** Create the output folder manually: `mkdir output`

---

## Usage Tips for Newcomers

1. **Start Small**: Begin with `--depth 1` to understand how it works before crawling deeper

2. **Use Intent Filtering**: Always use `--intent "your topic"` for better, more relevant results

3. **Check Output First**: Open the JSON file to see what data looks like before generating graphs

4. **Use --napoleon-mode**: It adds fun Napoleon-themed messages that make the crawl more engaging

5. **Explore the Graphs**: The HTML visualizations are interactive—zoom, pan, and click on nodes!

---

## Example Workflows

### Research a Company

```bash
python Napolean.py \
  --url https://company.com \
  --intent "company products services leadership history" \
  --depth 3 \
  --save-json output/company.json \
  --generate-report \
  --generate-graph
```

### Security Reconnaissance

```bash
python Napolean.py \
  --url https://target-site.com \
  --intent "security vulnerabilities" \
  --depth 2 \
  --scan-security \
  --save-json output/security_scan.json
```

### Academic Research

```bash
python Napolean.py \
  --url https://arxiv.org \
  --intent "machine learning neural networks deep learning" \
  --depth 2 \
  --save-json output/papers.json
```

---

## Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all dependencies are installed correctly
3. Ensure Python 3.8+ is being used
4. Check that Chrome/Chromium is installed (for Selenium)

---

<p align="center">
  <sub>Built with ⚔️ and 🧠 — Vive l'Empereur!</sub>
</p>
