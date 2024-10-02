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
