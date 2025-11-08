"""
Authentication Routes
User registration and login
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from typing import Optional
import hashlib
from datetime import datetime

from db import Database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

security = HTTPBasic()


class UserSignup(BaseModel):
    """User signup request model"""
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model"""
    user_id: str
    email: str
    username: str
    created_at: datetime


def hash_password(password: str) -> str:
    """Hash password using SHA256 (for MVP - use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed


@router.options("/signup")
async def signup_options():
    """Handle OPTIONS preflight for signup"""
    # CORS middleware should handle this, but explicit handler ensures it works
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    )


@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserSignup):
    """
    Create a new user account
    
    Args:
        user_data: User signup information
    
    Returns:
        Created user information
    """
    try:
        users_collection = Database.get_collection("users")
        
        # Check if user already exists
        existing_user = await users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        
        existing_username = await users_collection.find_one({"username": user_data.username})
        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        
        # Create user
        user_id = f"user_{hashlib.md5(user_data.email.encode()).hexdigest()[:12]}"
        password_hash = hash_password(user_data.password)
        
        user_doc = {
            "user_id": user_id,
            "email": user_data.email,
            "username": user_data.username,
            "password_hash": password_hash,
            "profiles": [],
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        result = await users_collection.insert_one(user_doc)
        
        if result.inserted_id:
            logger.info(f"User created: {user_id} ({user_data.email})")
            return UserResponse(
                user_id=user_id,
                email=user_data.email,
                username=user_data.username,
                created_at=user_doc["created_at"]
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.options("/login")
async def login_options():
    """Handle OPTIONS preflight for login"""
    # CORS middleware should handle this, but explicit handler ensures it works
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    )


@router.post("/login", response_model=UserResponse)
async def login(credentials: UserLogin):
    """
    Login user and return user information
    
    Args:
        credentials: Login credentials
    
    Returns:
        User information if login successful
    """
    try:
        users_collection = Database.get_collection("users")
        
        # Find user by email
        user = await users_collection.find_one({"email": credentials.email})
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Update last login
        await users_collection.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        logger.info(f"User logged in: {user['user_id']}")
        return UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            username=user["username"],
            created_at=user["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Get user information by user_id
    
    Args:
        user_id: User identifier
    
    Returns:
        User information
    """
    try:
        users_collection = Database.get_collection("users")
        user = await users_collection.find_one({"user_id": user_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            username=user["username"],
            created_at=user["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")
