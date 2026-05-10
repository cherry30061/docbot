
"""Send queries to the Groq AI API and get back answers."""

import sys
import traceback
from groq import Groq
from django.conf import settings


SYSTEM_PROMPT = """You are a helpful document search assistant.

Answer the user's question using ONLY the information provided in the CONTEXT below.
- If the context does not contain the answer, say: "I could not find this information in the uploaded documents."
- Be concise, accurate, and clear.
- When possible, mention which source you used (e.g. "According to Source 1...").
- Do not make up information that is not in the context.
"""


def ask_groq(question, context_chunks):
    """Ask Groq a question with the relevant document chunks as context."""
    print("\n" + "="*60, flush=True)
    print(f"[GROQ] Received question: {question[:80]}", flush=True)
    print(f"[GROQ] Number of context chunks: {len(context_chunks)}", flush=True)

    if not settings.GROQ_API_KEY:
        msg = "GROQ_API_KEY is empty. Check your .env file."
        print(f"[GROQ ERROR] {msg}", flush=True)
        return f"Error: {msg}"

    if not settings.GROQ_API_KEY.startswith('gsk_'):
        msg = f"GROQ_API_KEY does not look valid (should start with 'gsk_'). Got: {settings.GROQ_API_KEY[:15]}..."
        print(f"[GROQ ERROR] {msg}", flush=True)
        return f"Error: {msg}"

    print(f"[GROQ] Using model: {settings.GROQ_MODEL}", flush=True)
    print(f"[GROQ] API key starts with: {settings.GROQ_API_KEY[:10]}...", flush=True)

    context_text = "\n\n".join([
        f"[Source {i + 1}: {chunk.document.title}]\n{chunk.text}"
        for i, (chunk, score) in enumerate(context_chunks)
    ])

    if not context_text:
        context_text = "No relevant documents found."

    user_prompt = f"""CONTEXT:
{context_text}

QUESTION: {question}

ANSWER:"""

    try:
        print("[GROQ] Calling Groq API...", flush=True)
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        answer = response.choices[0].message.content.strip()
        print(f"[GROQ SUCCESS] Got answer ({len(answer)} chars)", flush=True)
        print("="*60 + "\n", flush=True)
        return answer
    except Exception as e:
        error_detail = f"{type(e).__name__}: {str(e)}"
        print(f"[GROQ ERROR] {error_detail}", flush=True)
        traceback.print_exc(file=sys.stdout)
        print("="*60 + "\n", flush=True)
        return f"AI Error: {error_detail}"