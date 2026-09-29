from pydantic import BaseModel 


class UserCreate(BaseModel):
    name: str 
    email: str 



class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int 
    name:str 
    email: str 

    