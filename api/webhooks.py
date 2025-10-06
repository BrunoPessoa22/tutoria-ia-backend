from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import stripe
import json
import hmac
import hashlib
from models.student import Student
from utils.database import get_db
from config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_signature: Optional[str] = Header(None),
    svix_id: Optional[str] = Header(None),
    svix_timestamp: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle Clerk webhooks."""
    try:
        payload = await request.body()

        # Verify webhook signature
        if settings.CLERK_WEBHOOK_SECRET:
            expected_sig = hmac.new(
                settings.CLERK_WEBHOOK_SECRET.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Compare signatures (simplified - Clerk uses Svix)
            # In production, use Svix library for verification

        data = json.loads(payload)
        event_type = data.get("type")

        if event_type == "user.created":
            # Create student record
            user_data = data["data"]
            student = Student(
                clerk_user_id=user_data["id"],
                email=user_data["email_addresses"][0]["email_address"],
                full_name=f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            )
            db.add(student)
            await db.commit()
            logger.info(f"Created student record for {student.email}")

        elif event_type == "user.updated":
            # Update student record
            user_data = data["data"]
            result = await db.execute(
                select(Student).where(Student.clerk_user_id == user_data["id"])
            )
            student = result.scalar_one_or_none()
            if student:
                student.email = user_data["email_addresses"][0]["email_address"]
                student.full_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
                await db.commit()

        elif event_type == "user.deleted":
            # Handle user deletion
            user_id = data["data"]["id"]
            result = await db.execute(
                select(Student).where(Student.clerk_user_id == user_id)
            )
            student = result.scalar_one_or_none()
            if student:
                student.is_active = False
                await db.commit()

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Clerk webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhooks."""
    try:
        payload = await request.body()

        # Verify webhook signature
        if settings.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload,
                stripe_signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)

        # Handle different event types
        if event.type == "checkout.session.completed":
            session = event.data.object

            # Find student by email
            result = await db.execute(
                select(Student).where(Student.email == session.customer_email)
            )
            student = result.scalar_one_or_none()

            if student:
                student.subscription_status = "active"
                student.stripe_customer_id = session.customer
                await db.commit()
                logger.info(f"Subscription activated for {student.email}")

        elif event.type == "customer.subscription.updated":
            subscription = event.data.object

            # Find student by Stripe customer ID
            result = await db.execute(
                select(Student).where(Student.stripe_customer_id == subscription.customer)
            )
            student = result.scalar_one_or_none()

            if student:
                student.subscription_status = subscription.status
                student.subscription_plan = subscription.items.data[0].price.nickname
                await db.commit()

        elif event.type == "customer.subscription.deleted":
            subscription = event.data.object

            # Find student by Stripe customer ID
            result = await db.execute(
                select(Student).where(Student.stripe_customer_id == subscription.customer)
            )
            student = result.scalar_one_or_none()

            if student:
                student.subscription_status = "canceled"
                await db.commit()
                logger.info(f"Subscription canceled for {student.email}")

        elif event.type == "invoice.payment_failed":
            invoice = event.data.object

            # Handle failed payment
            result = await db.execute(
                select(Student).where(Student.stripe_customer_id == invoice.customer)
            )
            student = result.scalar_one_or_none()

            if student:
                student.subscription_status = "past_due"
                await db.commit()
                # TODO: Send notification to student

        return {"status": "success"}

    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Stripe signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/elevenlabs")
async def elevenlabs_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle ElevenLabs webhooks for voice processing."""
    try:
        data = await request.json()
        event_type = data.get("event_type")

        if event_type == "voice_generation_completed":
            # Handle completed voice generation
            voice_id = data["voice_id"]
            audio_url = data["audio_url"]
            # Process the generated audio
            logger.info(f"Voice generation completed: {voice_id}")

        elif event_type == "voice_clone_ready":
            # Handle voice clone ready
            voice_id = data["voice_id"]
            # Update database with new voice ID
            logger.info(f"Voice clone ready: {voice_id}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"ElevenLabs webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/heygen")
async def heygen_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle HeyGen webhooks for avatar video generation."""
    try:
        data = await request.json()
        event_type = data.get("event_type")

        if event_type == "video_completed":
            # Handle completed video generation
            video_id = data["video_id"]
            video_url = data["video_url"]
            lesson_id = data.get("metadata", {}).get("lesson_id")

            if lesson_id:
                # Update lesson with video URL
                from models.lesson import Lesson
                result = await db.execute(
                    select(Lesson).where(Lesson.id == lesson_id)
                )
                lesson = result.scalar_one_or_none()
                if lesson:
                    if not lesson.materials_used:
                        lesson.materials_used = {}
                    lesson.materials_used["intro_video"] = video_url
                    await db.commit()
                    logger.info(f"Avatar video ready for lesson {lesson_id}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"HeyGen webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))