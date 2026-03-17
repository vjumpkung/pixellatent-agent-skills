---
name: pageindex
description: >
  Generate a hierarchical PageIndex (tree-structured table of contents) from any PDF or Markdown
  file using Claude as the reasoning engine — no OpenAI API key required, no special repository
  needed. This skill converts documents into LLM-optimized JSON trees with titles, page ranges,
  node IDs, and summaries, ideal for vectorless RAG, document navigation, and intelligent document
  analysis. Use this skill whenever the user wants to: index a document, generate a table of
  contents, create a document structure/outline, build a PageIndex, parse a PDF or Markdown into
  a tree, or prepare a document for RAG retrieval. Trigger even if the user says things like
  "index this PDF", "generate structure for this document", "create an outline from this file",
  or "build a pageindex".
---

# PageIndex Generation Skill

Generate a **PageIndex** — a hierarchical JSON tree — from any PDF or Markdown file.
**You (Claude) are the LLM engine.** No API key, no special repository required.

**Only prerequisites:** Python with `pymupdf` and/or `PyPDF2` installed.

```bash
pip install pymupdf PyPDF2
```

The extraction script at `./scripts/extract_pages.py` handles raw text
extraction. You do all the reasoning: structure detection, hierarchy building, and summaries.

---

## Output Format

Always produce a JSON file with this exact structure:

```json
{
  "doc_name": "filename.pdf",
  "structure": [
    {
      "title": "Chapter 1: Introduction",
      "node_id": "0000",
      "start_index": 1,
      "end_index": 12,
      "summary": "Overview of the topic, motivation, and chapter structure.",
      "nodes": [
        {
          "title": "1.1 Background",
          "node_id": "0001",
          "start_index": 2,
          "end_index": 5,
          "summary": "Historical context and prior work.",
          "nodes": []
        }
      ]
    }
  ]
}
```

**Field rules:**
- `node_id` — zero-padded sequential integers `"0000"`, `"0001"`, … assigned in depth-first order
- `start_index` / `end_index` — 1-indexed page numbers for PDF; line numbers for Markdown
- `summary` — leaf nodes; branch nodes (those with children) use `"prefix_summary"` instead
- `nodes` — always present, empty array `[]` for leaves
- Include `"doc_description"` at top level only if the user explicitly asks for it

**Output location:** same directory as the input file, named `<docname>_structure.json`.
If the user specifies a different output path, use that instead.

---

## Step-by-Step Workflow

### Step 1 — Identify and Validate Input

Confirm the file path and type (`.pdf` or `.md`/`.markdown`). Resolve relative paths to
absolute. Check the file exists.

Determine the output path: `<input_dir>/<docname>_structure.json` unless the user specifies otherwise.

### Step 2 — Extract Raw Content

The script path is `./scripts/extract_pages.py`.
Run it from any directory — it has no working-directory dependency.

```bash
# PDF — always run overview first (fast, no full text):
python ~/.claude/skills/pageindex/scripts/extract_pages.py \
  --pdf "/absolute/path/to/document.pdf" --overview \
  --output "/tmp/pageindex_overview.json"

# PDF — extract a specific page range:
python ~/.claude/skills/pageindex/scripts/extract_pages.py \
  --pdf "/absolute/path/to/document.pdf" --start 1 --end 20 \
  --output "/tmp/pageindex_toc_pages.json"

# Markdown:
python ~/.claude/skills/pageindex/scripts/extract_pages.py \
  --md "/absolute/path/to/document.md" \
  --output "/tmp/pageindex_md_content.json"
```

Use absolute paths for both the input file and `--output` to avoid any working-directory confusion.
Then read the output files with the Read tool.

### Step 3 — Build the Structure (your reasoning task)

#### For Markdown files

Structure comes directly from Markdown headers — no guessing needed:

1. Read the full markdown content from the extracted JSON
2. Scan every line: `#` headers become nodes; header level = nesting depth
3. Build the tree by nesting child headers under their closest parent
4. For each node:
   - `start_index` = line number of its header
   - `end_index` = line number just before the next header of same or higher level (or last line)
   - Text = all lines between this header and the next header of equal/higher level
5. Assign `node_id` values depth-first

#### For PDF files

**A. Check for an existing Table of Contents (pages 1–20)**

Read the first 20 pages. Look for:
- A page titled "Contents", "Table of Contents", "Index", or similar
- Lines pairing section titles with page numbers (e.g., `"2.1 Methodology .... 45"`)

If a clear TOC exists:
- Extract every entry as `{title, page_number}`
- Verify the offset between TOC page numbers and physical page numbers by spot-checking one section
- Build the flat list → convert to tree using section numbering (1.1, 1.2, 2.1 …)
- `start_index` = TOC page number ± offset; `end_index` = next section's start − 1

If no TOC (or TOC has no page numbers):
- Use the overview snippets to spot structural patterns (numbered chapters, ALL-CAPS headings)
- Extract pages in 30–50 page chunks and identify section starts:
  - A section starts when a page opens with a short, possibly numbered heading distinct from body text
- Build flat structure from identified starts, then nest by numbering/indentation

**B. Expand large nodes**

If any section spans > 10 pages, read those pages and check for visible sub-sections. Add them
as child nodes if found.

**C. Assign page ranges**

For every node: `end_index` = next sibling's `start_index` − 1.
Last node at each level: `end_index` = parent's `end_index`.

### Step 4 — Generate Summaries

For each node, write a 1–3 sentence summary:
- What topics/content this section contains
- Key terms, arguments, or data (if visible in the extracted text)
- What question a reader would answer by reading this section

If you only have the first few lines of a large section, summarize based on the title and opening.
Be transparent — say "covers X based on heading and introduction" when you haven't read all pages.

**Branch nodes** (with `nodes` children): use key `"prefix_summary"` instead of `"summary"`.
Short sections (< 5 lines of text): use the raw text verbatim as the summary.

### Step 5 — Finalize and Save

1. Assign `node_id` values: depth-first traversal, starting at `"0000"`
2. Validate: every node has `title`, `node_id`, `start_index`, `end_index`, and `summary` or `prefix_summary`
3. Write JSON to the output path determined in Step 1
4. Report to the user: output file path, top-level sections, total node count, page coverage

---

## Handling Large Documents

Be strategic — don't read everything at once:

| Doc size | Strategy |
|----------|----------|
| < 50 pages | Extract all pages, analyze in one pass |
| 50–200 pages | Overview + TOC area (pp. 1–20); read section starts on demand |
| > 200 pages | Overview + TOC; work chapter by chapter, 20–30 pages at a time |

Always run `--overview` first. Snippets tell you which pages have major headings before you load
full text.

---

## Extraction Script Reference

**Script:** `./scripts/extract_pages.py`
**Dependencies:** `pymupdf` (preferred) or `PyPDF2` — install with `pip install pymupdf PyPDF2`
**Works from any directory** — no special working directory required.

```
Arguments:
  --pdf PATH     Path to PDF file
  --md PATH      Path to Markdown file
  --start N      First page to extract (1-indexed, default: 1)
  --end N        Last page to extract (inclusive, default: last)
  --overview     PDF only: page count + 150-char snippets, no full text
  --parser       PyMuPDF (default) or PyPDF2
  --output FILE  Write JSON to file instead of stdout
```

**Output shapes:**

`--overview` mode:
```json
{
  "doc_name": "report.pdf",
  "total_pages": 146,
  "overview": [
    {"page": 1, "snippet": "Annual Report 2023..."},
    {"page": 2, "snippet": "Contents Introduction 3 Overview 9..."}
  ]
}
```

Full extraction mode:
```json
{
  "doc_name": "report.pdf",
  "total_pages": 146,
  "pages": [
    {"page": 1, "text": "Full page text..."},
    {"page": 2, "text": "Full page text..."}
  ]
}
```

Markdown mode:
```json
{
  "doc_name": "document.md",
  "total_lines": 842,
  "content": "# Title\n\n## Section 1\n..."
}
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: pymupdf` | `pip install pymupdf` |
| `ModuleNotFoundError: PyPDF2` | `pip install PyPDF2` |
| Empty text extracted from pages | Try `--parser PyPDF2` (some PDFs extract better with it) |
| Scanned PDF (image-only, no text) | Tell the user OCR is needed — text extraction won't work |
| `FileNotFoundError` for the script | Check that `~/.claude/skills/pageindex/scripts/extract_pages.py` exists |
