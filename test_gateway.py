"""
Quick script to test Gateway Service with current configuration
"""

import httpx
import asyncio


async def test_gateway():
    """Test Gateway Service chat endpoint"""
    
    print("Testing Gateway Service...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/chat",
                json={"query": "Hello, say hi in one sentence."},
                timeout=30.0
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ Success!")
                print(f"Answer: {data.get('answer', 'No answer')[:200]}")
                print(f"Citations: {len(data.get('citations', []))}")
            else:
                print(f"\n✗ Error: HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_gateway())
