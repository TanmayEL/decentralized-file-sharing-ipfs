import os
import jwt
from functools import wraps
from django.http import JsonResponse

JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError('JWT_SECRET environment variable is not set')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = int(os.environ.get('JWT_EXPIRY_HOURS', 24))

# roles in ascending order of power
ROLES = ('user', 'moderator', 'admin')


def generate_token(user_id, email, role='user'):
    from datetime import datetime, timedelta, timezone
    payload = {
        'userId': str(user_id),
        'email': email,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def require_auth(view_func):
    """Any logged-in user."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Access token required'}, status=401)

        token = auth_header.split(' ')[1]
        try:
            payload = decode_token(token)
            request.user_id = payload['userId']
            request.user_email = payload['email']
            request.user_role = payload.get('role', 'user')
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Invalid or expired token'}, status=403)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid or expired token'}, status=403)

        return view_func(request, *args, **kwargs)
    return wrapper


def require_role(*allowed_roles):
    """Only users whose role is in allowed_roles get through.

    Usage:
        @require_role('admin')
        @require_role('admin', 'moderator')
    """
    def decorator(view_func):
        @wraps(view_func)
        @require_auth  # always authenticate first
        def wrapper(request, *args, **kwargs):
            if request.user_role not in allowed_roles:
                return JsonResponse({'error': 'Insufficient permissions'}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def optional_auth(view_func):
    """Attaches user identity if a valid token is present, but never blocks.
    Use this for endpoints that are public but behave differently when logged in.
    Check `request.user_id` — it's None if the request is unauthenticated.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        request.user_id = None
        request.user_email = None
        request.user_role = None

        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = decode_token(token)
                request.user_id = payload['userId']
                request.user_email = payload['email']
                request.user_role = payload.get('role', 'user')
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                pass  # bad token — treat as anonymous

        return view_func(request, *args, **kwargs)
    return wrapper


def has_role(request, *roles):
    """Helper for inline role checks inside a view."""
    return getattr(request, 'user_role', 'user') in roles
