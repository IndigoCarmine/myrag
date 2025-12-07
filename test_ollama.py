"""
Quick test script to verify Ollama model is working
"""

import httpx
import asyncio
import json


async def test_ollama():
    """Test Ollama with available models"""
    
    models_to_test = ["deepseek-r1:8b", "gemma3:4b", "gemma3:1b"]
    
    for model in models_to_test:
        print(f"\nTesting Ollama with {model} model...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": "Say hello in one sentence.",
                        "stream": False
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ Success with {model}!")
                    print(f"Response: {data.get('response', 'No response')[:100]}...")
                    print(f"\nOllama is working correctly with {model}!")
                    return model, True
                else:
                    print(f"✗ Error with {model}: HTTP {response.status_code}")
                    print(f"Response: {response.text[:200]}")
        
        except Exception as e:
            print(f"✗ Error with {model}: {e}")
    
    return None, False


if __name__ == "__main__":
    asyncio.run(test_ollama())
