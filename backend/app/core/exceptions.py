class ParcelError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ParcelConflictError(ParcelError):
    def __init__(self, message: str) -> None:
        super().__init__("PARCEL_CONFLICT", message, 409)


class ParcelNotFoundError(ParcelError):
    def __init__(self, message: str) -> None:
        super().__init__("PARCEL_NOT_FOUND", message, 404)
