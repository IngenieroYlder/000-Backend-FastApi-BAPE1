import httpx
import asyncio
import os

async def test_key():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("Error: define GROQ_API_KEY en variables de entorno.")
        return
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",
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
