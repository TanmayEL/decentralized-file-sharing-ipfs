from django.urls import path, include
from django.http import JsonResponse

def health(request):
    from datetime import datetime, timezone
    return JsonResponse({'status': 'OK', 'timestamp': datetime.now(timezone.utc).isoformat()})

def root(request):
    return JsonResponse({'message': 'IPFS File Sharing Backend API'})

urlpatterns = [
    path('', root),
    path('api/health', health),
    path('api/', include('auth_app.urls')),
    path('api/', include('files_app.urls')),
    path('api/', include('admin_app.urls')),
]
