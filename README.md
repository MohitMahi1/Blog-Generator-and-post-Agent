# ✍️ Blog Writing Agent

> An intelligent multi-agent system that automatically researches, plans, writes, and structures high-quality technical blog posts from a simple topic.

---

## 📖 Project Description

**Blog Writing Agent** is a full-stack web application that turns a simple topic idea into a fully structured blog post. You type a topic into a chat interface, and the agent:

1. Decides whether the topic needs live web research.
2. Researches the topic and collects real sources with citations (when needed).
3. Plans the article — title, audience, tone, and section-by-section outline.
4. Writes every section in parallel.
5. Merges everything into a single polished Markdown article.
6. Offers to download it as **Markdown, PDF, or Word**.

---

## 🎯 What It Does & Why I Created It

### What it does
- **Research-first writing** — The agent decides between three research modes:
  - `closed_book` — writes purely from the model's knowledge (no search).
  - `hybrid` — searches the web only for specific sections that need fresh data.
  - `open_book` — researches the whole topic before writing.
- **Structured planning** — Instead of free-flowing text, the agent builds a real editorial plan (audience, tone, constraints, and per-section goals) before writing a single word.
- **Parallel section writing** — Each section of the plan is written by an independent worker in parallel (map-reduce fanout), then merged into one coherent article.
- **Evidence & citations** — Every web-sourced claim is backed by collected evidence with links, visible in the UI.
- **Chat-based UX** — A conversational flow ("Would you like to download it? … Which format?") makes the tool feel like an assistant, not a form.
- **Session history** — Recently generated blogs are saved to PostgreSQL and listed in the sidebar for the session.

### Why I created it
Writing a high-quality technical blog post takes hours of research, outlining, drafting, and editing. I wanted an **AI agent that does the entire pipeline end-to-end** - not just a text generator, but an agent that reasons about *what* it needs to know, *goes and finds it*, *plans* the structure like an editor, and *writes* every section - then hands you a finished article you can download and publish. This project is a practical exploration of  graph-based orchestration, and building a real product around them.

---

## 🚀 Live Demo

Try it live: **[https://blog-generator-post-agent.vercel.app/](https://blog-generator-post-agent.vercel.app/)**

---

## ✨ Features

| Feature | Description |
| --- | --- |
| 💬 Chat interface | Type a topic, get a full blog post in a conversational flow |
| 🌐 Web research | Automatic Tavily search with evidence and source links |
| 📐 Editorial planning | Auto-generated plan: title, audience, tone, section goals |
| ⚡ Parallel writing | Map-reduce fanout writes all sections at the same time |
| 📥 Downloads | Export your article as **Markdown (.md)**, **PDF**, or **Word (.doc)** |
| 🗂️ Recent blogs | Session-based history saved to PostgreSQL (15-minute retention) |
| 🧩 Rich output tabs | Inspect the plan, evidence, image specs, and live node-by-node logs |
| 🖼️ Image integration | The agent plans and attempts to generate AI images for the article *(see Known Issues)* |
| ✅ Confirmation flow | Asks before taking actions — download, and (coming soon) publish |

---

## 🧠 How It Works

The backend is a **LangGraph** state graph. Each step is a node; edges define the workflow:

```
START
  │
  ▼
ROUTER ────────────────┐
  │ decides mode &      │
  │ research need       │
  ├──▶ RESEARCH         │ (Tavily search → evidence)
  │      │              │
  ▼      ▼              │
ORCHESTRATOR ───────────┘
  │  builds the editorial plan (title, audience, sections)
  │
  ▼  (map-reduce fanout — one worker per section)
WORKERS  ◀── Send(task) ──┐
  │  each writes one      │
  │  section in parallel  │
  ▼                       │
REDUCER (subgraph)        │
  │  merge sections ──────┘
  │  decide images
  │  generate & place images
  ▼
 END  → final Markdown article
```

- **Router** decides the research mode and whether web research is required.
- **Research** runs the web searches and collects `EvidenceItem`s (title, URL, snippet, source).
- **Orchestrator** produces a structured `Plan` with `Task`s (goal, bullets, word target, tags).
- **Workers** write each section in parallel using `Send()` fan-out.
- **Reducer** merges the sections, decides which images the article needs, generates them, and places them back into the Markdown.

---

## 📦 How to Run Loacally

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** and **npm**
- API keys: **Mistral AI** (required) and **Tavily** (required for research). Google and database keys are optional but recommended.
- PostgreSQL database (e.g. [Supabase](https://supabase.com)) if you want session history Instead you can aslo use RAM for memory.

### 1. Clone the repository

```bash
git clone https://github.com/your-username/blog-writing-agent.git
cd Blog_Wrting_Agent
```

### 2. Set up the backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder with your keys:

```env
MISTRAL_API_KEY=your_mistral_api_key
TAVILY_API_KEY=your_tavily_api_key
GOOGLE_API_KEY=your_google_api_key        # optional — image generation
DATABASE_URL=postgresql://user:pass@host/db  # optional — session history
SUPABASE_REGION=ap-northeast-1            # optional — if using Supabase pooler
FRONTEND_URL=http://localhost:5173        # optional — CORS allow-list
```

Start the API server (port `8000`):

```bash
uvicorn app.main:app --reload
```

Verify it's running: [http://localhost:8000](http://localhost:8000) — you should see `{"message": "Blog Writing Agent API is running"}`.

### 3. Set up the frontend

```bash
cd ../frontend
npm install
npm run dev
```

### 4. Run it

Type a topic like *"Introduction to LangGraph with real examples"* in the chat, and watch the agent research, plan, and write the article in front of you.

---

## 🔌 API Reference

Base URL: `/api/v1`

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/generate` | Generate a blog (`{ "topic": "...", "as_of": "YYYY-MM-DD", "session_id": "..." }`) |
| `GET` | `/blogs/{session_id}` | List blogs in a session |
| `GET` | `/blog/{blog_id}` | Fetch a single blog (404 if expired) |
| `DELETE` | `/blog/{blog_id}` | Delete a single blog |
| `DELETE` | `/blogs/{session_id}` | Delete all blogs in a session |

---

## 🐛 Finding & Reporting Bugs

This project is a work in progress, and **your help makes it better**, we welcome contributions. If something isn't working:

**Open an issue** (or a PR!) with:
   - A clear, short title.
   - Steps to reproduce.
   - Expected vs. actual behavior.
   - Screenshots or the API error response, if available.

---

## ⚠️ Known Issues

### Image Generation is Failed
The article *text* pipeline works end-to-end, but the **AI image generation step currently fails**, so generated articles come back without images.

- **Impact:** Blogs are still generated, complete, and downloadable — they just contain no AI images.
- **Where it happens:** the `generate_and_place_images` node in the reducer subgraph (`backend/app/graph/nodes/reducer.py`), which calls Google GenAI, saves the image to `backend/images/`, and serves it via the `/images` static mount.
- **Likely suspects to investigate:**
  - `GOOGLE_API_KEY` validity, quota, or model availability.
  - The image size/quality values in `ImageSpec` (the `decide_images` node already normalizes unusual sizes like `"1566x1536"` — verify the model accepts them).
  - Error handling in the image node — an exception here should degrade gracefully instead of failing the whole generation.
- **Status:** actively being worked on.

---

## Future Implementation

### 🌐 MCP Server for Publishing (planned)
The next major feature is a **Model Context Protocol (MCP) server** that connects the agent to real blog platforms such as **Medium**, Dev.to, and Hashnode.

How it will work:

1. The agent finishes writing the article and asks: *"Can I post it?"* (this confirmation step already exists in the UI today).
2. If the user says **yes**, the agent calls the MCP server for the chosen platform.
3. The MCP server authenticates, uploads the article (title, body, tags, cover image), and confirms the published URL back in the chat.

Other ideas on the board:
- Fix and polish AI image generation.
- Support for more download formats (HTML, DOCX).
- Streaming token-level output during generation.
- Multi-language blog generation.

---

## ✅ Conclusion

Blog Writing Agent is an end-to-end demonstration of what **graph-orchestrated multi-agent LLM systems** can do in a real product: it researches like a journalist, plans like an editor, and writes like an author — then hands you a polished, downloadable article. Whether you're exploring agent architectures, LangGraph, or just want a smarter way to produce technical content, this project is a great starting point.

Have an idea, a bug report, or a pull request? Contributions are very welcome. 🚀

---

*Built with ❤️ using LangGraph, FastAPI, React, and modern AI tools.*
