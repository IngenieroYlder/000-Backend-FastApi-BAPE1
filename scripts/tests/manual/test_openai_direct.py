import httpx
import asyncio
import os

async def test_key():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("Error: define OPENAI_API_KEY en variables de entorno.")
        return
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo", # Use cheaper model for test
        "messages": [{"role": "user", "content": "hola"}],
        "max_tokens": 5
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=data, headers=headers, timeout=10.0)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_key())
