"""Process documents: clean text, split into chunks, save to DB."""

import re
from .extractors import extract_text


def clean_text(text):
    """Remove excessive whitespace and normalize the text."""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into overlapping chunks of words.
    chunk_size = words per chunk
    overlap    = words shared between consecutive chunks (keeps context)
    """
    if not text:
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(' '.join(chunk_words))
        start += chunk_size - overlap
        if end >= len(words):
            break

    return chunks


def process_document(document):
    """
    Full pipeline:
      1. Extract text from the uploaded file
      2. Clean it
      3. Split into chunks
      4. Save chunks to database
      5. Mark document as processed
    Returns: number of chunks created.
    """
    from searchbot.models import DocumentChunk

    # 1. Extract
    raw_text = extract_text(document.file.path, document.file_type)

    # 2. Clean
    cleaned_text = clean_text(raw_text)

    if not cleaned_text:
        raise ValueError("No text could be extracted from this document.")

    # 3. Remove old chunks if document is being re-processed
    DocumentChunk.objects.filter(document=document).delete()

    # 4. Chunk and save
    chunks = chunk_text(cleaned_text, chunk_size=500, overlap=50)
    for idx, chunk in enumerate(chunks):
        DocumentChunk.objects.create(
            document=document,
            chunk_index=idx,
            text=chunk,
        )

    # 5. Mark as processed
    document.is_processed = True
    document.save()

    return len(chunks)