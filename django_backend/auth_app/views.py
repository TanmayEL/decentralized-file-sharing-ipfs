import json
import bcrypt
from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from jwt import ExpiredSignatureError, InvalidTokenError
from core.database import get_users
from core.auth import generate_token, decode_token, require_auth


@csrf_exempt
@require_http_methods(['POST'])
def register(request):
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not username or len(username) < 3:
            return JsonResponse({'error': 'Username must be at least 3 characters'}, status=400)
        if not email or '@' not in email:
            return JsonResponse({'error': 'Valid email required'}, status=400)
        if not password or len(password) < 6:
            return JsonResponse({'error': 'Password must be at least 6 characters'}, status=400)

        users = get_users()

        if users.find_one({'$or': [{'email': email}, {'username': username}]}):
            return JsonResponse({'error': 'User with this email or username already exists'}, status=400)

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # first user ever becomes admin automatically
        role = 'admin' if users.count_documents({}) == 0 else 'user'

        result = users.insert_one({
            'username': username,
            'email': email,
            'password': hashed,
            'role': role,
            'files': [],
        })

        token = generate_token(result.inserted_id, email, role)

        return JsonResponse({
            'message': 'User created successfully',
            'token': token,
            'user': {'id': str(result.inserted_id), 'username': username, 'email': email, 'role': role},
        }, status=201)

    except Exception as e:
        print(f'Registration error: {e}')
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def login(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)

        users = get_users()
        user = users.find_one({'email': email})

        if not user or not bcrypt.checkpw(password.encode(), user['password'].encode()):
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        role = user.get('role', 'user')
        token = generate_token(user['_id'], user['email'], role)

        return JsonResponse({
            'message': 'Login successful',
            'token': token,
            'user': {'id': str(user['_id']), 'username': user['username'], 'email': user['email'], 'role': role},
        })

    except Exception as e:
        print(f'Login error: {e}')
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def refresh(request):
    """Hand in a still-valid token, get a fresh one back."""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Token required'}, status=401)

        token = auth_header.split(' ')[1]
        try:
            payload = decode_token(token)
        except ExpiredSignatureError:
            return JsonResponse({'error': 'Token expired — please log in again'}, status=401)
        except InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=403)

        # re-fetch role from DB in case it changed since the token was issued
        users = get_users()
        user = users.find_one({'_id': ObjectId(payload['userId'])}, {'role': 1})
        role = user.get('role', 'user') if user else payload.get('role', 'user')

        new_token = generate_token(payload['userId'], payload['email'], role)
        return JsonResponse({'token': new_token})

    except Exception as e:
        print(f'Refresh error: {e}')
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_auth
@require_http_methods(['GET'])
def profile(request):
    try:
        users = get_users()
        user = users.find_one({'_id': ObjectId(request.user_id)}, {'password': 0})

        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)

        user['_id'] = str(user['_id'])
        return JsonResponse({'user': user})

    except Exception as e:
        print(f'Profile error: {e}')
        return JsonResponse({'error': 'Internal server error'}, status=500)
