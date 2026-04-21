import json
from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.database import get_users, get_files
from core.auth import require_role

VALID_ROLES = ('user', 'moderator', 'admin')


@require_role('admin')
def list_users(request):
    """All registered users. Admin only."""
    try:
        users = list(get_users().find({}, {'password': 0}))
        for u in users:
            u['_id'] = str(u['_id'])
            u['files'] = [str(f) for f in u.get('files', [])]
        return JsonResponse({'users': users})
    except Exception as e:
        print(f'Admin list_users error: {e}')
        return JsonResponse({'error': 'Failed to fetch users'}, status=500)


@csrf_exempt
@require_role('admin')
def set_role(request, user_id):
    """Change a user's role. Admin only."""
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        new_role = data.get('role', '')

        if new_role not in VALID_ROLES:
            return JsonResponse({'error': f'Invalid role. Choose from: {", ".join(VALID_ROLES)}'}, status=400)

        # admins can't demote themselves
        if user_id == request.user_id and new_role != 'admin':
            return JsonResponse({'error': "Can't demote yourself"}, status=400)

        result = get_users().update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'role': new_role}}
        )

        if result.matched_count == 0:
            return JsonResponse({'error': 'User not found'}, status=404)

        return JsonResponse({'message': f'Role updated to {new_role}'})
    except Exception as e:
        print(f'Admin set_role error: {e}')
        return JsonResponse({'error': 'Failed to update role'}, status=500)


@require_role('admin', 'moderator')
def list_all_files(request):
    """Every file in the system. Admin + moderator."""
    try:
        files = list(get_files().find({}).sort('uploadDate', -1))
        result = []
        for f in files:
            uploader = get_users().find_one({'_id': f['uploader']}, {'username': 1})
            out = {
                'id': str(f['_id']),
                'name': f['name'],
                'size': f['size'],
                'type': f['type'],
                'ipfsHash': f['ipfsHash'],
                'isPublic': f.get('isPublic', False),
                'persistent': f.get('persistent', False),
                'uploader': uploader['username'] if uploader else 'unknown',
            }
            result.append(out)
        return JsonResponse({'files': result})
    except Exception as e:
        print(f'Admin list_all_files error: {e}')
        return JsonResponse({'error': 'Failed to fetch files'}, status=500)


@csrf_exempt
@require_role('admin', 'moderator')
def admin_delete_file(request, hash):
    """Delete any file regardless of ownership. Admin + moderator."""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        files = get_files()
        file_doc = files.find_one({'ipfsHash': hash})

        if not file_doc:
            return JsonResponse({'error': 'File not found'}, status=404)

        # remove from owner's file list
        get_users().update_one(
            {'_id': file_doc['uploader']},
            {'$pull': {'files': file_doc['_id']}}
        )
        files.delete_one({'_id': file_doc['_id']})

        return JsonResponse({'message': 'File deleted'})
    except Exception as e:
        print(f'Admin delete_file error: {e}')
        return JsonResponse({'error': 'Failed to delete file'}, status=500)
