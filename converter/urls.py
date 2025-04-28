from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    # Redirect the old multiple upload route to the unified upload page
    path('jobs/multiple/', RedirectView.as_view(pattern_name='job_create', permanent=False), name='multiple_job_create'),
    path('jobs/<uuid:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<uuid:job_id>/status/', views.job_status, name='job_status'),
    path('jobs/<uuid:job_id>/delete/', views.job_delete, name='job_delete'),
    path('jobs/<uuid:job_id>/retry/', views.job_retry, name='job_retry'),
    path('jobs/<uuid:job_id>/download-all/', views.job_download_all, name='job_download_all'),
    path('jobs/batch-action/', views.batch_job_action, name='batch_job_action'),
    path('jobs/download-selected/', views.download_selected_files, name='download_selected_files'),
    
    # Documentation URLs
    path('docs/', views.docs_readme, name='docs_readme'),
    path('docs/user-guide/', views.docs_user_guide, name='docs_user_guide'),
    path('about/', views.about, name='about'),
]
