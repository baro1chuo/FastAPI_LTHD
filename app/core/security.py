"""Băm mật khẩu và tạo/kiểm tra JWT."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core import config
from app.core.exceptions import AuthError

# Số vòng lặp PBKDF2 (khuyến nghị OWASP cho SHA-256)
_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Băm mật khẩu bằng PBKDF2-SHA256 (thư viện chuẩn) với salt ngẫu nhiên.

    Trả chuỗi dạng "pbkdf2_sha256$<vòng lặp>$<salt hex>$<hash hex>" để lưu vào passwordHash.
    """
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """So khớp mật khẩu người dùng nhập với hash đã lưu; trả False nếu hash sai định dạng."""
    try:
        _, iterations, salt, digest = password_hash.split("$")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(check.hex(), digest)  # so sánh thời gian hằng, chống timing attack


def create_access_token(user_id: int, role: str) -> str:
    """Tạo JWT chứa id người dùng (sub) và vai trò (role), hết hạn sau ACCESS_TOKEN_EXPIRE_MINUTES."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_access_token(token: str) -> int:
    """Giải mã JWT, trả id người dùng. Token sai chữ ký / hết hạn / sai định dạng -> AuthError (401)."""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise AuthError("Token không hợp lệ hoặc đã hết hạn")
