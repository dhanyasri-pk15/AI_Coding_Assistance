from pydantic import BaseModel
from typing import Optional
 
class ChatRequest(BaseModel):
    thread_id: str
    message: str
    
class ChatResponse(BaseModel):
    thread_id: str
    reply: str
    code: Optional[str] = None
    review_feedback: Optional[str] = None
    research_data: Optional[str] = None
 