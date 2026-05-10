"""Find the most relevant document chunks for a query using TF-IDF + cosine similarity."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from searchbot.models import DocumentChunk


def search_relevant_chunks(query, top_k=5):
    """
    Find the top K most relevant document chunks for a query.

    Returns: list of (DocumentChunk, similarity_score) tuples,
             sorted from most to least relevant.
    """
    # Get all chunks from database (with their parent document)
    chunks = list(DocumentChunk.objects.all().select_related('document'))

    if not chunks:
        return []

    chunk_texts = [c.text for c in chunks]

    # TF-IDF: turn text into number vectors based on word importance
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=5000,
        ngram_range=(1, 2),
    )

    try:
        chunk_vectors = vectorizer.fit_transform(chunk_texts)
        query_vector = vectorizer.transform([query])
    except ValueError:
        return []

    # Cosine similarity: how close is the query to each chunk?
    similarities = cosine_similarity(query_vector, chunk_vectors).flatten()

    # Get the indices of the top K highest scores
    top_indices = similarities.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = float(similarities[idx])
        if score > 0:
            results.append((chunks[idx], score))

    return results
