import os
import requests

PINATA_BASE = 'https://api.pinata.cloud/pinning'

def _headers():
    return {
        'pinata_api_key': os.environ.get('PINATA_API_KEY'),
        'pinata_secret_api_key': os.environ.get('PINATA_SECRET_KEY'),
    }

def upload_to_ipfs(file_path, original_name, compressed=False):
    import json
    with open(file_path, 'rb') as f:
        response = requests.post(
            f'{PINATA_BASE}/pinFileToIPFS',
            headers=_headers(),
            files={'file': (original_name, f)},
            data={
                'pinataMetadata': json.dumps({'name': original_name, 'compressed': compressed}),
                'pinataOptions': json.dumps({'cidVersion': 0}),
            },
        )
    response.raise_for_status()
    return response.json()['IpfsHash']

def unpin_from_ipfs(ipfs_hash):
    response = requests.delete(f'{PINATA_BASE}/unpin/{ipfs_hash}', headers=_headers())
    response.raise_for_status()

def get_gateway_url(ipfs_hash):
    gateway = os.environ.get('PINATA_GATEWAY_URL', 'https://gateway.pinata.cloud/ipfs')
    if not gateway.startswith('http'):
        gateway = f'https://{gateway}'
    # dedicated gateways use /ipfs/<hash>, public gateway already has /ipfs in path
    if 'mypinata.cloud' in gateway:
        return f'{gateway.rstrip("/")}/ipfs/{ipfs_hash}'
    return f'{gateway.rstrip("/")}/{ipfs_hash}'

def is_configured():
    return bool(os.environ.get('PINATA_API_KEY') and os.environ.get('PINATA_SECRET_KEY'))
