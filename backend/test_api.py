import requests
import json
import sseclient
import aiohttp
import asyncio

BASE_URL = "http://localhost:8000/api/assistant"

# def print_response(response):
#     print(f"Status Code: {response.status_code}")
#     print("Response:")
#     print(json.dumps(response.json(), indent=2))
#     print("\n" + "="*50 + "\n")

# def test_create_assistant():
#     data = {
#         "name": "Test Assistant",
#         "description": "A test assistant",
#         "knowledge_base_id": 1,
#         "configuration": {"model": "gpt-4o-mini", "service": "openai", "temperature": "0.8"}
#     }
#     response = requests.post(f"{BASE_URL}/", json=data)
#     print("Create Assistant Response:")
#     print_response(response)
#     return response.json()["id"]

# def test_delete_assistant(assistant_id):
#     response = requests.delete(f"{BASE_URL}/{assistant_id}")
#     print("Delete Assistant Response:")
#     print_response(response)

# def test_create_conversation(assistant_id):
#     data = {
#         "assistant_id": assistant_id
#     }
#     response = requests.post(f"{BASE_URL}/conversations", json=data)
#     print("Create Conversation Response:")
#     print_response(response)
#     return response.json()["id"]

# def test_chat_with_assistant(conversation_id, message):
#     data = {"content": message}
#     response = requests.post(f"{BASE_URL}/conversations/{conversation_id}/chat", json=data)
#     print(f"Chat Response (User: {message}):")
#     print_response(response)
#     return response.json()["assistant_message"]

# def test_get_conversation_history(conversation_id):
#     response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/history")
#     print("Get Conversation History Response:")
#     print_response(response)


# def test_get_all_assistants():
#     response = requests.get(f"{BASE_URL}/")
#     print("Get All Assistants Response:")
#     print_response(response)
#     return response.json()


# if __name__ == "__main__":
#     all_assistants = test_get_all_assistants()
#     print(all_assistants)

#     # Create an assistant
#     assistant_id = test_create_assistant()

#     # Create a conversation
#     conversation_id = test_create_conversation(assistant_id)

#     # Chat with the assistant
#     test_chat_with_assistant(conversation_id, "Hello, assistant! I am Bach")
#     test_chat_with_assistant(conversation_id, "What's my name?")
#     test_chat_with_assistant(conversation_id, "Thank you for your help!")

#     # Get conversation history
#     test_get_conversation_history(conversation_id)

#     # Delete the assistant
#     test_delete_assistant(assistant_id)

CONVERSATION_ID = 4  # Replace with an actual conversation ID
def stream_chat():
    url = f"{BASE_URL}/1/conversations/{CONVERSATION_ID}/chat/stream"
    headers = {
        "Content-Type": "application/json",
    }
    body = {
        "content": "Hello, what is machine learning?"
    }

    with requests.post(url,headers=headers, data=json.dumps(body), stream=True) as response:
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        for chunk in response.iter_content():
            print(chunk)

stream_chat()
