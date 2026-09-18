# Dalil AI | دليل

Dalil AI is a private workspace for asking questions about your own documents.
You can upload a PDF, Word file, spreadsheet, Markdown file, or plain text, then
ask questions in English or Arabic. Dalil finds the relevant passages, sends
only that context to a local Qwen model, and returns an answer with its sources.

I built Dalil because searching through several files by hand becomes slow very
quickly. The goal is simple: keep the documents organized, make their contents
searchable, and let every answer show where it came from.

## Main features

- Private accounts with separate document libraries.
- Upload support for PDF, DOCX, TXT, Markdown, XLSX, and XLSM files.
- Text extraction from paragraphs, Word tables, and spreadsheet rows.
- Questions in English or Arabic, including Arabic questions about English files.
- Search across the full library or one selected document.
- Automatic detection when a question mentions a filename such as `report.pdf`.
- Source-grounded answers with filenames, passage numbers, and match scores.
- Voice questions using local Whisper transcription.
- Saved chat history in the browser, with resumable and deletable conversations.
- Responsive English and Arabic interface with proper LTR and RTL layouts.
- One-command Docker startup with automatic prerequisite and health checks.

## How I built it

Dalil has two main workflows: one prepares documents for search, and the other
answers questions.

### Document ingestion

```text
Upload or pasted text
        |
        v
Validate file and extract text
        |
        v
Split text into overlapping passages
        |
        +----> Save document metadata and content in SQLite
        |
        v
Create local sentence-transformer embeddings
        |
        v
Store vectors and user/document metadata in Pinecone
```

Each passage receives a stable ID based on its document and position. Overlap
between passages helps preserve meaning when a useful sentence crosses a chunk
boundary. If indexing fails, Dalil removes the incomplete database and vector
records instead of leaving a half-imported document behind.

### Question answering

```text
Question
   |
   +----> Detect a mentioned filename and language
   |
   +----> Translate Arabic to English for stronger vector retrieval
   |      while preserving the original Arabic question
   v
Create query embedding -> Pinecone similarity search
   |
   v
Build a small context from the best matching passages
   |
   v
Local Qwen model -> answer in the question's language
   |
   v
Answer + source references -> saved chat interface
```

The model is instructed to use only the retrieved document context. It receives
the original question so an Arabic question produces an Arabic answer even when
the source document is written in English.

## Technology stack

| Part | Technology | Role |
| --- | --- | --- |
| Frontend | Next.js 16, React 19, TypeScript | Chat interface, document library, authentication screens, and API proxy |
| Styling | Tailwind CSS 4 | Responsive dark UI and Arabic RTL layout |
| Backend | FastAPI and Pydantic | API routes, validation, and service orchestration |
| Authentication | Argon2 and opaque cookie sessions | Password hashing and private user sessions |
| Local storage | SQLite | Users, sessions, document text, and metadata |
| Embeddings | Sentence Transformers | Local vector creation for documents and questions |
| Vector search | Pinecone | Semantic passage retrieval with user-level filtering |
| Answer model | Ollama with Qwen 3 8B | Local grounded answer generation and Arabic query translation |
| Speech | faster-whisper | Local voice transcription |
| File readers | pypdf, python-docx, openpyxl | PDF, Word, and Excel extraction |
| Packaging | Docker Compose | Reproducible backend and frontend services |
| Testing | pytest and ESLint | Backend behavior and frontend quality checks |

## Computer requirements

Dalil runs its answer and speech models locally, so it needs more memory than a
typical website.

### Minimum

- Windows 10 or Windows 11, 64-bit, with WSL 2 support.
- 4-core modern CPU.
- 16 GB RAM.
- About 15 GB of free disk space for Docker, Qwen, Whisper, dependencies, and caches.
- Stable internet connection for the first installation and Pinecone requests.
- A Pinecone account and API key.

### Recommended

- 6-core or better CPU.
- 24–32 GB RAM for smoother model use while Docker is running.
- SSD with at least 25 GB free.
- NVIDIA GPU with 8 GB or more VRAM if Ollama is configured to use it. A GPU is
  optional; the application works on CPU, but answers will take longer.

The first startup is the slowest because Docker builds the images and downloads
model dependencies. Later starts reuse Docker layers and local model caches.

## Start everything with one command

### Double-click on Windows

Open the project folder and double-click:

```text
Start Dalil AI.cmd
```

The launcher shows startup progress, opens the browser when Dalil is ready, and
displays the frontend, API, and health-check addresses. You can close the
launcher window after startup; Docker keeps the application running.

To stop the application, double-click:

```text
Stop Dalil AI.cmd
```

### PowerShell command

Open PowerShell in the project folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-dalil.ps1
```

When startup finishes, Dalil opens at [http://localhost:3000](http://localhost:3000).

To stop the containers:

```powershell
docker compose down
```

Your SQLite database and uploaded files stay in `data/`, so stopping or
rebuilding the containers does not remove your library.

## What the startup automation does

The `scripts/start-dalil.ps1` pipeline is designed for both daily use and a new
Windows computer. It performs these steps in order:

1. Checks whether Docker Desktop is installed.
2. Attempts installation through `winget` when Docker is missing.
3. Starts Docker Desktop and waits for its engine.
4. Checks whether Ollama is installed and attempts installation when needed.
5. Configures and starts Ollama so the backend container can reach it.
6. Checks for `qwen3:8b` and downloads it if it is missing.
7. Creates `.env` from `.env.example` when necessary.
8. Requests a Pinecone API key if one is not configured.
9. Stops old Dalil containers and clears ports `3000` and `8000`.
10. Builds CPU-optimized Docker images and starts both services.
11. Waits for the FastAPI health check and Next.js response.
12. Tests the connection from the backend container to Ollama.
13. Opens Dalil in the default browser only after everything is ready.

A fresh Docker Desktop installation can require a Windows restart. If the script
asks for one, restart the computer and run the same command again.

## Docker services

The Compose setup runs two containers:

- `frontend`: the production Next.js server on port `3000`.
- `backend`: the FastAPI server on port `8000`.

Ollama stays on Windows so it can use the machine's native CPU or GPU setup. The
backend connects to it through `host.docker.internal`. The backend image uses
CPU-only PyTorch to avoid downloading unnecessary CUDA libraries.

Useful Docker commands:

```powershell
# Show service status
docker compose ps

# Follow application logs
docker compose logs -f backend frontend

# Rebuild and restart manually
docker compose up -d --build

# Stop the application
docker compose down
```

## Project structure

```text
app/
  api/             FastAPI routes for auth, documents, questions, and speech
  database/        SQLite connection and repositories
  dependencies/    Authentication dependencies
  models/          Internal document, chunk, and user models
  schemas/         Request and response models
  services/        Extraction, chunking, embeddings, retrieval, RAG, and speech

frontend/
  app/             Next.js page, layout, and global styles
  components/      Authentication, document dialogs, answers, and branding
  lib/             API client, translations, and shared TypeScript types

scripts/
  start-dalil.ps1  Automated Windows and Docker startup pipeline
  live_smoke_test.py
  contexta_test_pack.py

tests/             Backend unit and API tests
data/              Persistent database, uploads, and runtime logs
compose.yaml       Frontend/backend Docker orchestration
Dockerfile         CPU-optimized backend image
```

## Configuration

Copy `.env.example` to `.env` only when configuring the project manually. The
startup script does this automatically.

| Variable | Default | Purpose |
| --- | --- | --- |
| `PINECONE_API_KEY` | none | Required credential for vector storage |
| `PINECONE_INDEX_NAME` | `local-ai-documenter` | Pinecone index name |
| `OLLAMA_MODEL` | `qwen3:8b` | Local answer model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama URL outside Docker; Compose overrides it for the backend |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Local embedding model |
| `CHUNK_SIZE` | `1000` | Maximum passage length in characters |
| `CHUNK_OVERLAP` | `150` | Repeated characters between passages |
| `TOP_K` | `5` | Maximum retrieved passages per question |
| `MAX_UPLOAD_BYTES` | `20971520` | Maximum upload size, currently 20 MB |
| `WHISPER_MODEL` | `small` | Local speech-recognition model |
| `AUTH_SESSION_DAYS` | `7` | Login session lifetime |

Never commit `.env`; it contains the Pinecone API key.

## Manual development setup

Docker is the easiest way to run Dalil. For active development, the services can
also run directly on Windows.

### Backend

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Add `PINECONE_API_KEY` to `.env` and make sure Ollama is running with
`qwen3:8b` before asking questions.

### Frontend

Run this in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

## Tests

Run the backend test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Check the frontend:

```powershell
cd frontend
npm run lint
npm run build
```

Run a live end-to-end question test when Pinecone and Ollama are available:

```powershell
.\.venv\Scripts\python.exe scripts\live_smoke_test.py
```

## Data and privacy

- Passwords are hashed with Argon2 and are never stored as plain text.
- Browser authentication uses opaque HttpOnly session cookies.
- SQLite data, uploads, embeddings, Qwen inference, and Whisper run locally.
- Pinecone stores document vectors and their user/document metadata remotely.
- The browser communicates with the Next.js server; it never receives Pinecone
  or Ollama credentials.
- Chat history is currently saved per user in that browser's local storage.

For an internet-facing deployment, use HTTPS, set `AUTH_COOKIE_SECURE=true`, add
rate limiting and backups, and replace local SQLite with persistent managed
storage when running more than one backend instance.
