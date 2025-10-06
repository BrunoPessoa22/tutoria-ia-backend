import anthropic
from typing import Dict, List, Optional, Any
import json
import logging
from config import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class ClaudeTutor:
    """Core AI tutoring logic using Claude."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL

    async def conduct_lesson(
        self,
        student_profile: Dict[str, Any],
        lesson_plan: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        user_message: str
    ) -> Dict[str, Any]:
        """Conduct a tutoring session interaction."""
        try:
            # Build context
            system_prompt = self._build_system_prompt(student_profile, lesson_plan)

            # Format conversation history
            messages = self._format_conversation(conversation_history)
            messages.append({"role": "user", "content": user_message})

            # Get response from Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE,
                system=system_prompt,
                messages=messages
            )

            # Parse response and extract teaching elements
            ai_response = response.content[0].text
            analysis = self._analyze_response(ai_response, user_message)

            return {
                "response": ai_response,
                "analysis": analysis,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Error in Claude tutoring session: {e}")
            raise

    async def generate_lesson_plan(
        self,
        student_profile: Dict[str, Any],
        topic: str,
        duration_minutes: int,
        curriculum_module: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a personalized lesson plan."""
        prompt = f"""Create a detailed {duration_minutes}-minute English lesson plan for the following student:

Student Profile:
- Name: {student_profile.get('full_name')}
- Level: {student_profile.get('english_level')}
- Learning Style: {student_profile.get('learning_style')}
- Weak Areas: {', '.join(student_profile.get('weak_areas', []))}
- Interests: {', '.join(student_profile.get('interests', []))}

Topic: {topic}
{f'Curriculum Module: {curriculum_module}' if curriculum_module else ''}

Provide a structured JSON response with:
1. warm_up (5 min) - Engaging opener
2. introduction (10 min) - New concepts
3. practice (20 min) - Interactive exercises
4. production (20 min) - Student speaks/writes
5. wrap_up (5 min) - Review and homework
6. vocabulary - Key words to teach
7. grammar_points - Grammar to cover
8. materials_needed - Resources required
9. success_criteria - How to measure success
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse and structure the response
        return self._parse_lesson_plan(response.content[0].text)

    async def assess_student_response(
        self,
        student_message: str,
        expected_response: Optional[str] = None,
        assessment_criteria: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Assess a student's response for errors and provide feedback."""
        prompt = f"""Analyze the following student response in detail:

Student Response: "{student_message}"
{f'Expected/Model Response: "{expected_response}"' if expected_response else ''}

Provide detailed assessment including:
1. Grammar errors (with corrections)
2. Vocabulary usage (appropriateness and alternatives)
3. Pronunciation issues (if detectable from spelling)
4. Fluency and coherence
5. Overall score (0-100)
6. Specific feedback for improvement
7. Positive reinforcement

Return as structured JSON."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.content[0].text)

    async def generate_follow_up_questions(
        self,
        lesson_content: Dict[str, Any],
        student_performance: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized follow-up questions based on lesson."""
        prompt = f"""Based on this lesson and student performance, generate 5 follow-up questions
        that reinforce weak areas and build on strengths.

Lesson Topics: {lesson_content.get('topics')}
Student Weak Areas: {student_performance.get('errors')}
Student Strengths: {student_performance.get('strengths')}

Questions should be progressively challenging and engaging."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract questions from response
        return self._extract_questions(response.content[0].text)

    async def create_placement_test_question(
        self,
        level: str,
        question_number: int,
        previous_performance: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate adaptive placement test questions."""
        prompt = f"""Create placement test question #{question_number} for estimated level {level}.
{f'Previous performance: {previous_performance}' if previous_performance else ''}

Provide:
1. Question text
2. Question type (multiple_choice, fill_blank, open_ended, speaking)
3. Options (if applicable)
4. Correct answer
5. Difficulty level
6. Skill being tested"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.content[0].text)

    def _build_system_prompt(
        self,
        student_profile: Dict[str, Any],
        lesson_plan: Dict[str, Any]
    ) -> str:
        """Build a comprehensive system prompt for the tutor."""
        return f"""You are an expert English tutor conducting a personalized lesson.

Student Profile:
- Name: {student_profile.get('full_name')}
- Level: {student_profile.get('english_level')} (CEFR)
- Native Language: {student_profile.get('native_language')}
- Learning Goals: {student_profile.get('learning_goals')}
- Learning Style: {student_profile.get('learning_style')}
- Weak Areas: {', '.join(student_profile.get('weak_areas', []))}
- Interests: {', '.join(student_profile.get('interests', []))}

Today's Lesson Plan:
- Topic: {lesson_plan.get('topic')}
- Objectives: {lesson_plan.get('objectives')}
- Vocabulary Focus: {', '.join(lesson_plan.get('vocabulary', []))}
- Grammar Focus: {lesson_plan.get('grammar_points')}

Teaching Guidelines:
1. Be encouraging and patient
2. Correct errors gently with explanations
3. Use examples relevant to student's interests
4. Adapt language complexity to student's level
5. Encourage student to speak/write as much as possible
6. Provide clear, structured explanations
7. Use Portuguese for clarification only when necessary
8. Celebrate progress and effort

Remember to maintain a conversational, friendly tone while being educational."""

    def _format_conversation(
        self,
        history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Format conversation history for Claude API."""
        formatted = []
        for msg in history[-10:]:  # Keep last 10 messages for context
            role = "assistant" if msg.get("role") == "ai" else "user"
            formatted.append({
                "role": role,
                "content": msg.get("content", "")
            })
        return formatted

    def _analyze_response(
        self,
        ai_response: str,
        user_message: str
    ) -> Dict[str, Any]:
        """Analyze the AI response for teaching elements."""
        analysis = {
            "corrections_made": [],
            "new_vocabulary": [],
            "grammar_explained": [],
            "encouragement_given": False,
            "question_asked": "?" in ai_response,
            "example_provided": False
        }

        # Basic analysis (can be enhanced with NLP)
        if "correct" in ai_response.lower() or "error" in ai_response.lower():
            analysis["corrections_made"].append("Grammar or vocabulary correction")

        if "for example" in ai_response.lower() or "e.g." in ai_response.lower():
            analysis["example_provided"] = True

        if "great" in ai_response.lower() or "excellent" in ai_response.lower() or "good job" in ai_response.lower():
            analysis["encouragement_given"] = True

        return analysis

    def _parse_lesson_plan(self, response_text: str) -> Dict[str, Any]:
        """Parse lesson plan from Claude's response."""
        try:
            # Try to extract JSON if present
            if "{" in response_text and "}" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
        except:
            pass

        # Fallback to structured parsing
        return {
            "warm_up": "Extracted warm-up activity",
            "introduction": "New concepts introduction",
            "practice": "Practice exercises",
            "production": "Student production activity",
            "wrap_up": "Lesson summary and homework",
            "vocabulary": ["word1", "word2"],
            "grammar_points": ["grammar point"],
            "materials_needed": ["materials"],
            "success_criteria": ["criteria"],
            "raw_response": response_text
        }

    def _extract_questions(self, response_text: str) -> List[str]:
        """Extract questions from Claude's response."""
        questions = []
        lines = response_text.split("\n")
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                # Remove numbering or bullets
                question = line.lstrip("0123456789.-• ").strip()
                if question:
                    questions.append(question)

        # Ensure we have 5 questions
        return questions[:5] if len(questions) >= 5 else questions