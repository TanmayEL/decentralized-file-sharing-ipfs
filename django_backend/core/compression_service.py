import os
import gzip
import shutil
from PIL import Image

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MIN_SIZE = 1024 * 1024  # don't bother under 1MB
IMAGE_THRESHOLD = 0.9   # only keep compressed if actually smaller
GZIP_THRESHOLD = 0.8    # gzip needs to earn it — 20% savings minimum

def _compress_image(file_path, compressed_path, file_size):
    img = Image.open(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    if ext in ('.jpg', '.jpeg'):
        img.save(compressed_path, 'JPEG', quality=80, optimize=True, progressive=True)
    elif ext == '.png':
        img.save(compressed_path, 'PNG', optimize=True, compress_level=8)
    elif ext == '.webp':
        img.save(compressed_path, 'WEBP', quality=80)
    else:
        img.save(compressed_path, quality=80)

    compressed_size = os.path.getsize(compressed_path)
    ratio = (1 - compressed_size / file_size) * 100
    print(f'Image: {file_size/1024/1024:.2f}MB → {compressed_size/1024/1024:.2f}MB ({ratio:.1f}% smaller)')

    if compressed_size < file_size * IMAGE_THRESHOLD:
        os.unlink(file_path)
        return {'file_path': compressed_path, 'compressed': True, 'original_size': file_size, 'compressed_size': compressed_size}

    # not worth it — just use the original
    os.unlink(compressed_path)
    return {'file_path': file_path, 'compressed': False, 'original_size': file_size}

def _compress_gzip(file_path, compressed_path, file_size):
    with open(file_path, 'rb') as f_in, gzip.open(compressed_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    compressed_size = os.path.getsize(compressed_path)
    ratio = (1 - compressed_size / file_size) * 100
    print(f'File: {file_size/1024/1024:.2f}MB → {compressed_size/1024/1024:.2f}MB ({ratio:.1f}% smaller)')

    if compressed_size < file_size * GZIP_THRESHOLD:
        os.unlink(file_path)
        return {'file_path': compressed_path, 'compressed': True, 'original_size': file_size, 'compressed_size': compressed_size}

    os.unlink(compressed_path)
    return {'file_path': file_path, 'compressed': False, 'original_size': file_size}

def compress_file(file_path, original_name):
    try:
        file_size = os.path.getsize(file_path)

        if file_size < MIN_SIZE:
            return {'file_path': file_path, 'compressed': False, 'original_size': file_size}

        ext = os.path.splitext(original_name)[1].lower()
        compressed_path = file_path + '.compressed'

        if ext in IMAGE_EXTENSIONS:
            return _compress_image(file_path, compressed_path, file_size)

        return _compress_gzip(file_path, compressed_path, file_size)
    except Exception as e:
        print(f'Compression failed, sending original: {e}')
        return {'file_path': file_path, 'compressed': False, 'original_size': os.path.getsize(file_path)}
