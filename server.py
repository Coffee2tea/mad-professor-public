import os
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

app = FastAPI()

# In-memory store for the latest uploaded document text.
CURRENT_DOC: dict[str, Optional[str]] = {"text": None, "filename": None}


def read_file_bytes_to_text(file: UploadFile) -> str:
    data = file.file.read()
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


@app.get("/", response_class=HTMLResponse)
async def root():
    # Simple single-page UI: upload text file or paste text, then ask questions.
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Mad Professor Web</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #0f172a; color: #e2e8f0; }
        header { padding: 20px; background: linear-gradient(90deg, #7c3aed, #2563eb); color: #fff; }
        main { padding: 20px; max-width: 900px; margin: 0 auto; }
        .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); }
        .card h2 { margin-top: 0; }
        input[type="file"], textarea, input[type="text"] { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #1f2937; background: #0b1221; color: #e2e8f0; }
        button { background: #2563eb; color: #fff; border: none; padding: 10px 14px; border-radius: 8px; cursor: pointer; }
        button.secondary { background: #1f2937; }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .status { font-size: 0.9rem; color: #a5b4fc; }
        .answer { white-space: pre-wrap; }
      </style>
    </head>
    <body>
      <header>
        <h1>Mad Professor · Web</h1>
        <p>Upload a document or paste text, then ask questions. Includes a “voice” style in responses.</p>
      </header>
      <main>
        <div class="card">
          <h2>1) Provide Document</h2>
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
          <h2>2) Ask a Question</h2>
          <form id="askForm">
            <label>Your question</label>
            <input type="text" name="question" placeholder="Ask about the document..." required />
            <div style="margin-top:10px;">
              <button type="submit">Ask</button>
              <span id="askStatus" class="status"></span>
            </div>
          </form>
          <div style="margin-top:12px;">
            <strong>Answer (with voice style):</strong>
            <div id="answer" class="answer"></div>
          </div>
        </div>
      </main>
      <script>
        const uploadForm = document.getElementById('uploadForm');
        const askForm = document.getElementById('askForm');
        const docStatus = document.getElementById('docStatus');
        const askStatus = document.getElementById('askStatus');
        const answerEl = document.getElementById('answer');

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
          askStatus.textContent = 'Thinking...';
          answerEl.textContent = '';
          const res = await fetch('/ask', { method: 'POST', body: formData });
          const data = await res.json();
          askStatus.textContent = data.message || '';
          answerEl.textContent = data.answer || '(no answer)';
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

    CURRENT_DOC["text"] = text
    CURRENT_DOC["filename"] = filename or "pasted-text"
    return {"message": f"Stored document ({CURRENT_DOC['filename']}) with {len(text)} chars"}


@app.post("/ask")
async def ask(question: str = Form(...)):
    doc = CURRENT_DOC.get("text")
    if not doc:
        return JSONResponse({"message": "Upload or paste a document first", "answer": ""}, status_code=400)

    # Simple heuristic answer: echo back a brief snippet and include a voice style tag.
    snippet = doc[:280].replace("\n", " ")
    answer_text = f"Voice (calm mentor): Based on the document, here is a related note: {snippet}"
    return {"message": "ok", "answer": answer_text}


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"


def get_port() -> int:
    try:
        return int(os.getenv("PORT", "8000"))
    except ValueError:
        return 8000
