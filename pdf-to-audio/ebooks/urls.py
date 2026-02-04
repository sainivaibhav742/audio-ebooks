from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_ebook, name='upload_ebook'),
    path('list/', views.ebook_list, name='ebook_list'),
    path('<int:pk>/', views.ebook_detail, name='ebook_detail'),
    path('<int:pk>/status/', views.check_processing_status, name='check_status'),
    path('<int:pk>/delete/', views.delete_ebook, name='delete_ebook'),
]