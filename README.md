
# 🧠 Haushaltsgeräte Assistent
**Version 0.3**

Ein lokal laufender Chatbot zur Analyse und Beantwortung von Fragen aus PDF-Bedienungsanleitungen für deine Haushaltsgeräte.  
Er nutzt `Flask`, `Ollama`, `ChromaDB` und ein lokal laufendes LLM (z. B. Mixtral oder LLaMA 3).  
Alle Daten bleiben **komplett offline auf deinem Gerät**. 🚀

![Banner](haushaltsgeraete_assistent_banner.png)

---

- Upload von beliebig vielen PDF- und DOCX-Bedienungsanleitungen
- Verarbeitung inkl. OCR bei Bedarf
- Intelligente Chunking-Strategie basierend auf Texttyp
- Volltextsuche mit Synonym-Fallback
- Lokaler Ollama-LLM-Chat mit Weboberfläche
- Feedbacksystem zum Fine-Tuning
- Dokumentverwaltung (Auswahl/Löschen)

---

## 🖥️ Voraussetzungen (Mac & Windows)

### 📦 1. Python & Miniconda

Empfohlen: [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

```bash
# für Mac
brew install --cask miniconda
```

```bash
# für Windows
# Lade Miniconda von https://docs.conda.io/en/latest/miniconda.html
# und installiere mit „Add to PATH“ aktiviert.
```

Dann:

```bash
conda create -n haushaltsgeraete-assistent python=3.11
conda activate haushaltsgeraete-assistent
```

---

### 🧰 2. Homebrew (Mac only)

Installiere [Homebrew](https://brew.sh/), falls noch nicht vorhanden:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Dann:

```bash
brew install tesseract ghostscript poppler
brew install ocrmypdf
```

---

## 📦 3. Python-Abhängigkeiten

```bash
pip install -r requirements.txt
```

---

## ⚙️ 4. Modell (Ollama)

Installiere [Ollama](https://ollama.com/) und lade ein Modell wie:

```bash
ollama pull mixtral:8x7b
# oder
ollama pull llama3:70b-instruct-q4_K_M
```

---

## ▶️ Starten der App

```bash
python app_0.3.py
```

Dann öffne im Browser:

```
http://localhost:5050
```

---

## 📁 Ordnerstruktur

```
├── app.py
├── uploads/
├── feedback/
├── chromadb/
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🧠 Modellwahl

| Modell | Qualität | RAM/VRAM |
|--------|----------|----------|
| `mixtral:8x7b` | ⭐⭐⭐⭐ | ca. 40 GB |
| `llama3:70b-instruct-q4_K_M` | ⭐⭐⭐⭐⭐ | ab 48 GB |
| `deepseek:chat` | ⭐⭐⭐⭐ | gute DE-Unterstützung |

---

## 🗑️ Löschung & Feedback

- Hochgeladene PDFs können einzeln gelöscht werden
- Chunks werden automatisch aus ChromaDB entfernt
- Feedback mit richtiger Antwort wird gespeichert (für Nachtraining geeignet)
