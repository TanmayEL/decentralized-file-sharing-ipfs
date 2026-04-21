from django.urls import path
from . import views

urlpatterns = [
    path('admin/users', views.list_users),                        # GET  — admin only
    path('admin/users/<str:user_id>/role', views.set_role),       # PATCH — admin only
    path('admin/files', views.list_all_files),                    # GET  — admin + moderator
    path('admin/files/<str:hash>', views.admin_delete_file),      # DELETE — admin + moderator
]
