# app/utils/auth.py
from fastapi.security import HTTPBearer

SECRET_KEY = "super-secret-key-change-me"  # ← 記得改成你自己的
ALGORITHM = "HS256"

bearer = HTTPBearer()

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

bearer = HTTPBearer()


def require_role(allowed_roles: list[str]):
    def wrapper(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
        token = credentials.credentials  # ★ 正確取得 token
        print("@@@@@", token)

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print("@@@@@", payload)
            role = payload.get("role")
            print("@@@@@", role)

            if role is None:
                print("@@@@@", 1)
                raise HTTPException(status_code=401, detail="Token missing role")

            if role not in allowed_roles:
                print("@@@@@", 2)
                raise HTTPException(status_code=403, detail="Permission denied")

            return payload

        except jwt.ExpiredSignatureError:
            print("@@@@@", 3)
            raise HTTPException(status_code=401, detail="Token expired")

        except jwt.InvalidTokenError:
            print("@@@@@", 4)
            raise HTTPException(status_code=401, detail="Invalid token")

    return wrapper
