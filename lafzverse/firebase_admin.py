import json
import os

import firebase_admin
from firebase_admin import credentials


_firebase_app = None


def get_firebase_app():
    global _firebase_app
    if _firebase_app:
        return _firebase_app

    cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    cred_file = os.getenv('FIREBASE_SERVICE_ACCOUNT_FILE')

    if cred_json:
        try:
            data = json.loads(cred_json)
        except json.JSONDecodeError:
            return None
        cred = credentials.Certificate(data)
    elif cred_file:
        if not os.path.exists(cred_file):
            return None
        cred = credentials.Certificate(cred_file)
    else:
        return None

    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app
