from pydantic import BaseModel, ConfigDict, Field 


class UserCreate(BaseModel):
    name: str 
    email: str 
    password: str = Field(
        min_length=8,
        max_length=128
    )



class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class UserPatch(BaseModel):
    name: str | None = None
    email: str | None = None




class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True) # return's as the object 
    id:int 
    name:str 
    email: str 


    
class UserListResponse(BaseModel):
    item: list[UserResponse]
    page:int
    page_size:int 
    total:int 
    total_pages:int 
    