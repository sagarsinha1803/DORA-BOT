from fastapi import APIRouter, Query, status, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from .service import APIServices
from ..auth.service import CurrentUser
from ..database.core import DBSession


router = APIRouter(
    prefix='/agent',
    tags=['Agent']
)

@router.get("/chat_stream/{message}")
async def chat_stream(db: DBSession, curruser: CurrentUser, message: str, checkpoint_id: Optional[str] = Query(None)):
    try:
        APIServices.get_user_by_id(db, curruser.get_uuid())
        return StreamingResponse(
            APIServices.generate_chat_response(message, checkpoint_id),
            media_type="text/event-stream"
        )
    except Exception as ex:
        return None