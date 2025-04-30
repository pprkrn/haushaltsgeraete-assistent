import chromadb
from chromadb import PersistentClient
from chromadb.config import Settings
import fitz  # PyMuPDF
import os

def read_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        full_text = ""
        for page in doc:
            text = page.get_text()
            if text:
                full_text += text + "\n"
        return full_text
    except Exception as e:
        print(f"Fehler beim Öffnen der PDF: {e}")
        return ""

def split_into_chunks(text, chunk_size=500, overlap=50):
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para[-overlap:] + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

if __name__ == "__main__":
    client = PersistentClient(path="./chromadb")

    collection = client.get_or_create_collection(name="bedienungsanleitungen")

    file_path = "beispiel_anleitung.pdf"  # oder dein Dateiname

    text = read_pdf(file_path)

    if text.strip():
        chunks = split_into_chunks(text)
        print(f"PDF in {len(chunks)} Chunks zerlegt. Speichere in ChromaDB...")

        for i, chunk in enumerate(chunks):
            collection.add(
                documents=[chunk],
                ids=[f"chunk_{i}"]
            )

        print("✅ Datenbank gespeichert unter ./chromadb/")  # << nur Info-Print
    else:
        print("❗ Kein Text extrahiert. Bitte prüfe die Datei.")
