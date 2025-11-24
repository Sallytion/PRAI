"""
Authentication API Routes - MongoDB/Beanie
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
import httpx
from datetime import datetime

from app.core.auth import create_access_token, verify_token
from app.models.user import User
from app.config import get_settings

settings = get_settings()
router = APIRouter()

# OAuth configuration
oauth = OAuth()
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params={'scope': 'repo user'},
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    client_kwargs={'scope': 'repo user'},
)


@router.get("/github/login")
async def github_login(request: Request):
    """Initiate GitHub OAuth login"""
    redirect_uri = settings.GITHUB_REDIRECT_URI
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request):
    """Handle GitHub OAuth callback"""
    try:
        # Get access token from GitHub
        token = await oauth.github.authorize_access_token(request)
        
        # Get user info from GitHub
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f"Bearer {token['access_token']}"}
            )
            github_user = user_response.json()
        
        # Check if user exists
        user = await User.find_one(User.github_id == github_user['id'])
        
        if not user:
            # Create new user
            user = User(
                github_id=github_user['id'],
                username=github_user['login'],
                email=github_user.get('email'),
                avatar_url=github_user.get('avatar_url'),
                access_token=token['access_token']
            )
            await user.insert()
        else:
            # Update existing user
            user.access_token = token['access_token']
            user.avatar_url = github_user.get('avatar_url')
            user.email = github_user.get('email')
            user.updated_at = datetime.utcnow()
            await user.save()
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": str(user.id), "github_id": user.github_id}
        )
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"http://localhost:8000/?token={access_token}",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub authentication failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user(request: Request):
    """Get current authenticated user"""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = auth_header.split(" ")[1]
    
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = await User.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": str(user.id),
        "github_id": user.github_id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat()
    }


@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out"}
