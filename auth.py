import os
import jwt
from fastapi import HTTPException, Header
from typing import Optional

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")


async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify Clerk JWT token and return user data.

    For development, if no auth header is provided, return mock user.
    For production, require valid token.
    """
    # Development mode: allow unauthenticated access
    if os.getenv("ENVIRONMENT") == "development" and not authorization:
        return {
            "user_id": "dev_user_123",
            "email": "dev@example.com",
            "name": "Dev User"
        }

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "")

    if not CLERK_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Clerk secret key not configured")

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            CLERK_SECRET_KEY,
            algorithms=["RS256"],
            options={"verify_signature": True}
        )

        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name", "")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Get current authenticated user."""
    return await verify_token(authorization)
