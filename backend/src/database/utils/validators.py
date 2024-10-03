import uuid
from email_validator import validate_email, EmailNotValidError


def validate_email_address(email: str) -> bool:
    """
    Validate email address using email_validator package

    Args:
        email: str: Email address to validate

    Returns:
        bool: True if email is valid, False otherwise
    """
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def is_valid_uuid(uuid_to_test: str, version: int = 4) -> bool:
    """
    Check if uuid is valid

    Args:
        uuid_to_test (str): Uuid to test
        version (int): Uuid version. Default is `4`
    """
    try:
        # check for validity of Uuid
        uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return True
