from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from thefirst import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('upload/', views.compare_document_view, name='compare_document'),
    path('dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('review/<int:pk>/', views.project_review_view, name='project_review'),
    path('status/<int:pk>/', views.update_submission_status, name='update_submission_status'),
    
    # 🧠 NEW: Background Route for Local Ollama Llama3 Assistant Queries
    path('review/<int:project_id>/ai-insight/', views.get_ai_insight, name='get_ai_insight'),
]

# Made by essa manzoor and abdul hafeez of iqra national university 2022-2026  
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)