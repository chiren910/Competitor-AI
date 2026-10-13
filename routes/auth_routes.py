from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from utils.auth_service import register_user, login_user, verify_session, delete_session

router = APIRouter(prefix="/auth", tags=["authentication"])

COOKIE_NAME = "ca_session_token"
COOKIE_MAX_AGE = 14 * 24 * 3600  # 14 days


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


def get_token_from_request(request: Request) -> Optional[str]:
    """Extract auth token from Cookie, Authorization header, or query param."""
    # 1. Cookie
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    # 2. Authorization Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    # 3. Query Param
    token = request.query_params.get("auth_token")
    if token:
        return token
    return None


def get_authenticated_user(request: Request) -> Optional[dict]:
    """Helper to verify current request user, returns user dict or None."""
    token = get_token_from_request(request)
    if not token:
        return None
    return verify_session(token)


@router.post("/register")
def api_register(payload: RegisterRequest, response: Response):
    """Register a new user account."""
    try:
        user, token = register_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            company=payload.company or ""
        )
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            path="/"
        )
        return {
            "success": True,
            "message": "Registration successful",
            "user": user,
            "token": token
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login")
def api_login(payload: LoginRequest, response: Response):
    """Authenticate with email and password."""
    try:
        user, token = login_user(
            email=payload.email,
            password=payload.password
        )
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            path="/"
        )
        return {
            "success": True,
            "message": "Login successful",
            "user": user,
            "token": token
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@router.get("/me")
def api_me(request: Request):
    """Check current user session."""
    user = get_authenticated_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    return {"authenticated": True, "user": user}


@router.post("/logout")
def api_logout(request: Request, response: Response):
    """Log out current user and clear session."""
    token = get_token_from_request(request)
    if token:
        delete_session(token)
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"success": True, "message": "Successfully logged out"}
