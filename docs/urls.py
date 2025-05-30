from django.urls import path
from . import views

app_name = 'docs'

# Use explicit URL patterns instead of capturing arbitrary strings
urlpatterns = [
    path('', views.docs_index, name='index'),
    # Explicit paths for each allowed document
    path('installation/', views.docs_installation, name='installation'),
    path('user_guide/', views.docs_user_guide, name='user_guide'),
    path('troubleshooting/', views.docs_troubleshooting, name='troubleshooting'),
    path('docker_setup/', views.docs_docker_setup, name='docker_setup'),
    path('README/', views.docs_readme, name='readme'),
    # General document viewer for compatibility with both systems
    path('view/<str:doc_key>/', views.view_documentation, name='view'),
]