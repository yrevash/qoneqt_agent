from pydantic import BaseMoodl ,Field, Any,List , Dict 


class LoadRequests(BaseModel):
    request_id = Field(List, description="Unique request identifier")
    payload: Any = Field(Dict ,description="Payload data for processing")
    timestamp: str = Field(str, description="Timestamp of the request")
    
    
    