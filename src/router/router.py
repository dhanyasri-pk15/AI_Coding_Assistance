from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.models import ChatRequest, ChatResponse
from src.database.database import get_db
from src.schema.schema import Customers, ErrorLogs
from src.service.service import GraphService
 
router = APIRouter()
graph_service = GraphService()
 
# 1.149 - 1.152 router endpoint definition
@router.post("/chat", response_model=ChatResponse)
# 1.153 - 1.178 perform pydantic validation to the request body
async def chat(request: ChatRequest,db: AsyncSession = Depends(get_db)):
    # 1.20 - 1.149 - router function chat(response building and pydantic validation)
    thread_id = request.thread_id
    message = request.message
    try:
        # Validate thread_id as UUID; if invalid, skip customer lookup.
        from uuid import UUID
        try:
            thread_uuid = UUID(thread_id)
        except Exception:
            thread_uuid = None

        if thread_uuid:
            result = await db.execute(
                select(Customers).where(Customers.customer_id == thread_uuid)
            )
            customer = result.scalar_one_or_none()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
        else:
            customer = None
 
        # Duplicate customer lookup removed
 
        # No customer validation needed when thread_id is not a UUID

        result = await graph_service.invoke(
            thread_id,
            message
        )

        print("Type :", type(result))
        if isinstance(result, dict):
            code = result.get("code")
            review_feedback = result.get("review_feedback")
            research_data = result.get("research_data")
            reply = "Execution completed"
        elif isinstance(result, ChatResponse):
            code = result.code
            review_feedback = result.review_feedback
            research_data = result.research_data
            reply = result.reply
        else:
            code = getattr(result, "code", None)
            review_feedback = getattr(result, "review_feedback", None)
            research_data = getattr(result, "research_data", None)
            reply = getattr(result, "reply", "Execution completed")

        return ChatResponse(
            thread_id=thread_id,
            reply=reply,
            code=code,
            review_feedback=review_feedback,
            research_data=research_data,
        )
 
    except Exception as e:

        print("CHAT ERROR:", str(e))
        error_log = ErrorLogs(file_name="router.py",function_name="chat",error_message=str(e))
 
        db.add(error_log)
        await db.commit()
 
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
 
 