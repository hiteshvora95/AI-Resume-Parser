class ParserError(Exception):
    """
    Base exception for all file parsing errors.
    """
    pass


class ScannedPDFError(ParserError):
    """
    Raised when a PDF file has no readable text.
    """
    pass


class UnsupportedFileTypeError(ParserError):
    """
    Raised when the uploaded file is not a supported type.
    """
    pass
