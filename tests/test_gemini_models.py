"""
Test script to list available Gemini models
"""
import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load from both locations
load_dotenv()  # Load from root
load_dotenv("src/.env")  # Load from src/

async def list_gemini_models():
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    print("\n🔍 Fetching available Gemini models...\n")
    
    # List models endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()
            
            print("📋 Available models:\n")
            for model in result.get("models", []):
                name = model.get("name", "").replace("models/", "")
                display_name = model.get("displayName", "")
                supported_methods = model.get("supportedGenerationMethods", [])
                
                # Check if it supports generateContent
                if "generateContent" in supported_methods:
                    print(f"✅ {name}")
                    print(f"   Display Name: {display_name}")
                    print(f"   Methods: {', '.join(supported_methods)}")
                    print()
                else:
                    print(f"❌ {name} (doesn't support generateContent)")
                    print()
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            if hasattr(e, 'response'):
                print(f"Response: {e.response.text}")

if __name__ == "__main__":
    asyncio.run(list_gemini_models())

