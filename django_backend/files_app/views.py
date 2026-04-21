import os
import json
import tempfile
from datetime import datetime, timezone
from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.database import get_files, get_users
from core.auth import require_auth, optional_auth, has_role
from core.ipfs_service import upload_to_ipfs, get_gateway_url, is_configured
from core.compression_service import compress_file


def _serialize_file(f, include_uploader=True):
    """Convert a MongoDB file doc to something JSON-friendly."""
    out = {
        'id': str(f['_id']),
        'name': f['name'],
        'size': f['size'],
        'originalSize': f.get('originalSize'),
        'compressed': f.get('compressed', False),
        'type': f['type'],
        'ipfsHash': f['ipfsHash'],
        'uploadDate': f['uploadDate'].isoformat() if isinstance(f['uploadDate'], datetime) else f['uploadDate'],
        'isPublic': f.get('isPublic', False),
        'description': f.get('description', ''),
        'persistent': f.get('persistent', False),
        'accessList': [str(uid) for uid in f.get('accessList', [])],
    }
    if include_uploader and 'uploader' in f:
        uploader = f['uploader']
        if isinstance(uploader, dict):
            out['uploader'] = {'id': str(uploader['_id']), 'username': uploader.get('username')}
        else:
            out['uploader'] = str(uploader)
    return out


def _has_access(file_doc, user_id):
    uploader_id = str(file_doc['uploader']) if not isinstance(file_doc['uploader'], dict) else str(file_doc['uploader']['_id'])
    access_list = [str(uid) for uid in file_doc.get('accessList', [])]
    return file_doc.get('isPublic') or uploader_id == user_id or user_id in access_list


@csrf_exempt
@require_auth
def upload_file(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)

        uploaded = request.FILES['file']

        if uploaded.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'File size exceeds 10MB limit'}, status=400)

        if not is_configured():
            return JsonResponse({'error': 'Pinata configuration not available'}, status=500)

        is_public = request.POST.get('isPublic', 'false').lower() == 'true'
        description = request.POST.get('description', '')

        # save to temp file so we can compress it
        suffix = os.path.splitext(uploaded.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        print(f'Compressing: {uploaded.name} ({uploaded.size / 1024 / 1024:.2f}MB)')
        result = compress_file(tmp_path, uploaded.name)
        final_size = result.get('compressed_size') or result['original_size']

        ipfs_hash = upload_to_ipfs(result['file_path'], uploaded.name, result['compressed'])
        os.unlink(result['file_path'])

        file_doc = {
            'name': uploaded.name,
            'size': final_size,
            'originalSize': result['original_size'],
            'compressed': result['compressed'],
            'type': uploaded.content_type,
            'ipfsHash': ipfs_hash,
            'uploader': ObjectId(request.user_id),
            'isPublic': is_public,
            'description': description,
            'persistent': False,
            'accessList': [],
            'uploadDate': datetime.now(timezone.utc),
        }

        files = get_files()
        inserted = files.insert_one(file_doc)

        get_users().update_one(
            {'_id': ObjectId(request.user_id)},
            {'$push': {'files': inserted.inserted_id}}
        )

        return JsonResponse({
            'message': 'File uploaded successfully',
            'file': {
                'id': str(inserted.inserted_id),
                'name': file_doc['name'],
                'size': file_doc['size'],
                'type': file_doc['type'],
                'ipfsHash': ipfs_hash,
                'uploadDate': file_doc['uploadDate'].isoformat(),
                'isPublic': file_doc['isPublic'],
                'description': file_doc['description'],
            },
        })

    except Exception as e:
        print(f'Upload error: {e}')
        return JsonResponse({'error': 'File upload failed'}, status=500)


@csrf_exempt
@optional_auth
def file_actions(request, hash):
    """GET = download (public files need no token), DELETE = delete (always needs auth)."""
    if request.method == 'GET':
        return _download_file(request, hash)
    elif request.method == 'DELETE':
        if not request.user_id:
            return JsonResponse({'error': 'Access token required'}, status=401)
        return _delete_file(request, hash)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def _download_file(request, hash):
    try:
        files = get_files()
        file_doc = files.find_one({'ipfsHash': hash})

        if not file_doc:
            return JsonResponse({'error': 'File not found'}, status=404)

        # public files: anyone can download, no token needed
        # private files: need to be logged in and in the access list
        if not file_doc.get('isPublic'):
            if not request.user_id:
                return JsonResponse({'error': 'Login required to access this file'}, status=401)
            if not _has_access(file_doc, request.user_id):
                return JsonResponse({'error': 'Access denied'}, status=403)

        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(get_gateway_url(hash))

    except Exception as e:
        print(f'Download error: {e}')
        return JsonResponse({'error': 'File download failed'}, status=500)


def _delete_file(request, hash):
    try:
        files = get_files()
        file_doc = files.find_one({'ipfsHash': hash})

        if not file_doc:
            return JsonResponse({'error': 'File not found'}, status=404)

        is_owner = str(file_doc['uploader']) == request.user_id
        if not is_owner and not has_role(request, 'admin', 'moderator'):
            return JsonResponse({'error': 'Only file owner can delete'}, status=403)

        get_users().update_one(
            {'_id': ObjectId(request.user_id)},
            {'$pull': {'files': file_doc['_id']}}
        )
        files.delete_one({'_id': file_doc['_id']})

        return JsonResponse({'message': 'File deleted successfully'})

    except Exception as e:
        print(f'Delete error: {e}')
        return JsonResponse({'error': 'Failed to delete file'}, status=500)


@require_auth
def get_metadata(request, hash):
    try:
        files = get_files()
        file_doc = files.find_one({'ipfsHash': hash})

        if not file_doc:
            return JsonResponse({'error': 'File not found'}, status=404)

        if not _has_access(file_doc, request.user_id):
            return JsonResponse({'error': 'Access denied'}, status=403)

        # pull uploader username
        uploader = get_users().find_one({'_id': file_doc['uploader']}, {'username': 1})
        file_doc['uploader'] = uploader

        return JsonResponse(_serialize_file(file_doc))

    except Exception as e:
        print(f'Metadata error: {e}')
        return JsonResponse({'error': 'Failed to get metadata'}, status=500)


@require_auth
def get_user_files(request):
    try:
        user_oid = ObjectId(request.user_id)
        files = get_files()

        docs = list(files.find({
            '$or': [{'uploader': user_oid}, {'accessList': user_oid}]
        }).sort('uploadDate', -1))

        # attach uploader usernames
        for doc in docs:
            uploader = get_users().find_one({'_id': doc['uploader']}, {'username': 1})
            doc['uploader'] = uploader

        return JsonResponse({'files': [_serialize_file(f) for f in docs]})

    except Exception as e:
        print(f'Files error: {e}')
        return JsonResponse({'error': 'Failed to get files'}, status=500)


def get_public_files(request):
    try:
        files = get_files()
        docs = list(files.find({'isPublic': True}).sort('uploadDate', -1).limit(50))

        for doc in docs:
            uploader = get_users().find_one({'_id': doc['uploader']}, {'username': 1})
            doc['uploader'] = uploader

        return JsonResponse({'files': [_serialize_file(f) for f in docs]})

    except Exception as e:
        print(f'Public files error: {e}')
        return JsonResponse({'error': 'Failed to get public files'}, status=500)


@csrf_exempt
@require_auth
def share_file(request, hash):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        user_ids = data.get('userIds', [])

        files = get_files()
        file_doc = files.find_one({'ipfsHash': hash})

        if not file_doc:
            return JsonResponse({'error': 'File not found'}, status=404)

        if str(file_doc['uploader']) != request.user_id:
            return JsonResponse({'error': 'Only file owner can share'}, status=403)

        new_ids = [ObjectId(uid) for uid in user_ids]
        existing = file_doc.get('accessList', [])
        merged = list({str(oid): oid for oid in existing + new_ids}.values())

        files.update_one({'_id': file_doc['_id']}, {'$set': {'accessList': merged}})

        return JsonResponse({'message': 'File shared successfully'})

    except Exception as e:
        print(f'Share error: {e}')
        return JsonResponse({'error': 'Failed to share file'}, status=500)


@csrf_exempt
@require_auth
def toggle_persistence(request, hash):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        files = get_files()
        file_doc = files.find_one({'ipfsHash': hash})

        if not file_doc:
            return JsonResponse({'error': 'File not found'}, status=404)

        if str(file_doc['uploader']) != request.user_id:
            return JsonResponse({'error': 'Only file owner can modify persistence'}, status=403)

        new_value = not file_doc.get('persistent', False)
        files.update_one({'_id': file_doc['_id']}, {'$set': {'persistent': new_value}})

        return JsonResponse({
            'message': f'File persistence {"enabled" if new_value else "disabled"}',
            'persistent': new_value,
        })

    except Exception as e:
        print(f'Toggle persistence error: {e}')
        return JsonResponse({'error': 'Failed to toggle persistence'}, status=500)
