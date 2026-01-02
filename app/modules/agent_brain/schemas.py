from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal

class AgentDecision(BaseModel):
    """
    Structured output from the Agent's Brain.
    """
    decision: Literal["ACCEPT", "REJECT", "HOLD"] = Field(
        ..., 
        description="The binary decision on whether to engage with this candidate."
    )
    confidence_score: float = Field(
        ..., 
        description="A score between 0.0 and 1.0 indicating how confident the agent is."
    )
    reasoning: str = Field(
        ..., 
        description="A concise explanation of why this decision was made, referencing specific skills or bio details."
    )
    generated_message: Optional[str] = Field(
        None, 
        description="If ACCEPT, this contains the icebreaker message to send. If REJECT, this is null."
    )

    @validator("confidence_score")
    def check_score(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v