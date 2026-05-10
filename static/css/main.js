
// ===== DocBot Main JS =====

document.addEventListener('DOMContentLoaded', function() {
    initChat();
    initDeleteButtons();
    initAlertAutoDismiss();
});

function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// ===== Chat =====
function initChat() {
    const chatForm = document.getElementById('chat-form');
    if (!chatForm) return;

    const messagesContainer = document.getElementById('chat-messages');
    const questionInput = document.getElementById('question-input');
    const sendBtn = document.getElementById('send-btn');

    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (!question) return;

        const welcome = messagesContainer.querySelector('.welcome-message');
        if (welcome) welcome.remove();

        addMessage('user', question);
        questionInput.value = '';
        sendBtn.disabled = true;

        const typingId = showTypingIndicator();

        try {
            const formData = new FormData();
            formData.append('question', question);
            formData.append('csrfmiddlewaretoken', getCSRFToken());

            const response = await fetch('/ask/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCSRFToken() }
            });

            const data = await response.json();
            removeTypingIndicator(typingId);

            if (data.success) {
                addMessage('bot', data.answer, data.sources);
            } else {
                addMessage('bot', 'Error: ' + (data.error || 'Something went wrong.'));
            }
        } catch (err) {
            removeTypingIndicator(typingId);
            addMessage('bot', 'Network error. Please try again.');
        } finally {
            sendBtn.disabled = false;
            questionInput.focus();
        }
    });
}

function addMessage(type, text, sources) {
    sources = sources || [];
    const messagesContainer = document.getElementById('chat-messages');
    const message = document.createElement('div');
    message.className = 'message ' + type + '-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = type === 'user'
        ? '<i class="bi bi-person"></i>'
        : '<i class="bi bi-robot"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatText(text);

    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        sourcesDiv.innerHTML = '<strong><i class="bi bi-bookmark"></i> Sources:</strong> ' +
            sources.map(s => '<span class="source-tag">' + escapeHtml(s) + '</span>').join('');
        bubble.appendChild(sourcesDiv);
    }

    message.appendChild(avatar);
    message.appendChild(bubble);
    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    const id = 'typing-' + Date.now();
    const indicator = document.createElement('div');
    indicator.id = id;
    indicator.className = 'message bot-message';
    indicator.innerHTML =
        '<div class="message-avatar"><i class="bi bi-robot"></i></div>' +
        '<div class="message-bubble">' +
            '<div class="typing-indicator">' +
                '<div class="typing-dot"></div>' +
                '<div class="typing-dot"></div>' +
                '<div class="typing-dot"></div>' +
            '</div>' +
        '</div>';
    messagesContainer.appendChild(indicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) indicator.remove();
}

function formatText(text) {
    let safe = escapeHtml(text);
    safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    safe = safe.replace(/\n/g, '<br>');
    return safe;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== Delete Document =====
function initDeleteButtons() {
    const deleteBtns = document.querySelectorAll('.delete-btn');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const docId = this.dataset.docId;
            const docTitle = this.dataset.docTitle;

            if (!confirm('Delete "' + docTitle + '"?\nThis cannot be undone.')) return;

            try {
                const response = await fetch('/delete/' + docId + '/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    const row = document.getElementById('doc-row-' + docId);
                    if (row) {
                        row.style.transition = 'opacity 0.4s ease';
                        row.style.opacity = '0';
                        setTimeout(() => {
                            row.remove();
                            showToast(data.message || 'Deleted successfully', 'success');
                        }, 400);
                    }
                } else {
                    showToast(data.error || 'Failed to delete', 'danger');
                }
            } catch (err) {
                showToast('Network error', 'danger');
            }
        });
    });
}

// ===== Toast =====
function showToast(message, type) {
    type = type || 'info';
    const container = document.querySelector('.container.mt-3') || createToastContainer();
    const alert = document.createElement('div');
    alert.className = 'alert alert-' + type + ' alert-dismissible fade show animated-alert';
    alert.innerHTML =
        '<i class="bi bi-info-circle"></i> ' + escapeHtml(message) +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    container.appendChild(alert);

    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 300);
    }, 4000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'container mt-3';
    document.body.insertBefore(container, document.querySelector('.main-content'));
    return container;
}

// ===== Auto-dismiss flash messages =====
function initAlertAutoDismiss() {
    const alerts = document.querySelectorAll('.alert.animated-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}