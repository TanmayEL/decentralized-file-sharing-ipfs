from django.urls import path
from . import views

urlpatterns = [
    path('upload', views.upload_file),
    path('files', views.get_user_files),
    path('public-files', views.get_public_files),
    path('file/<str:hash>', views.file_actions),        # GET=download, DELETE=delete
    path('metadata/<str:hash>', views.get_metadata),
    path('share/<str:hash>', views.share_file),
    path('file/<str:hash>/toggle-persistence', views.toggle_persistence),
]
