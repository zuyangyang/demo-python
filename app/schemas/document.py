from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DocumentBase(BaseModel):
    """Base document schema with common fields."""
    title: str = Field(..., min_length=1, max_length=256)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Title cannot be empty or whitespace only')
        return v


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    deleted: Optional[bool] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return v


class DocumentOut(DocumentBase):
    """Schema for document output."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    owner_id: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Schema for document list response with pagination."""
    items: list[DocumentOut]
    page: int
    page_size: int
    total: int
