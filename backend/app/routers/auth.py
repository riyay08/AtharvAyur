from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_db
from app.models.user import User
from app.schemas.auth import AuthSessionRequest, TokenResponse

router = APIRouter(tags=["auth"])

_TOKEN_TTL_SECONDS = 90 * 24 * 60 * 60


@router.post("/auth/token", response_model=TokenResponse)
def issue_access_token(
    body: AuthSessionRequest = AuthSessionRequest(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    if body.user_id is not None:
        user = db.get(User, body.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    else:
        user = User()
        db.add(user)
        db.flush()

    now = int(time.time())
    claims = {
        "user_id": str(user.id),
        "sub": str(user.id),
        "exp": now + _TOKEN_TTL_SECONDS,
    }
    token = jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    db.commit()
    return TokenResponse(access_token=token, token_type="bearer", user_id=user.id)
