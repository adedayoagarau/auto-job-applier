"""
Authentication module for AutoJobApplier
Provides JWT-based authentication for API endpoints
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, validator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import environment configuration
try:
    from src.env_config import env_config
    SECRET_KEY = env_config.jwt_secret_key
    ALGORITHM = env_config.jwt_algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = env_config.access_token_expire_minutes
except ImportError:
    # Fallback if env_config not available
    import os
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production-use-env-var")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing (using argon2 instead of bcrypt for better compatibility)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# HTTP Bearer security scheme
security = HTTPBearer()


# Pydantic models
class UserCreate(BaseModel):
    """User registration model"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    user_id: Optional[int] = None


class User(BaseModel):
    """User model"""
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if email is None:
            raise credentials_exception

        token_data = TokenData(email=email, user_id=user_id)
        return token_data

    except JWTError:
        raise credentials_exception


# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency to get the current authenticated user from JWT token
    Use this in route dependencies: current_user: TokenData = Depends(get_current_user)
    """
    token = credentials.credentials
    token_data = verify_token(token)
    return token_data


# Simple in-memory user store (replace with database in production)
class UserStore:
    """Simple in-memory user storage (replace with database in production)"""

    def __init__(self):
        self.users = {}
        self.user_id_counter = 1
        # Create default admin user
        self._create_default_user()

    def _create_default_user(self):
        """Create a default admin user for testing"""
        default_email = "admin@autojobapplier.com"
        default_password = "Admin123!"

        if default_email not in self.users:
            self.users[default_email] = {
                "id": self.user_id_counter,
                "email": default_email,
                "full_name": "Admin User",
                "hashed_password": get_password_hash(default_password),
                "is_active": True,
                "created_at": datetime.now()
            }
            self.user_id_counter += 1

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        return self.users.get(email)

    def create_user(self, email: str, password: str, full_name: Optional[str] = None) -> dict:
        """Create a new user"""
        if email in self.users:
            raise ValueError("User already exists")

        user = {
            "id": self.user_id_counter,
            "email": email,
            "full_name": full_name,
            "hashed_password": get_password_hash(password),
            "is_active": True,
            "created_at": datetime.now()
        }

        self.users[email] = user
        self.user_id_counter += 1

        return user

    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate a user by email and password"""
        user = self.get_user_by_email(email)

        if not user:
            return None

        if not verify_password(password, user["hashed_password"]):
            return None

        if not user["is_active"]:
            return None

        return user


# Global user store instance
user_store = UserStore()


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate a user"""
    return user_store.authenticate_user(email, password)


def create_user(email: str, password: str, full_name: Optional[str] = None) -> dict:
    """Create a new user"""
    return user_store.create_user(email, password, full_name)
