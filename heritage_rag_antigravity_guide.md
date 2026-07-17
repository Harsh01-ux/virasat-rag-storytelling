# Heritage RAG Storytelling Engine — Build Guide with Google Antigravity

Goal: working demo where a user asks about a heritage site and gets a cited, multilingual story back — built inside a hackathon timeframe.

---

## Step 0 — Install & set up Antigravity

1. Download from antigravity.google/download, install, sign in with Google account.
2. Open **Antigravity IDE** (not just Manager view) — you want hands-on editing + agent help side by side.
3. Create a new empty folder, e.g. `heritage-rag/`, open it as your workspace.
4. Get a **Gemini API key** from Google AI Studio (you already have experience with this from your voice agent project). Keep quota in mind — RAG + translation calls add up fast.

---

## Step 1 — Write the spec first (this is what you feed the agent)

Before prompting Antigravity, write a short spec file. Agents build better when given a clear target instead of a vague ask.

Create `SPEC.md` with something like:

```
Project: Heritage RAG Storytelling Engine
Scope: 2-3 heritage sites, curated source docs (~15-20 files)
Stack: Python, ChromaDB, sentence-transformers (multilingual), Gemini API, Streamlit
Pipeline: 
  1. Ingest docs -> chunk -> embed -> store in Chroma with metadata (site, era, region, language)
  2. User query -> retrieve top-k chunks -> pass to Gemini with prompt requiring cited answer
  3. Gemini generates story in requested language + expertise level (beginner/expert)
  4. Output shows story + source citations (doc name + snippet)
Non-goals for now: true knowledge graph, 20+ languages of source data, ASI ingestion pipeline
```

Give this file to the agent as context in your first prompt.

---

## Step 2 — Curate your data (you do this, not the agent)

Antigravity can't go find "5000 years of heritage" for you. Pick 2-3 sites you can demo well (e.g. a Chola temple, a Rajasthan fort, an ASI-listed monument near you). For each, collect:
- 2-4 short text documents (Wikipedia summary, ASI page text, a regional history snippet)
- Save as plain `.txt` or `.pdf` files in `data/raw/`

Prompt to Antigravity once you have files dropped in:
> "I've added heritage documents to `data/raw/`. Write a script `ingest.py` that reads all txt/pdf files, chunks them (~500 tokens with overlap), and stores chunks with metadata (source filename, site name) ready for embedding."

Review the chunking output before moving on — bad chunking wrecks retrieval quality later.

---

## Step 3 — Embeddings + vector store

Prompt:
> "Add embedding generation using a multilingual sentence-transformers model (paraphrase-multilingual-mpnet-base-v2), and store embeddings + metadata in a local ChromaDB collection called `heritage`. Write this as `embed_store.py` and make it re-runnable without duplicating entries."

Run it, check that `chroma_db/` folder gets created and populated. Ask the agent to write a tiny test script that queries Chroma with a sample question and prints the top 3 retrieved chunks — verify they're actually relevant before moving on.

---

## Step 4 — Retrieval + generation (the RAG core)

Prompt:
> "Write `rag_query.py`: takes a user question + target language + expertise level (beginner/expert). Retrieve top-5 relevant chunks from Chroma. Build a prompt for Gemini that: includes the retrieved chunks as context, instructs the model to answer ONLY using that context, requires the answer in the target language, adjusts tone/depth for expertise level, and requires inline citations referencing which source chunk each claim came from."

This is the most important prompt in the whole build — the citation instruction is what makes it match the problem statement (grounded, cited answers). Test it with a couple of different languages (Hindi, Tamil, English) and both expertise levels.

---

## Step 5 — Citation formatting

Ask the agent to post-process Gemini's output so citations render cleanly, e.g. mapping `[1]` markers back to actual source filenames/snippets, shown as a small "Sources" list under the story.

> "Parse the Gemini response for citation markers and render a Sources section below the story, listing source filename + the exact chunk text used."

---

## Step 6 — Frontend

Prompt:
> "Build a Streamlit app `app.py`: text input for the question, dropdown for language (Hindi, Tamil, Bengali, English, +2 more), toggle for beginner/expert, a Generate button, and display the story with sources below. Call `rag_query.py` functions directly."

Antigravity's browser control can actually open and click through the running Streamlit app to catch UI bugs — ask it to "test the app by asking a sample question in Tamil and confirm the output renders correctly."

---

## Step 7 — Iterate on quality

Once it runs end-to-end, spend remaining time here — this is what actually wins hackathons:
- Try queries the retrieval fails on, ask agent to tune chunk size/overlap
- Check translations aren't hallucinating facts not in source (spot check 2-3 languages)
- Add a "no relevant info found" fallback instead of the model making things up

---

## Step 8 — Demo prep

- Pre-pick 2-3 impressive demo queries (different languages, different sites) — don't improvise live
- Have a slide/README showing the architecture diagram (ask Antigravity to generate a simple mermaid diagram of the pipeline)
- Be ready to explain honestly: "we scoped to a curated dataset of N sites for the hackathon; the pipeline generalizes to the full ASI corpus"

---

## Quick reference: what to lean on Antigravity for vs yourself

| Task | Who |
|---|---|
| Writing/debugging code | Antigravity |
| Choosing libraries, fixing errors | Antigravity |
| Testing UI via browser | Antigravity |
| Collecting real heritage source docs | You |
| Deciding demo scope (which sites) | You |
| Judging if translations are accurate | You (or a teammate who reads that language) |
| API key & quota management | You |
