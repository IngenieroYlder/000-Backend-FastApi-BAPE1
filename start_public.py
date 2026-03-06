import os
import sys
import uvicorn
import threading
import time
from pyngrok import ngrok, conf

def start_ngrok():
    # Ensure ngrok lists on the right port
    public_url = ngrok.connect(8000).public_url
    print("\n" + "="*60)
    print(f"🚀  PUBLIC ACCESS URL: {public_url}")
    print("="*60)
    print("⚠️  IMPORTANT FOR GOOGLE CALENDAR:")
    print(f"1. Go to Google Cloud Console > Credentials")
    print(f"2. Add this RI to 'Authorized redirect URIs':")
    print(f"   {public_url}/calendar/callback")
    print(f"3. Update your .env file locally (optional, but recommended if sticking to this url):")
    print(f"   GOOGLE_REDIRECT_URI={public_url}/calendar/callback")
    print("="*60 + "\n")
    
    # Store in environment for the app to see (if it reads it dynamically, which we should update routes to do)
    os.environ["Note_From_Ngrok"] = "Please update GOOGLE_REDIRECT_URI in .env manually or handle dynamically"
    return public_url

def start_server():
    # Use the same command as standard start but python driven
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False) # Reload false to avoid duplicate ngrok tunnels

if __name__ == "__main__":
    # Check if pyngrok is installed
    try:
        from pyngrok import ngrok
    except ImportError:
        print("Installing pyngrok...")
        os.system(f"{sys.executable} -m pip install pyngrok")

    # Start Ngrok in a separate thread (or just before server if blocking, but uvicorn blocks)
    # Ngrok is non-blocking usually with pyngrok
    try:
        public_url = start_ngrok()
        
        # We need to inject this URL into the app's config if we want it to be automatic
        # However, FastAPI loads .env at startup. 
        # Ideally, we set an env var HERE before importing app
        os.environ["GOOGLE_REDIRECT_URI"] = f"{public_url}/calendar/callback"
        os.environ["BASE_PUBLIC_URL"] = public_url
        print(f"[System] Overriding GOOGLE_REDIRECT_URI in memory to: {os.environ['GOOGLE_REDIRECT_URI']}")
        print(f"[System] Setting BASE_PUBLIC_URL to: {os.environ['BASE_PUBLIC_URL']}")
        
        # Start App
        start_server()
        
    except KeyboardInterrupt:
        print("Shutting down...")
        ngrok.kill()
