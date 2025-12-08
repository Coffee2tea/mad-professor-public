import hashlib
import os
import threading
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

app = FastAPI()

# Settings
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


@dataclass
class Chunk:
    text: str
    doc_name: str
    idx: int


class DocStore:
    """Holds document chunks, embeddings, and FAISS index."""

    def __init__(self):
        self.lock = threading.Lock()
        self.model = None
        self.index = None
        self.chunks: List[Chunk] = []

    def _ensure_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(EMBED_MODEL_NAME)

    def _new_index(self, dim: int):
        import faiss  # type: ignore

        self.index = faiss.IndexFlatIP(dim)

    def reset(self):
        with self.lock:
            self.index = None
            self.chunks = []

    def _chunk_text(self, text: str, doc_name: str, chunk_size: int = 600, overlap: int = 100) -> List[Chunk]:
        words = text.split()
        chunks = []
        start = 0
        idx = 0
        while start < len(words):
            end = min(len(words), start + chunk_size)
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            chunks.append(Chunk(text=chunk_text, doc_name=doc_name, idx=idx))
            start = end - overlap
            if start < 0:
                start = 0
            idx += 1
        return chunks

    def _embed(self, texts: List[str]) -> np.ndarray:
        self._ensure_model()
        vectors = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return vectors.astype("float32")

    def add_document(self, name: str, text: str):
        """Reset index and load a new single document."""
        with self.lock:
            self.index = None
            self.chunks = []

            new_chunks = self._chunk_text(text, doc_name=name)
            if not new_chunks:
                return
            embeddings = self._embed([c.text for c in new_chunks])
            self._new_index(embeddings.shape[1])
            self.index.add(embeddings)
            self.chunks = new_chunks

    def query(self, question: str, k: int = 4) -> List[Chunk]:
        with self.lock:
            if self.index is None or not self.chunks:
                return []
            q_emb = self._embed([question])
            scores, idxs = self.index.search(q_emb, min(k, len(self.chunks)))
            top = []
            for i in idxs[0]:
                if 0 <= i < len(self.chunks):
                    top.append(self.chunks[i])
            return top


doc_store = DocStore()
chat_history: List[Tuple[str, str]] = []


def read_file_bytes_to_text(file: UploadFile) -> str:
    data = file.file.read()
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def summarize_with_openai(prompt: str) -> Optional[str]:
    api_key = os.getenv("AI_BUILDER_TOKEN") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=OPENAI_BASE_URL)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a calm mentor voice. Keep answers concise and grounded in the provided context.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


def build_prompt(question: str, contexts: List[Chunk]) -> str:
    ctx_block = "\n\n".join([f"[{c.doc_name} #{c.idx}] {c.text}" for c in contexts])
    return (
        "Answer the question using only the context. Keep the tone as a calm mentor voice.\n\n"
        f"Context:\n{ctx_block}\n\n"
        f"Question: {question}\nAnswer:"
    )


def generate_answer(question: str, contexts: List[Chunk]) -> str:
    if not contexts:
        return "Voice (calm mentor): I do not have any document loaded yet. Please upload text first."
    prompt = build_prompt(question, contexts)
    llm_answer = summarize_with_openai(prompt)
    if llm_answer:
        return llm_answer
    # Fallback: simple extractive answer from top chunk
    primary = contexts[0].text[:400].replace("\n", " ")
    return f"Voice (calm mentor): Based on the document, here is a related passage: {primary}"


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Mad Professor Web</title>
      <style>
        :root { color-scheme: dark; }
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #0b1221; color: #e2e8f0; }
        header { padding: 20px; background: linear-gradient(90deg, #7c3aed, #2563eb); color: #fff; }
        main { padding: 20px; max-width: 1100px; margin: 0 auto; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
        .card { background: #0f172a; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); }
        .card h2 { margin-top: 0; }
        input[type="file"], textarea, input[type="text"] { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #1f2937; background: #0b1221; color: #e2e8f0; }
        button { background: #2563eb; color: #fff; border: none; padding: 10px 14px; border-radius: 8px; cursor: pointer; }
        button.secondary { background: #1f2937; }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .status { font-size: 0.9rem; color: #a5b4fc; }
        .chat { max-height: 420px; overflow-y: auto; padding: 8px; border: 1px solid #1f2937; border-radius: 8px; background: #0b1221; }
        .msg { margin-bottom: 12px; padding: 10px; border-radius: 8px; }
        .user { background: #1f2937; }
        .bot { background: #111827; }
        .sources { font-size: 0.85rem; color: #cbd5f5; }
      </style>
    </head>
    <body>
      <header>
        <h1>Mad Professor · Web</h1>
        <p>Upload a document, then ask questions. Answers are grounded in the uploaded text with a calm mentor voice.</p>
      </header>
      <main>
        <div class="grid">
          <div class="card">
            <h2>Document</h2>
            <form id="uploadForm">
              <label>Upload text file</label>
              <input type="file" name="file" accept=".txt" />
              <p style="text-align:center;margin:10px 0;">— or —</p>
              <label>Paste text</label>
              <textarea name="pastedText" rows="6" placeholder="Paste text here..."></textarea>
              <div style="margin-top:10px;">
                <button type="submit">Save Document</button>
                <span id="docStatus" class="status"></span>
              </div>
            </form>
          </div>
          <div class="card">
            <h2>Ask</h2>
            <form id="askForm">
              <label>Your question</label>
              <input type="text" name="question" placeholder="Ask about the document..." required />
              <div style="margin-top:10px;">
                <button type="submit">Ask</button>
                <span id="askStatus" class="status"></span>
              </div>
            </form>
          </div>
        </div>
        <div class="card" style="margin-top:16px;">
          <h2>Conversation</h2>
          <div id="chat" class="chat"></div>
        </div>
      </main>
      <script>
        const uploadForm = document.getElementById('uploadForm');
        const askForm = document.getElementById('askForm');
        const docStatus = document.getElementById('docStatus');
        const askStatus = document.getElementById('askStatus');
        const chat = document.getElementById('chat');

        const history = [];

        function addMessage(role, text, sources=[]) {
          const div = document.createElement('div');
          div.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
          div.innerHTML = '<strong>' + (role === 'user' ? 'You' : 'Mad Professor') + ':</strong><br>' + text.replace(/\\n/g, '<br>');
          if (sources.length) {
            const src = document.createElement('div');
            src.className = 'sources';
            src.textContent = 'Sources: ' + sources.join(' | ');
            div.appendChild(src);
          }
          chat.appendChild(div);
          chat.scrollTop = chat.scrollHeight;
        }

        uploadForm.addEventListener('submit', async (e) => {
          e.preventDefault();
          const formData = new FormData(uploadForm);
          docStatus.textContent = 'Saving...';
          const res = await fetch('/upload', { method: 'POST', body: formData });
          const data = await res.json();
          docStatus.textContent = data.message || 'Saved';
        });

        askForm.addEventListener('submit', async (e) => {
          e.preventDefault();
          const formData = new FormData(askForm);
          const question = formData.get('question');
          addMessage('user', question);
          askStatus.textContent = 'Thinking...';
          const res = await fetch('/ask', { method: 'POST', body: formData });
          const data = await res.json();
          askStatus.textContent = data.message || '';
          addMessage('bot', data.answer || '(no answer)', data.sources || []);
          askForm.reset();
        });
      </script>
    </body>
    </html>
    """


@app.post("/upload")
async def upload(file: UploadFile | None = File(None), pastedText: str = Form("")):
    text = pastedText.strip()
    filename = None
    if file and file.filename:
        filename = file.filename
        text_from_file = read_file_bytes_to_text(file)
        if text_from_file:
            text = text_from_file
    if not text:
        return JSONResponse({"message": "No text provided"}, status_code=400)

    name = filename or "pasted-text"
    doc_store.add_document(name, text)
    chat_history.clear()
    return {"message": f"Stored document ({name}) with {len(text)} characters"}


@app.post("/ask")
async def ask(question: str = Form(...)):
    if not question.strip():
        return JSONResponse({"message": "Question is empty", "answer": ""}, status_code=400)
    contexts = doc_store.query(question)
    answer = generate_answer(question, contexts)
    sources = [f"{c.doc_name} #{c.idx}" for c in contexts]
    chat_history.append((question, answer))
    return {"message": "ok", "answer": answer, "sources": sources}


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"


def get_port() -> int:
    try:
        return int(os.getenv("PORT", "8000"))
    except ValueError:
        return 8000
