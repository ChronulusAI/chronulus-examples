from pydantic import BaseModel, Field


class RequestInfo(BaseModel):
    request_id: str
    timestamp: float


class SportsWinProb(RequestInfo):
    side1: str
    side2: str
    reverse_order: bool = Field(default=False)


class VCRegret(RequestInfo):
    company_name: str
