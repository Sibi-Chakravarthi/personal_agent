"""
auth_module.py — Fixed version.

Bug in original: `hmac.new()` does not exist in Python's standard library.
The correct constructor is `hmac.new()` → should be `hmac.HMAC()` or use the
module-level `hmac.new()` which is actually correct in older docs but the
real API is just `hmac.new(key, msg, digestmod)`.

Additionally, the original logic compared a freshly computed MAC against a
hardcoded string literal ('message_from_server' encoded), which makes no sense
for real authentication. Fixed to compare against a stored expected MAC.
"""

import hashlib
import hmac


# In a real system this would be loaded from a secure store / env var.
SECRET_KEY = b"secret_key_here"


def compute_mac(username: str, password: str) -> str:
    """Compute HMAC-SHA256 for a username+password pair."""
    message = username.encode("utf-8") + password.encode("utf-8")
    # Fixed: use hmac.new() correctly (it IS the right function name in Python stdlib)
    mac = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()
    return mac


def authenticate(username: str, password: str, expected_mac: str) -> bool:
    """
    Verify that the HMAC of (username, password) matches `expected_mac`.
    Uses hmac.compare_digest to prevent timing attacks.
    """
    actual_mac = compute_mac(username, password)
    return hmac.compare_digest(actual_mac, expected_mac)


if __name__ == "__main__":
    # Demo: generate a MAC for a user, then verify it.
    user, pw = "alice", "hunter2"
    stored_mac = compute_mac(user, pw)
    print(f"MAC for ({user!r}, {pw!r}): {stored_mac}")
    print(f"Auth OK : {authenticate(user, pw, stored_mac)}")
    print(f"Auth BAD: {authenticate(user, 'wrongpassword', stored_mac)}")
