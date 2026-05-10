from django.contrib import admin
from .models import UserProfile, Document, DocumentChunk, QueryLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'file_size_kb', 'uploaded_by', 'uploaded_at', 'is_processed')
    list_filter = ('file_type', 'is_processed')
    search_fields = ('title',)
    readonly_fields = ('uploaded_at', 'file_size')


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'created_at')
    list_filter = ('document',)
    search_fields = ('text',)


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('question', 'answer')
    readonly_fields = ('created_at',)