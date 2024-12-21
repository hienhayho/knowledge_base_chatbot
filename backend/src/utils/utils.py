import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def convert_boolean_env_var(env_var: str) -> bool:
    """
    Convert a boolean environment variable to a boolean value.
    """
    return os.getenv(env_var, "False").lower() in [
        "true",
        "1",
    ]


def get_now():
    """
    Get the current date and time in Asia/Ho_Chi_Minh timezone
    """
    tz = os.getenv("TZ", "Asia/Singapore")
    timezone = pytz.timezone(tz)
    current_time = datetime.now(timezone)
    return current_time
