from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from models.user import fake_decode_token

router = APIRouter(prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


@router.get('/items')
async def read_items(token: str = Depends(oauth2_scheme)):
    return {'token': token}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    return user