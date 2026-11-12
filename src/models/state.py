from typing import TypedDict, Optional
 
 
class AgentState(TypedDict):
    thread_id: str
    message: str
 
    # router classification
    intent: str
 
    # agent outputs
    code: Optional[str]
    review_feedback: Optional[str]
    research_data: Optional[str]
 
    # reviewer decision
    approved: Optional[bool]
 
    # graph step
    step: int
 
 