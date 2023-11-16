import hashlib

ENCODING = 'utf-8'

def sha256(data, security = False):
    if (isinstance(data, str)):
        data = data.encode(ENCODING)

    return hashlib.sha256(data, usedforsecurity = security).hexdigest()
