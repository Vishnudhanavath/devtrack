from pydantic import BaseModel, Field
from typing import Literal

class ProjectMemeberCreate(BaseModel):
    user_id: int
    role: Literal["manager","member"]="member"






from pydantic import BaseModel, ConfigDict
from typing import Literal

from app.models.project_member import ProjectRole


class ProjectMemberCreate(BaseModel):
    user_id: int
    role: Literal["manager", "member"] = "member"


class ProjectMemberUpdate(BaseModel):
    role: Literal["manager", "member"]


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    user_id: int
    role: ProjectRole


