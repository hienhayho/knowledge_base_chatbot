import os
import requests
from langfuse import Langfuse
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from langfuse.llama_index import LlamaIndexCallbackHandler

from src.settings import defaul_settings
from src.database import ContextualRAG

load_dotenv()

langfuse = Langfuse()

langfuse_callback_handler = LlamaIndexCallbackHandler()
Settings.callback_manager = CallbackManager([langfuse_callback_handler])

rag = ContextualRAG.from_setting(setting=defaul_settings)


def main():
    print(
        rag.search(
            is_contextual_rag=False,
            collection_name="c32fba91-09a3-489d-8d35-9bb8424c6e73",
            query="Who is the author of Sherlock Home ?",
            debug=True,
        )
    )


def get_cost_from_trace_id(trace_id):
    url = f"https://cloud.langfuse.com/api/public/traces/{trace_id}"
    response = requests.get(
        url, auth=(os.getenv("LANGFUSE_PUBLIC_KEY"), os.getenv("LANGFUSE_SECRET_KEY"))
    )

    data = response.json()

    return data["totalCost"]


def get_cost():
    url = "https://cloud.langfuse.com/api/public/sessions/12345678"
    response = requests.get(
        url, auth=(os.getenv("LANGFUSE_PUBLIC_KEY"), os.getenv("LANGFUSE_SECRET_KEY"))
    )

    data = response.json()

    print(sum([get_cost_from_trace_id(item["id"]) for item in data["traces"]]))


if __name__ == "__main__":
    # main()
    # get_embedding(chunk="Hello, how are you?")
    get_cost()
    # observations = langfuse.fetch_observation("42b29f55-d63c-4ee3-bf60-837d2c8498d6")
    # print(observations)
