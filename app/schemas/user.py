from pydantic import BaseModel, ConfigDict 


class UserCreate(BaseModel):
    name: str 
    email: str 



class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class UserPatch(BaseModel):
    name: str | None = None
    email: str | None = None




class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int 
    name:str 
    email: str 

    
class UserListResponse(BaseModel):
    item: list[UserResponse]
    page:int
    page_size:int 
    total:int 
    total_pages:int 
    