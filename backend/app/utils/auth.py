# app/utils/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt

SECRET_KEY = "super-secret-key-change-me"   # ← 記得改成你自己的
ALGORITHM = "HS256"

bearer = HTTPBearer()


def require_role(allowed_roles: list[str]):
    """
    在 router 裡面這樣用：
    @router.get("/xxx", dependencies=[Depends(require_role(["engineer", "admin"]))])
    """
    def wrapper(token=Depends(bearer)):
        try:
            payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            role = payload.get("role")
            if role not in allowed_roles:
                raise HTTPException(status_code=403, detail="Permission denied")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

    return wrapper
