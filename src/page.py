from pydantic import BaseModel, Field

class Page(BaseModel):
    page: int = Field(..., description='Current Page number starting from 1.')
    is_last_page: bool = Field(default=False, description='Flag to indicate if this is the last page or not')