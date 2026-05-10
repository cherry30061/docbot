
"""View functions for signup, login, dashboards, and chat."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Document, QueryLog
from .forms import SignupForm, LoginForm, DocumentUploadForm
from .utils.extractors import get_file_extension
from .utils.processor import process_document
from .utils.search import search_relevant_chunks
from .utils.groq_client import ask_groq


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role', 'user')
            if hasattr(user, 'profile'):
                user.profile.role = role
                user.profile.save()
            login(request, user)
            messages.success(request, f"Welcome {user.username}! Account created.")
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'auth/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def home_view(request):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.is_admin:
        return redirect('admin_dashboard')
    return redirect('chat')


@login_required
def admin_dashboard_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        messages.error(request, "Admin access required.")
        return redirect('chat')

    documents = Document.objects.all()
    upload_form = DocumentUploadForm()
    return render(request, 'admin/dashboard.html', {
        'documents': documents,
        'upload_form': upload_form,
    })


@login_required
def upload_document_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        messages.error(request, "Admin access required.")
        return redirect('chat')

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.file_size = document.file.size
            document.file_type = get_file_extension(document.file.name)
            document.save()
            try:
                num_chunks = process_document(document)
                messages.success(request, f"'{document.title}' uploaded and split into {num_chunks} chunks.")
            except Exception as e:
                messages.warning(request, f"Uploaded but processing failed: {str(e)}")
            return redirect('admin_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect('admin_dashboard')


@login_required
@require_POST
def delete_document_view(request, document_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return JsonResponse({'success': False, 'error': 'Admin access required'}, status=403)

    document = get_object_or_404(Document, id=document_id)
    title = document.title
    document.delete()
    return JsonResponse({'success': True, 'message': f"Deleted '{title}'"})


@login_required
def chat_view(request):
    documents = Document.objects.filter(is_processed=True)
    recent_queries = QueryLog.objects.filter(user=request.user)[:10]
    return render(request, 'chat/chat.html', {
        'documents': documents,
        'recent_queries': recent_queries,
    })


@login_required
@require_POST
def ask_question_view(request):
    """Real AI question answering: search chunks + ask Groq."""
    question = request.POST.get('question', '').strip()
    print(f"\n[ASK] User={request.user.username} | Question={question[:80]}", flush=True)

    if not question:
        return JsonResponse({'success': False, 'error': 'Please enter a question'}, status=400)

    total_docs = Document.objects.filter(is_processed=True).count()
    print(f"[ASK] Processed documents in DB: {total_docs}", flush=True)

    if total_docs == 0:
        return JsonResponse({
            'success': True,
            'answer': "No documents have been uploaded yet. Please ask an admin to upload some documents first.",
            'sources': [],
        })

    relevant_chunks = search_relevant_chunks(question, top_k=5)
    print(f"[ASK] Relevant chunks found: {len(relevant_chunks)}", flush=True)

    if not relevant_chunks:
        answer = "I couldn't find any relevant information in the uploaded documents to answer your question. Try rephrasing or asking about a different topic."
        sources = []
    else:
        answer = ask_groq(question, relevant_chunks)
        sources = list({chunk.document.title for chunk, score in relevant_chunks})

    QueryLog.objects.create(
        user=request.user,
        question=question,
        answer=answer,
        sources=', '.join(sources),
    )

    print(f"[ASK] Returning answer ({len(answer)} chars), sources={sources}", flush=True)
    return JsonResponse({'success': True, 'answer': answer, 'sources': sources})