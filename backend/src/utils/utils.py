import os
from dotenv import load_dotenv

load_dotenv()


def convert_boolean_env_var(env_var: str) -> bool:
    return os.getenv(env_var, "False").lower() in [
        "true",
        "1",
    ]
