"""
Test API Keys for Claude and ElevenLabs
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_apis():
    """Test both Claude and ElevenLabs APIs"""

    # Test Claude API
    print("\n🤖 Testing Claude API...")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'Hello! Claude API is working!' in a friendly way."}
            ]
        )
        print("✅ Claude API is working!")
        print(f"   Response: {message.content[0].text}")
    except Exception as e:
        print(f"❌ Claude API Error: {e}")

    # Test ElevenLabs API
    print("\n🔊 Testing ElevenLabs API...")
    try:
        import aiohttp
        api_key = os.getenv('ELEVENLABS_API_KEY')

        async with aiohttp.ClientSession() as session:
            # Get available voices
            url = "https://api.elevenlabs.io/v1/voices"
            headers = {"xi-api-key": api_key}

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    voices = data.get("voices", [])
                    print("✅ ElevenLabs API is working!")
                    print(f"   Available voices: {len(voices)}")
                    if voices:
                        print(f"   First voice: {voices[0].get('name', 'Unknown')}")
                else:
                    print(f"❌ ElevenLabs API Error: Status {response.status}")
    except Exception as e:
        print(f"❌ ElevenLabs API Error: {e}")

    print("\n✨ API Key Configuration Summary:")
    print(f"   Claude API Key: {'✅ Configured' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing'}")
    print(f"   ElevenLabs API Key: {'✅ Configured' if os.getenv('ELEVENLABS_API_KEY') else '❌ Missing'}")
    print(f"   HeyGen API Key: {'⏳ Not configured yet' if not os.getenv('HEYGEN_API_KEY') or os.getenv('HEYGEN_API_KEY') == 'your_heygen_key_here' else '✅ Configured'}")

if __name__ == "__main__":
    asyncio.run(test_apis())