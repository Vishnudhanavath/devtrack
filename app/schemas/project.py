from pydantic import BaseModel,ConfigDict, Field 


# What client is allowed to send
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str|None = None 


class ProjectUpdate(BaseModel):
    name:str = Field(min_length=1, max_length=150)
    description: str |None = None 


#What API is allowed to return
class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int 
    name:str 
    description: str|None 
    owner_id:int 



