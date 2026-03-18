import hashlib
import hmac
def authenticate(username, password):
    secret_key = b'secret_key_here'
    expected_message = f'message_from_server'.encode('utf-8')
    message = username.encode('utf-8') + password.encode('utf-8')
    mac = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, expected_message.decode())
print(authenticate('username', 'password'))