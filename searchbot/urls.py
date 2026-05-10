"""URL routes for the searchbot app."""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('upload/', views.upload_document_view, name='upload_document'),
    path('delete/<int:document_id>/', views.delete_document_view, name='delete_document'),
    path('chat/', views.chat_view, name='chat'),
    path('ask/', views.ask_question_view, name='ask_question'),
]
