from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extends Django's User model to add admin/normal role."""
    USER_ROLES = (
        ('admin', 'Admin'),
        ('user', 'Normal User'),
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=10,
        choices=USER_ROLES,
        default='user'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'admin'


class Document(models.Model):
    """An uploaded document (PDF, DOCX, XLSX, PPTX, TXT)."""
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=10)
    file_size = models.IntegerField(help_text="Size in bytes")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']

    def _str_(self):
        return self.title

    def file_size_kb(self):
        return round(self.file_size / 1024, 2)

    def delete(self, *args, **kwargs):
        if self.file:
            try:
                self.file.delete(save=False)
            except Exception:
                pass
        super().delete(*args, **kwargs)


class DocumentChunk(models.Model):
    """A small piece of text extracted from a document for similarity search."""
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    chunk_index = models.IntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'chunk_index']

    def _str_(self):
        return f"{self.document.title} - chunk {self.chunk_index}"


class QueryLog(models.Model):
    """Logs every question a user asks and the answer given by AI."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='queries'
    )
    question = models.TextField()
    answer = models.TextField()
    sources = models.TextField(
        blank=True,
        help_text="Document titles used to answer (comma-separated)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def _str_(self):
        return f"{self.user.username}: {self.question[:50]}"