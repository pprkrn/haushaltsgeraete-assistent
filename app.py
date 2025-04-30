from flask import Flask, request, jsonify, render_template_string
from chromadb import PersistentClient
import ollama
import re
import os
import fitz  # PyMuPDF
import json
from datetime import datetime

def clean_question(q):
    return q.strip().lower()

# Flask App
app = Flask(__name__)

# ChromaDB Verbindung
client = PersistentClient(path="./chromadb")
collection = client.get_collection(name="bedienungsanleitungen")

# Minimal-HTML für den Browser-Chat mit Upload-Formular
HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Haushaltsgeräte Assistent</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f7;
            color: #1c1c1e;
            margin: 0;
            padding: 40px;
            line-height: 1.5;
        }
        h1, h2, h3 {
            color: #111;
        }
        input[type="text"], select, textarea {
            width: 100%;
            max-width: 400px;
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #ccc;
            border-radius: 12px;
            font-size: 16px;
            background-color: white;
        }
        input[type="file"] {
            margin-top: 5px;
            font-size: 14px;
        }
        input[type="range"] {
            width: 300px;
        }
        button {
            background-color: #007aff;
            color: white;
            padding: 10px 16px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 5px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #005bb5;
        }
        form {
            margin-bottom: 20px;
        }
        #response {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin-top: 20px;
            max-width: 800px;
        }
        ul {
            padding-left: 20px;
        }
        #upload-status, #delete-status {
            margin-top: 10px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>Haushaltsgeräte Assistent</h1>
    <form id="chat-form" onsubmit="return false;">
        <div style="display: flex; gap: 10px; align-items: center;">
            <input type="text" id="question" placeholder="Deine Frage..." style="flex: 1; max-width: 400px; padding: 10px;">
            <button type="submit" style="padding: 10px 16px;">Fragen</button>
        </div>
        <br>
        <label for="num-results">Anzahl der Fundstellen: <span id="slider-value">4</span></label><br>
        <input type="range" id="num-results" name="num-results" min="1" max="10" value="4">
        <br>
        <label for="active-pdfs">PDFs, die bei der Antwort berücksichtigt werden:</label><br>
        <div id="active-pdfs-container" style="max-height: 150px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 12px; min-width: 300px; width: fit-content; max-width: 100%; white-space: nowrap;"></div>
    </form>
    <div id="response" style="margin-top: 20px;"></div>

    <hr style="margin: 40px 0;">

    <h2>Neue PDF-Anleitung hochladen</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="pdf_file" accept=".pdf" required>
        <button type="submit">Hochladen & Integrieren</button>
    </form>

    <div id="upload-status" style="margin-top: 20px; color: green;"></div>
    <div id="pdf-list" style="margin-top: 20px;">
        <h3>Hochgeladene Anleitungen:</h3>
        <ul id="pdf-files"></ul>
        <h3>PDF-Anleitung löschen</h3>
        <form id="delete-form">
            <select id="delete-select"></select>
            <button type="submit">Löschen</button>
        </form>
        <div id="delete-status" style="margin-top: 10px; color: red;"></div>
    </div>
    <script>
        async function loadUploadedPDFs() {
            const res = await fetch('/list-pdfs');
            const data = await res.json();
            const list = document.getElementById('pdf-files');
            list.innerHTML = "";
            data.files.forEach(f => {
                const li = document.createElement('li');
                li.textContent = f;
                list.appendChild(li);
            });
        }

        async function updateDeleteSelect() {
            const res = await fetch('/list-pdfs');
            const data = await res.json();
            const select = document.getElementById('delete-select');
            select.innerHTML = "";
            data.files.forEach(f => {
                const option = document.createElement('option');
                option.value = f;
                option.textContent = f;
                select.appendChild(option);
            });
        }

        async function updateActiveSelect() {
            const res = await fetch('/list-pdfs');
            const data = await res.json();
            const container = document.getElementById('active-pdfs-container');
            container.innerHTML = "";
            data.files.forEach(f => {
                const label = document.createElement('label');
                label.style.display = "block";
                label.style.whiteSpace = "nowrap";
                const checkbox = document.createElement('input');
                checkbox.type = "checkbox";
                checkbox.name = "active-pdfs";
                checkbox.value = f;
                checkbox.checked = true;
                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(" " + f));
                container.appendChild(label);
            });
        }

        document.querySelector('form[action="/upload"]').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const formData = new FormData(form);
            const statusDiv = document.getElementById('upload-status');
            statusDiv.textContent = "⏳ Hochladen...";
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.text();
            statusDiv.textContent = result;
            await loadUploadedPDFs();
            await updateDeleteSelect();
            await updateActiveSelect();
        });

        document.getElementById('chat-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const questionInput = document.getElementById('question');
            const rawQuestion = questionInput.value;
            const responseDiv = document.getElementById('response');
            if (!rawQuestion.trim()) {
                responseDiv.textContent = "Bitte gib eine Frage ein.";
                return;
            }
            responseDiv.textContent = "⏳ Einen Moment, ich denke nach...";
            const numResults = document.getElementById('num-results').value;
            const selectedPDFs = Array.from(document.querySelectorAll('input[name="active-pdfs"]:checked')).map(cb => cb.value);
            const res = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: rawQuestion,
                    num_results: parseInt(numResults),
                    active_pdfs: selectedPDFs
                })
            });
            const data = await res.json();
            const question = rawQuestion.trim();
            document.getElementById('question').value = question;
            let sourceHTML = "";
            if (data.sources && data.sources.length > 0) {
                sourceHTML = "<br><br><b>Fundstellen (sortiert nach Relevanz):</b><ul>";
                for (let [id, text] of data.sources) {
                    sourceHTML += `<li><b>${id}</b>: ${text}</li>`;
                }
                sourceHTML += "</ul>";
            }

            let resultHTML = "<b>Antwort:</b><br>" + data.answer;
            resultHTML += `
                <br><br><b>War die Antwort hilfreich?</b><br>
                <button id="feedback-yes">👍 Ja</button>
                <button id="feedback-no">👎 Nein</button>
                <div id="feedback-form" style="display:none; margin-top:10px;">
                    <textarea id="correct-answer" rows="4" style="width:100%;" placeholder="Wie hätte die Antwort lauten sollen?"></textarea><br>
                    <button id="submit-feedback">Feedback absenden</button>
                </div>
            `;
            resultHTML += sourceHTML;
            responseDiv.innerHTML = resultHTML;

            document.getElementById('feedback-yes').addEventListener('click', async () => {
                await fetch('/feedback', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        question: rawQuestion,
                        given_answer: data.answer,
                        correct: true
                    })
                });
                alert("Danke für dein Feedback!");
            });

            document.getElementById('feedback-no').addEventListener('click', () => {
                document.getElementById('feedback-form').style.display = 'block';
            });

            document.getElementById('submit-feedback').addEventListener('click', async () => {
                const correction = document.getElementById('correct-answer').value;
                await fetch('/feedback', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        question: rawQuestion,
                        given_answer: data.answer,
                        correct: false,
                        corrected_answer: correction
                    })
                });
                alert("Danke für deine Korrektur!");
                document.getElementById('feedback-form').style.display = 'none';
            });
        });

        document.getElementById('num-results').addEventListener('input', function(e) {
            document.getElementById('slider-value').textContent = e.target.value;
        });

        document.getElementById('delete-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const filename = document.getElementById('delete-select').value;
            const res = await fetch('/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ filename })
            });
            const msg = await res.text();
            document.getElementById('delete-status').textContent = msg;
            await loadUploadedPDFs();
            await updateDeleteSelect();
            await updateActiveSelect();
        });

        window.addEventListener("load", () => {
            loadUploadedPDFs();
            updateDeleteSelect();
            updateActiveSelect();
        });
    </script>
</body>
</html>
"""

# Route: Browser-Seite
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    raw_question = data.get("question", "")
    question = clean_question(raw_question)
    print(f"Bereinigte Frage: '{question}' (Original: '{raw_question}')")

    # Ähnlichste Fundstellen abrufen
    results = collection.query(
        query_texts=[question],
        n_results=data.get("num_results", 4)  # kannst du anpassen
    )
    print("🎯 Gefundene IDs (vor Filter):", results["ids"][0])
    print("✅ Aktive PDFs im Frontend:", data.get("active_pdfs", []))

    active_pdfs = data.get("active_pdfs", [])
    if not active_pdfs:
        # Wenn keine Auswahl im Frontend getroffen wurde, verwende alle PDFs
        print("⚠️ Keine PDF-Auswahl im Frontend – verwende alle Einträge.")
        filtered = list(zip(results["ids"][0], results["documents"][0], results["distances"][0]))
    else:
        filtered = [(id_, doc, dist) for id_, doc, dist in zip(
            results["ids"][0], results["documents"][0], results["distances"][0]
        ) if any(id_.startswith(f"{pdf}_") for pdf in active_pdfs)]

    filtered.sort(key=lambda x: x[2])
    print("🧃 IDs nach Filter:", [id_ for id_, _, _ in filtered])
    if not filtered:
        print("🌀 Versuche erneute Abfrage mit unbearbeiteter Frage…")
        results = collection.query(
            query_texts=[raw_question],
            n_results=data.get("num_results", 4)
        )
        filtered = [(id_, doc, dist) for id_, doc, dist in zip(
            results["ids"][0], results["documents"][0], results["distances"][0]
        ) if any(id_.startswith(f"{pdf}_") for pdf in active_pdfs)] if active_pdfs else list(zip(results["ids"][0], results["documents"][0], results["distances"][0]))

        filtered.sort(key=lambda x: x[2])
        print("🧃 IDs nach Re-Try:", [id_ for id_, _, _ in filtered])

        if not filtered:
            return jsonify({
                "answer": "Entschuldigung, keine passenden Informationen gefunden. Stelle sicher, dass eine passende Anleitung ausgewählt ist.",
                "sources": []
            })
    ids, chunks, _ = zip(*filtered) if filtered else ([], [], [])

    # Modellkontext begrenzen (z. B. auf 12000 Zeichen ≈ 4000 Tokens)
    max_chars_context = 12000
    context = ""
    for chunk in chunks:
        if len(context) + len(chunk) > max_chars_context:
            break
        context += chunk + "\n\n"
    print(f"📏 Kontextgröße: {len(context)} Zeichen")

    # Prompt fürs LLM
    prompt = f"""
Du bist ein smarter Haushaltsgeräte-Assistent.
Beantworte die folgende Nutzerfrage basierend ausschließlich auf den unten angegebenen Auszügen (Kontext) aus Bedienungsanleitungen.

**Wichtig:**
- Gib eine vollständige, direkte Antwort.
- Formuliere eigenständig und verständlich.
- Füge keine erfundenen Informationen hinzu.
- Antworte bitte in natürlichem, klarem und freundlichem DEUTSCH.
- Wenn im Kontext keine passende Information enthalten ist, antworte ehrlich mit: "Entschuldigung, dazu habe ich in der Anleitung keine Information gefunden."

--- Kontext der Anleitung ---
{context}
------------------------------------

Frage: {question}
Antwort:
"""

    response = ollama.generate(
        model="mixtral:8x7b",
        prompt=prompt
    )

    return jsonify({
        "answer": response['response'],
        "sources": list(zip(ids, chunks))
    })

import tempfile
import subprocess

def read_pdf(path):
    # Erstelle temporäre OCR-Version
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        ocr_path = tmp.name

    print(f"🔍 Starte OCR für: {path}")
    try:
        subprocess.run(
            ["ocrmypdf", "--force-ocr", "--deskew", "--rotate-pages", path, ocr_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ OCR fehlgeschlagen: {e}")
        return ""

    # Text aus OCR-Version extrahieren
    text = ""
    with fitz.open(ocr_path) as doc:
        for page in doc:
            text += page.get_text("text")
    return text

def detect_pdf_style(text):
    lines = text.splitlines()
    avg_line_length = sum(len(l) for l in lines) / max(len(lines), 1)
    ratio_short_lines = sum(1 for l in lines if len(l.strip()) < 40) / max(len(lines), 1)

    if ratio_short_lines > 0.4 and avg_line_length < 60:
        return "stichpunktartig"
    elif any("Seite" in l or re.match(r"[-–]\s*\d+\s*[-–]", l) for l in lines[:10]):
        return "mit_seitenumbruechen"
    else:
        return "fliesstext"

def adaptive_chunk(text, style, max_chars=1000):
    if style == "fliesstext":
        paragraphs = text.split("\n\n")
    elif style == "stichpunktartig":
        paragraphs = re.split(r"\n[-•*●]\s*", text)
    elif style == "mit_seitenumbruechen":
        paragraphs = re.split(r"(\n-{2,}\n|\n\s*Seite\s*\d+\s*\n)", text)
    else:
        paragraphs = text.split("\n\n")

    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) < max_chars:
            current += p.strip() + "\n"
        else:
            chunks.append(current.strip())
            current = p.strip() + "\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks

def split_into_chunks(text, max_chars=500):
    style = detect_pdf_style(text)
    return adaptive_chunk(text, style, max_chars=max_chars)

@app.route("/upload", methods=["POST"])
def upload():
    if "pdf_file" not in request.files:
        return "Keine Datei ausgewählt", 400
    file = request.files["pdf_file"]
    if file.filename == "":
        return "Ungültiger Dateiname", 400
    path = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(path)

    print(f"📥 Neue Anleitung empfangen: {file.filename}")

    # Text extrahieren und einfügen
    text = read_pdf(path)
    chunks = split_into_chunks(text)
    

    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            ids=[f"{file.filename}_chunk_{i}"]
        )
    return f"✅ Anleitung '{file.filename}' erfolgreich integriert. ({len(chunks)} Abschnitte)"

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/list-pdfs")
def list_pdfs():
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        return jsonify(files=[])
    files = [f for f in os.listdir(upload_dir) if f.endswith(".pdf")]
    return jsonify(files=files)

@app.route("/delete", methods=["POST"])
def delete_pdf():
    data = request.get_json()
    filename = data.get("filename", "")
    if not filename:
        return "Kein Dateiname angegeben", 400

    results = collection.get()
    to_delete = [id for id in results["ids"] if id.startswith(f"{filename}_")]

    msg = ""
    if to_delete:
        collection.delete(ids=to_delete)
        msg = f"✅ {len(to_delete)} Einträge für '{filename}' gelöscht."
    else:
        msg = f"⚠️ Keine Einträge für '{filename}' gefunden."

    # Auch die Datei im uploads-Ordner löschen
    file_path = os.path.join("uploads", filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    return msg

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    os.makedirs("feedback", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"feedback/feedback_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return "Feedback gespeichert"


# Route: Zeige alle Chunks zu einer PDF
@app.route("/show_chunks/<pdf_id>")
def show_chunks(pdf_id):
    results = collection.get()
    chunks = [
        (id_, doc) for id_, doc in zip(results["ids"], results["documents"])
        if id_.startswith(f"{pdf_id}_")
    ]
    if not chunks:
        return f"Keine Chunks gefunden für: {pdf_id}"
    html = "<h2>Gespeicherte Chunks zu {}</h2><hr>".format(pdf_id)
    for id_, doc in chunks:
        html += f"<b>{id_}</b><br><pre>{doc}</pre><hr>"
    return html

# App starten
if __name__ == "__main__":
    app.run(debug=True)
