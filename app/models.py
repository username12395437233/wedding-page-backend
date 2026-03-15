from typing import Optional

from pydantic import BaseModel, Field


class AlcoholModel(BaseModel):
    whiteWine: bool = False
    redWine: bool = False
    champagne: bool = False
    beer: bool = False
    whiskey: bool = False
    tinctures: bool = False


class SubmitRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    allergy: Optional[str] = Field(default="", max_length=1000)
    alcohol: AlcoholModel


class SubmitResponse(BaseModel):
    ok: bool
    id: int
    message: str