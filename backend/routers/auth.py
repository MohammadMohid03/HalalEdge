import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate, UserOut, Token, UserLogin
from backend.services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    send_simulated_email
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered."
        )

    # Create new user
    hashed_password = get_password_hash(user_in.password)
    verification_token = secrets.token_urlsafe(32)
    db_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password=hashed_password,
        country=user_in.country,
        is_verified=False,
        verification_token=verification_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Send simulated verification email
    verify_link = f"http://localhost:8000/api/auth/verify?token={verification_token}"
    email_body = f"""Assalamu Alaikum {db_user.full_name},

Thank you for signing up for HalalEdge! 

Before you can use your account, please verify your email address by clicking the link below:

{verify_link}

(Alternatively, copy-paste the URL into your browser)

Regards,
The HalalEdge Team
"""
    send_simulated_email(db_user.email, "Verify your HalalEdge Account", email_body)

    # Create access token (still allow immediate registration token so UI flow is smooth)
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

from fastapi.responses import HTMLResponse

@router.get("/verify", response_class=HTMLResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.verification_token == token).first()
    if not db_user:
        return HTMLResponse(content="""
        <html>
            <head>
                <title>Verification Failed — HalalEdge</title>
                <style>
                    body { font-family: sans-serif; background-color: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                    .card { background: #1e293b; padding: 2.5rem; border-radius: 16px; border: 1px solid #334155; text-align: center; max-width: 450px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3); }
                    h1 { color: #ef4444; margin-bottom: 1rem; font-size: 1.8rem; }
                    p { color: #94a3b8; line-height: 1.6; font-size: 0.95rem; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Verification Failed</h1>
                    <p>The verification link is invalid, expired, or has already been used.</p>
                </div>
            </body>
        </html>
        """, status_code=400)
    
    db_user.is_verified = True
    db_user.verification_token = None
    db.commit()
    
    return HTMLResponse(content="""
    <html>
        <head>
            <title>Email Verified — HalalEdge</title>
            <style>
                body { font-family: sans-serif; background-color: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .card { background: #1e293b; padding: 2.5rem; border-radius: 16px; border: 1px solid #334155; text-align: center; max-width: 450px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3); }
                h1 { color: #10b981; margin-bottom: 1rem; font-size: 1.8rem; }
                p { color: #94a3b8; line-height: 1.6; font-size: 0.95rem; }
                a { display: inline-block; margin-top: 1.5rem; background: #0ea5e9; color: white; padding: 0.75rem 1.75rem; border-radius: 8px; text-decoration: none; font-weight: bold; transition: background 0.2s; }
                a:hover { background: #0284c7; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Email Verified!</h1>
                <p>Alhamdulillah, your email address has been verified successfully. You can now access your watchlist, portfolio, and detailed Shariah & AI prediction dashboards.</p>
                <a href="http://localhost:5500/login.html">Sign In to HalalEdge</a>
            </div>
        </body>
    </html>
    """)

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if not db_user or not verify_password(user_in.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # We will warn but not block logins on development, or let's allow it but warn them.
    # Actually, let's enforce email verification. If not verified, raise an HTTP 403.
    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first. A verification link has been sent to simulated_emails.log in the project root."
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"detail": "Logged out successfully"}

@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
def update_me(user_in: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    if user_in.country is not None:
        current_user.country = user_in.country
    if user_in.email is not None and user_in.email != current_user.email:
        # Check if email is already taken
        existing_user = db.query(User).filter(User.email == user_in.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already registered."
            )
        current_user.email = user_in.email
    if user_in.password is not None:
        current_user.password = get_password_hash(user_in.password)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    email_clean = email.lower().strip()
    db_user = db.query(User).filter(User.email == email_clean).first()
    if db_user:
        reset_token = secrets.token_urlsafe(32)
        db_user.reset_token = reset_token
        db.commit()
        
        reset_link = f"http://localhost:5500/reset-password.html?token={reset_token}"
        email_body = f"""Hello {db_user.full_name},

You have requested a password reset for your HalalEdge account. 

Please click the link below to set a new password:

{reset_link}

(Alternatively, copy-paste the URL into your browser)

If you did not request this, you can safely ignore this email.

Regards,
The HalalEdge Team
"""
        send_simulated_email(db_user.email, "Reset your HalalEdge Password", email_body)
        
    return {"detail": "If an account exists with that email, a password reset link has been sent. Please check simulated_emails.log."}

@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.reset_token == token).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )
    
    db_user.password = get_password_hash(new_password)
    db_user.reset_token = None
    db.commit()
    return {"detail": "Password has been reset successfully."}

