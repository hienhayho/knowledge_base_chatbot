import os
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

BACKEND_PORT = int(os.getenv("BACKEND_PORT"))
RELOAD = os.getenv("MODE") == "development"
CLEAN_INTERVAL = int(os.getenv("CLEAN_INTERVAL") or 10)
WORKERS = int(os.getenv("WORKERS") or 1)

pprint(
    {
        "BACKEND_PORT": BACKEND_PORT,
        "RELOAD": RELOAD,
        "CLEAN_INTERVAL": CLEAN_INTERVAL,
        "WORKERS": WORKERS,
    }
)

if RELOAD:
    os.system(f"fastapi dev --port {BACKEND_PORT} app.py")
else:
    os.system(f"fastapi run --port {BACKEND_PORT} --workers {WORKERS} app.py")
