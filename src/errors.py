class AppError(Exception):
    pass


class InputFileError(AppError):
    pass


class DecodeError(AppError):
    pass


class OutputFileError(AppError):
    pass
