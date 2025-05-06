# Changelog

## [app_0.3] – Migration auf LangChain RAG
**Datum:** 2025-05-06

### Hinzugefügt
- **LangChain-Integration**  
  - Verwendung von `langchain_chroma.Chroma` als Vectorstore statt direktem ChromaDB-Client  
  - Fallback-Logik, um bei fehlerhafter/älterer Collection-Konfiguration das `./chromadb`-Verzeichnis zu löschen und neu anzulegen  
  - Einbindung von `langchain_community.retrievers.BM25Retriever` für synonymfähige Retrieva  
  - Nutzung von `RecursiveCharacterTextSplitter` zum flexiblen Chunking

- **Upload und Speicherung**  
  - `upload`-Route fügt Dokumente jetzt per `vectorstore.add_documents(...)` mit Metadaten hinzu  
  - Unterstützung für PDF- und DOCX-Uploads (führt OCR oder `python-docx` aus)

- **Retrieval & QA**  
  - Ersetzen von `collection.query(...)` durch `retriever.get_relevant_documents(...)`  
  - Frage-Endpoint baut Prompt aus den über LangChain geretrieveten Dokumenten  
  - Metadaten-Anker (`source`) aus den Document-Objekten im Frontend ausgegeben

### Geändert
- **Routen-Logik**  
  - `/delete` löscht nur noch die Datei im Upload-Ordner (einfachere Handhabung)  
  - `/ask` liefert jetzt Quellen-Array aus den LangChain-Docs  
- **Abhängigkeiten**  
  - Entfernen älterer ChromaDB-Imports, Ersetzen durch `langchain_chroma` & `langchain_community`  
  - Aktualisierung aller LangChain-Imports gemäß v0.2+  
- **Frontend**  
  - Akzeptanz von `.docx` in der File-Input-Form  
  - Keine eigene Anzeige aller Chunks mehr, stattdessen Metadaten-Liste im rechten Panel  

---

## [app_0.2] – ChatGPT-Anbindung & DOCX-Support
**Datum:** 2025-05-05

### Hinzugefügt
- **OpenAI/ChatGPT-Integration**  
  - Einlesen von `OPENAI_API_KEY` via `python-dotenv`  
  - Neuer Client `openai_client = OpenAI(...)`  
  - Auswahl-Dropdown für GPT-Modelle (`gpt-4-turbo`, `gpt-4o`) im Frontend  
  - `/ask`-Route leitet je nach Auswahl an OpenAI oder Ollama weiter

- **DOCX-Upload**  
  - Unterstützung für `.docx`-Dateien via `python-docx`  
  - Extraktion der Absätze und Chunking analog zu PDF

### Geändert
- Erweiterung der HTML-Maske um Modell-Auswahl und Hinweis bei Download  
- Anpassung der `/ask`-Logik:  
  - Prüfung auf OpenAI-Modelle vs. lokale LLM via Ollama  
  - Fehlermeldung/Download-Hinweis bei fehlendem Ollama-Modell  

---

## [app_0.1] – Ausgangsversion mit ChromaDB & Ollama
**Datum:** 2025-05-01

- Basis-Setup mit Flask, ChromaDB `PersistentClient`, Ollama-LLM  
- PDF-Upload, OCR mit `ocrmypdf`, Text-Chunking nach Format (Fließtext, Stichpunkt, Seitenumbrüche)  
- `/ask`-Route: manuelles Query der ChromaDB mit `collection.query(...)`  
- Einfaches Chat-Frontend ohne Online-Modelle oder DOCX-Support  