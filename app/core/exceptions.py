"""Exception nghiệp vụ: service raise, main.py đổi thành HTTP response {"detail": message}."""


class AppError(Exception):
    """Lớp cha của mọi lỗi nghiệp vụ; status_code là mã HTTP trả về."""

    status_code = 400

    def __init__(self, message: str):
        """message: thông báo lỗi gửi cho client."""
        super().__init__(message)
        self.message = message


class BusinessRuleError(AppError):
    """400 – vi phạm quy tắc nghiệp vụ (vd sai mật khẩu hiện tại)."""
    status_code = 400


class AuthError(AppError):
    """401 – sai email/mật khẩu, token sai hoặc hết hạn."""
    status_code = 401


class ForbiddenError(AppError):
    """403 – tài khoản bị khóa, không đủ quyền, admin tự khóa/xóa mình."""
    status_code = 403


class NotFoundError(AppError):
    """404 – không tìm thấy bản ghi."""
    status_code = 404


class ConflictError(AppError):
    """409 – trùng dữ liệu (vd email đã tồn tại)."""
    status_code = 409
