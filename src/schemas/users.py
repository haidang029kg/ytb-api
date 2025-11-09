from pydantic import BaseModel, EmailStr


class UserCreateReq(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str


class LoginReq(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenReq(BaseModel):
    refresh_token: str


class TokenRenew(BaseModel):
    access_token: str
    token_type: str
