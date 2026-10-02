from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.user import User

security = HTTPBearer()



def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        sub = str(payload.get("sub", ""))
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token subject")

        user = None
        if sub.isdigit():
            user = db.query(User).filter(User.id == int(sub)).first()

        if not user:
            user = db.query(User).filter(User.email == sub).first()

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user