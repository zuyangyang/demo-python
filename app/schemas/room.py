from pydantic import BaseModel, Field


class RoomCreateRequest(BaseModel):
    room_id: str = Field(min_length=1)


class RoomResponse(BaseModel):
    room_id: str
    has_image: bool = False


