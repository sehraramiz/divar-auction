import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken

from auction.core.config import config
from auction.core.log import logger


def get_fernet_obj():
    hlib = hashlib.md5()
    hlib.update(config.secret_key.encode("utf-8"))
    key = base64.urlsafe_b64encode(hlib.hexdigest().encode("latin-1"))
    return Fernet(key)


def encrypt_data(data: dict) -> str:
    data_str = json.dumps(data)
    fernet = get_fernet_obj()
    return fernet.encrypt(data_str.encode("utf-8")).decode("utf-8")


def decrypt_data(encrypted_data: str) -> dict:
    fernet = get_fernet_obj()
    try:
        data_str = fernet.decrypt(encrypted_data).decode("utf-8")
        return json.loads(data_str)
    except InvalidToken as e:
        raise e
    except Exception as e:
        logger.error(f"Data descryption error: {e}")
        return {}
