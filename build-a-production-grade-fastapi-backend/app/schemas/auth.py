from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    # SECURITY: self-registration ALWAYS creates a CLIENT account. Role escalation
    # to Admin/Consultant must be performed by an existing Admin via a dedicated
    # admin endpoint (not yet implemented). This field is intentionally omitted
    # from the public register payload.


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
