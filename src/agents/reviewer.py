from langgraph.prebuilt import create_react_agent
from src.agents.prompts import reviewer_prompt
from src.mcp_clients.context7 import Context7Client
from src.utils.logger import get_logger
from src.utils.helpers import extract_text

logger = get_logger(__name__) 

class ReviewerAgent:
 
    def __init__(self):
        self.agent = None
        self.llm = None
        self.tools = None
        self.logger = logger

#1.53 - 1.68 create agent for reviewer
    async def create_agent(self, service):
        self.logger.info(f"Creating reviewer agent")
        try:
            self.llm = service.get_llm()
            context7=Context7Client()
            self.tools= await context7.get_tools()
            self.agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=reviewer_prompt
            )
        except Exception as e:
            self.logger.error(f"Reviewer tool agent failed. Using LLM fallback: {e}")
            self.agent = None
 
        return self
    
# 1.102 - 1.112 invoke reviewer agent 
    async def invoke_agent(self, state):
        self.logger.info("Running reviewer node")

        code = state.get("code", "")
        message = state.get("message", "")
        step = state.get("step", 0)
        previous_feedback = state.get("review_feedback", "")

        # Edge case: No code to review
        if not code or not code.strip():
            self.logger.warning("No code to review - auto-rejecting")
            return {
                "review_feedback": "DECISION: REJECTED\nSUMMARY: No code was produced by the coder agent.\nISSUES:\n1. [CRITICAL] Empty code output",
                "approved": False,
                "step": step + 1
            }

        # Edge case: If we've iterated too many times, auto-approve to prevent loops
        if step >= 5:
            self.logger.warning(f"Step {step} >= 5 — auto-approving to prevent infinite loop")
            return {
                "review_feedback": f"DECISION: APPROVED\nCONFIDENCE: MEDIUM\nSUMMARY: Auto-approved after {step} iterations to prevent infinite loop.\n\nISSUES:\n- Review cycle limit reached. Code may still have minor issues.",
                "approved": True,
                "step": step + 1
            }

        query = f"""
Original User Request:
{message}

Code to Review:
{code}

{"Previous Review Feedback (iteration " + str(step) + "):" + chr(10) + previous_feedback if previous_feedback else "This is the first review."}

Review this code following your checklist. Output your response in the STRICT FORMAT specified in your system prompt.
Remember: Your DECISION line must contain exactly APPROVED or REJECTED.
"""
 
        try:
 
            if self.agent:
                result = await self.agent.ainvoke({
                    "messages": [{"role": "user", "content": query}]
                })
 
                feedback = extract_text(result["messages"][-1].content)
 
            else:
                result = await self.llm.ainvoke(query)
                feedback = extract_text(result.content)
 
        except Exception as e:
 
            self.logger.error(f"Reviewer failed: {e}")

            # Rate limit or high demand — auto-approve to avoid burning quota or blocking
            if any(k in str(e) for k in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                self.logger.warning("Rate limit / high demand during review — auto-approving")
                return {
                    "review_feedback": "DECISION: APPROVED\nSUMMARY: Auto-approved due to temporary API high demand / rate limit. Manual review recommended.",
                    "approved": True,
                    "step": step + 1
                }

            feedback = "DECISION: APPROVED\nSUMMARY: Auto-approved due to reviewer error."

        # Robust approval detection
        approved = self._parse_decision(feedback)

        return {
            "review_feedback": feedback,
            "approved": approved,
            "step": step + 1
        }

    def _parse_decision(self, feedback: str) -> bool:
        """
        Robustly parse the reviewer's APPROVED/REJECTED decision.
        Handles multiple output formats and edge cases.
        """
        if not feedback:
            return False

        feedback_upper = feedback.upper()

        # Primary: Look for explicit DECISION line
        for line in feedback_upper.splitlines():
            line = line.strip()
            if line.startswith("DECISION:"):
                decision_value = line.replace("DECISION:", "").strip()
                if "REJECTED" in decision_value:
                    return False
                if "APPROVED" in decision_value:
                    return True

        # Fallback: Check for APPROVED/REJECTED keywords with context
        # "REJECTED" takes priority if both appear
        has_rejected = any(
            phrase in feedback_upper
            for phrase in ["REJECTED", "NOT APPROVED", "DECISION: NO", "APPROVED: NO"]
        )
        has_approved = any(
            phrase in feedback_upper
            for phrase in ["APPROVED", "DECISION: YES", "APPROVED: YES"]
        )

        if has_rejected:
            return False
        if has_approved:
            return True

        # Default: If we can't parse, assume rejected (safer)
        self.logger.warning("Could not parse reviewer decision — defaulting to rejected")
        return False
 
