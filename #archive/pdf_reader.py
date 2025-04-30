import fitz  # PyMuPDF
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer

def read_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        full_text = ""
        page_count = len(doc)
        print(f"PDF hat {page_count} Seiten. Extrahiere Text...")

        for i, page in enumerate(doc):
            try:
                text = page.get_text()
                if text:
                    full_text += text + "\n"
                print(f"Seite {i+1}/{page_count} gelesen.")
            except Exception as e:
                print(f"Fehler beim Lesen von Seite {i+1}: {e}")
                continue  # Fehlerhafte Seite überspringen

        return full_text

    except Exception as e:
        print(f"Fehler beim Öffnen der PDF: {e}")
        return ""

def split_into_chunks(text, chunk_size=500, overlap=50):
    # Erstmal den Text in Absätze splitten (wo \n\n vorkommt)
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + " "
        else:
            chunks.append(current_chunk.strip())
            # Baue neues Chunk auf, aber nimm etwas Overlap mit
            current_chunk = para[-overlap:] + " "

    # Falls noch Text im letzten Chunk ist
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks   

if __name__ == "__main__":
    # Hier deine neue (einfachere) PDF-Datei eintragen:
    file_path = "beispiel_anleitung.pdf"  # <-- ändere auf deinen neuen Dateinamen!

    text = read_pdf(file_path)

    if text:
        chunks = split_into_chunks(text)
        print(f"\nPDF wurde erfolgreich in {len(chunks)} Chunks aufgeteilt.")
        print("\nBeispiel-Chunk:\n")
        print(chunks[0])
    else:
        print("Kein Text extrahiert. Bitte prüfe die Datei.")
def get_english_synonyms(word):
    synonyms = set()
    for syn in wn.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace("_", " "))
    return list(synonyms)