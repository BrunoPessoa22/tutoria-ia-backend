"""
Test Claude API Integration
"""
import asyncio
from services.claude_tutor import ClaudeTutor

async def test_claude():
    """Test Claude API with a simple request"""
    tutor = ClaudeTutor()

    print("🤖 Testing Claude API connection...")

    try:
        # Test with a simple question
        response = await tutor.generate_response(
            student_profile={
                "name": "Test User",
                "level": "intermediate",
                "native_language": "Portuguese"
            },
            message="Hello! Can you help me learn English?",
            lesson_context={
                "topic": "Greetings",
                "objective": "Practice basic greetings"
            }
        )

        print("✅ Claude API is working!")
        print(f"Response: {response['response'][:200]}...")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_claude())