from django.urls import path
from . import views

app_name = 'docs'

urlpatterns = [
    path('', views.docs_index, name='index'),
    path('<str:doc_name>/', views.docs_view, name='view'),
]