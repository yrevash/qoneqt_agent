import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User
from app.modules.recsys.service import recsys_service
from pydantic import BaseModel, Optional, Any, Field 
import datetime
from api.core import Router

class TimerScheduling(BaseModel):
    initiator_name: str = Field(..., description="Name of the user to get recommendations for")


async def scheduling_user_recommendations(initiator_name :str):
    print(f"\nScheduling recommendations for: '{initiator_name}'")
    
    return 
    