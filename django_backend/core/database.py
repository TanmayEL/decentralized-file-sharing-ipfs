import os
from pymongo import MongoClient

# cached so serverless re-invocations don't reconnect every time
_client = None
_db = None

def get_db():
    global _client, _db
    if _db is not None:
        return _db

    uri = os.environ.get('MONGODB_URI')
    if not uri:
        raise ValueError('MONGODB_URI environment variable is not set')
    _client = MongoClient(uri)

    # get the database from the URI, fall back to 'ipfs-files'
    try:
        db_name = _client.get_default_database().name
    except Exception:
        db_name = 'ipfs-files'
    _db = _client[db_name]
    return _db

def get_users():
    return get_db()['users']

def get_files():
    return get_db()['files']
