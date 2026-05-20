import os
import httpx
from typing import Optional
from app.config import settings

class AIRateLimitError(Exception):
    """Raised when an AI provider returns a 429 Rate Limit error."""
    pass

class AIService:
    # CAPABILITIES: Useful for UI and logic
    # text: standard chat, audio: voice-to-text, vision: image analysis, tools: function calling
    PROVIDER_CAPABILITIES = {
        "openai": ["text", "audio", "vision", "tools"],
        "groq": ["text", "audio", "vision"], # Groq whisper is very fast
        "gemini": ["text", "vision", "tools"] # Gemini 1.5 has native vision/tools
    }

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.groq_api_key = settings.GROQ_API_KEY
        self.gemini_api_key = getattr(settings, "GEMINI_API_KEY", None)
        
        # Default models
        self.openai_model = "gpt-4o"
        self.groq_model = "llama-3.1-8b-instant"
        self.gemini_model = "gemini-1.5-flash-latest"

    def get_configured_providers(self, company_settings=None):
        providers = []
        key_sources = [
            ("openai", "openai_api_key"),
            ("groq", "groq_api_key"),
            ("gemini", "gemini_api_key"),
        ]

        for provider, attr in key_sources:
            key = getattr(company_settings, attr, None) if company_settings else None
            if not key:
                key = getattr(self, attr, None)
            if isinstance(key, str):
                key = key.strip()
            if key:
                providers.append((provider, key))

        return providers

    async def generate_response(
        self, 
        prompt: str, 
        system_instruction: str = "You are a helpful assistant.", 
        provider: str = "openai",
        api_key: Optional[str] = None
    ) -> str:
        """
        Generates a response using the specified provider (openai, groq, or gemini).
        If api_key is provided, it overrides the default environment key.
        """
        if provider == "groq":
            return await self._call_groq(prompt, system_instruction, api_key)
        elif provider == "gemini":
            return await self._call_gemini(prompt, system_instruction, api_key)
        else:
            return await self._call_openai(prompt, system_instruction, api_key)

    async def _call_openai(self, prompt: str, system_instruction: str, api_key: Optional[str] = None) -> str:
        key = api_key or self.openai_api_key
        if not key:
            return "Error: OpenAI API Key not configured."
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=data, headers=headers, timeout=30.0)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                elif resp.status_code == 429:
                    raise AIRateLimitError("OpenAI Rate Limit Reached")
                elif resp.status_code == 401:
                    return "Error: Invalid OpenAI API Key."
                else:
                    return f"Error: OpenAI Error: {resp.text}"
            except AIRateLimitError:
                raise
            except Exception as e:
                return f"OpenAI Connection Error: {str(e)}"

    async def _call_gemini(self, prompt: str, system_instruction: str, api_key: Optional[str] = None) -> str:
        key = api_key or self.gemini_api_key
        if not key:
            return "Error: Gemini API Key not configured."
            
        try:
            import google.generativeai as genai
            from google.api_core import exceptions
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name=self.gemini_model,
                system_instruction=system_instruction
            )
            
            import asyncio
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
                return response.text
            except exceptions.ResourceExhausted:
                print(f"[Gemini] Rate limit reached.")
                raise AIRateLimitError("Gemini Rate Limit Reached")
            except Exception as e:
                print(f"[Gemini Error] {e}")
                raise
        except AIRateLimitError:
            raise
        except Exception as e:
            msg = f"Error: Gemini Error: {str(e)}"
            print(f"[Gemini Fatal] {msg}")
            return msg

    async def _call_groq(self, prompt: str, system_instruction: str, api_key: Optional[str] = None) -> str:
        key = api_key or self.groq_api_key
        if not key:
            return "Error: Groq API Key not configured."
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=data, headers=headers, timeout=30.0)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                elif resp.status_code == 429:
                    raise AIRateLimitError("Groq Rate Limit Reached")
                else:
                    return f"Error: Groq Error: {resp.text}"
            except AIRateLimitError:
                raise
            except Exception as e:
                return f"Error: Groq Connection Error: {str(e)}"

    async def transcribe_audio(
        self, 
        audio_path: str, 
        provider: str = "openai",
        api_key: Optional[str] = None
    ) -> str:
        """
        Transcribes audio using the specified provider.
        """
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."

        if provider == "groq":
            return await self._transcribe_groq(audio_path, api_key)
        else:
            return await self._transcribe_openai(audio_path, api_key)

    async def _transcribe_openai(self, audio_path: str, api_key: Optional[str] = None) -> str:
        key = api_key or self.openai_api_key
        if not key:
            return "Error: OpenAI API Key not configured."
            
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {key}"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                with open(audio_path, "rb") as f:
                    files = {"file": (os.path.basename(audio_path), f, "audio/ogg")}
                    data = {"model": "whisper-1"}
                    
                    resp = await client.post(url, headers=headers, files=files, data=data, timeout=60.0)
                    
                    if resp.status_code == 200:
                        return resp.json().get("text", "")
                    else:
                        return f"OpenAI Whisper Error: {resp.text}"
            except Exception as e:
                return f"OpenAI Connection Error: {str(e)}"

    async def _transcribe_groq(self, audio_path: str, api_key: Optional[str] = None) -> str:
        key = api_key or self.groq_api_key
        if not key:
            return "Error: Groq API Key not configured."
            
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {key}"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                with open(audio_path, "rb") as f:
                    # Groq requires filename and might be strict about format. OGG usually works.
                    files = {"file": (os.path.basename(audio_path), f, "audio/ogg")}
                    # Groq Whisper Model (Distil)
                    data = {"model": "whisper-large-v3-turbo", "response_format": "json"} 
                    
                    resp = await client.post(url, headers=headers, files=files, data=data, timeout=60.0)
                    
                    if resp.status_code == 200:
                        return resp.json().get("text", "")
                    else:
                        return f"Groq Whisper Error: {resp.text}"
            except Exception as e:
                return f"Groq Connection Error: {str(e)}"

    async def summarize_conversation(self, history_text: str, provider: str = "openai", api_key: Optional[str] = None, system_instruction: Optional[str] = None) -> str:
        """
        Generates a concise summary of the conversation history.
        """
        if not system_instruction:
            system_instruction = (
                "Eres un experto en resumir conversaciones de ventas y soporte. "
                "Tu objetivo es crear un resumen CONCISO pero rico en contexto. "
                "Incluye: Nombres, Intenciones de compra, Datos clave (dirección, teléfono), y Estado actual. "
                "NO incluyas saludos genéricos. El resumen debe servir para que el próximo agente entienda todo en 5 segundos."
            )
        prompt = f"Resume la siguiente conversación y añade detalles nuevos al resumen anterior si existe:\n\n{history_text}"
        
        return await self.generate_response(prompt, system_instruction, provider, api_key)

    async def analyze_image(
        self, 
        image_path: str, 
        prompt: str = "Describe esta imagen en detalle para ayudar a una venta.", 
        provider: str = "openai", 
        api_key: Optional[str] = None
    ) -> str:
        """
        Analyzes an image using Vision models (GPT-4o or Llama Vision).
        """
        if not os.path.exists(image_path):
            return "[Error: Imagen no encontrada en servidor]"

        import base64
        
        # Helper to encode image
        def encode_image(path):
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        base64_image = encode_image(image_path)
        
        if provider == "groq":
            return await self._analyze_image_groq(base64_image, prompt, api_key)
        elif provider == "gemini":
            return await self._analyze_image_gemini(base64_image, prompt, api_key)
        else:
            return await self._analyze_image_openai(base64_image, prompt, api_key)

    async def _analyze_image_gemini(self, base64_image: str, prompt: str, api_key: Optional[str] = None) -> str:
        key = api_key or self.gemini_api_key
        if not key:
            return "Error: Gemini API Key not configured for Vision."
            
        try:
            import google.generativeai as genai
            import base64
            from io import BytesIO
            from PIL import Image
            
            genai.configure(api_key=key)
            # Use 1.5 Flash or Pro for Vision
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            
            # Decode base64 to PIL Image
            img_data = base64.b64decode(base64_image)
            img = Image.open(BytesIO(img_data))
            
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: model.generate_content([prompt, img]))
            
            return response.text
        except Exception as e:
            return f"Gemini Vision Error: {str(e)}"

    async def _analyze_image_openai(self, base64_image: str, prompt: str, api_key: Optional[str] = None) -> str:
        key = api_key or self.openai_api_key
        if not key:
            return "Error: OpenAI API Key not configured for Vision."
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=data, headers=headers, timeout=60.0)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                else:
                    return f"OpenAI Vision Error: {resp.text}"
            except Exception as e:
                return f"OpenAI Vision Connection Error: {str(e)}"

    async def _analyze_image_groq(self, base64_image: str, prompt: str, api_key: Optional[str] = None) -> str:
        key = api_key or self.groq_api_key
        if not key:
            return "Error: Groq API Key not configured for Vision."
            
        # Groq Vision Model
        model = "llama-3.2-11b-vision-preview" # or 90b if available/needed
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=data, headers=headers, timeout=60.0)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                else:
                    return f"Groq Vision Error: {resp.text}"
            except Exception as e:
                return f"Groq Vision Connection Error: {str(e)}"

    async def _analyze_image_groq(self, base64_image: str, prompt: str, api_key: Optional[str] = None) -> str:
        key = api_key or self.groq_api_key
        if not key:
            return "Error: Groq API Key not configured for Vision."
            
        # Groq Vision Model
        model = "llama-3.2-11b-vision-preview" # or 90b if available/needed
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=data, headers=headers, timeout=60.0)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                else:
                    return f"Groq Vision Error: {resp.text}"
            except Exception as e:
                return f"Groq Vision Connection Error: {str(e)}"

    async def get_embedding(self, text: str, api_key: Optional[str] = None) -> Optional[list]:
        """
        Generates an embedding vector. 
        Prioritizes OpenAI if key is present.
        Falls back to local FastEmbed if no OpenAI key is found.
        """
        key = api_key or self.openai_api_key
        
        # 1. Try OpenAI
        if key:
            url = "https://api.openai.com/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "text-embedding-3-small",
                "input": text
            }
            
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(url, json=data, headers=headers, timeout=10.0)
                    if resp.status_code == 200:
                        return resp.json()["data"][0]["embedding"]
                    else:
                        print(f"[Embedding] OpenAI Error: {resp.text}. Falling back to local...")
                except Exception as e:
                    print(f"[Embedding] Connection Error: {str(e)}. Falling back to local...")

        # 2. Fallback to Local FastEmbed
        return await self._get_local_embedding(text)

    async def _get_local_embedding(self, text: str) -> Optional[list]:
        """
        Uses FastEmbed to generate embeddings locally (CPU friendly).
        """
        try:
            # Lazy import to avoid overhead if not used
            from fastembed import TextEmbedding
            
            # This will download the model on first use (~200MB)
            # We use 'BAAI/bge-small-en-v1.5' or multilingual if needed.
            # 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' is good for mixed (EN/ES)
            # FastEmbed default is 'BAAI/bge-small-en-v1.5' which is decent.
            # Let's use a lightweight multilingual one if possible, or sticking to default is fine for now.
            # FastEmbed supported models: https://qdrant.github.io/fastembed/examples/Supported_Models/
            
            # We'll use the default for now, acts as a general purpose.
            # caching the model instance would be better in a real service to avoid reloading.
            if not hasattr(self, "_local_embedding_model"):
                print("[Embedding] Loading local FastEmbed model (multilingual-e5-large)...")
                # 'intfloat/multilingual-e5-large' had ONNX path issues on Windows.
                # Switching to 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
                # It is lighter, robust, and supports 50+ languages including Spanish.
                self._local_embedding_model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            
            # FastEmbed returns a generator of numpy arrays
            embeddings = list(self._local_embedding_model.embed([text]))
            if embeddings:
                return embeddings[0].tolist() # Convert numpy to list
            return None
            
        except ImportError:
            print("[Embedding] Error: 'fastembed' not installed. Run 'pip install fastembed'.")
            return None
        except Exception as e:
            print(f"[Embedding] Local Error: {str(e)}")
            return None

# Singleton instance
ai_service = AIService()
