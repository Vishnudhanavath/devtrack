from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.repositories.project_member_repository import (
    ProjectMemberRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.project_member import ProjectMemberCreate



class ProjectMemberService:

    def __init__(
        self,
        member_repository: ProjectMemberRepository,
        project_repository: ProjectRepository,
        user_repository: UserRepository,
    ):
        self.member_repository = member_repository
        self.project_repository = project_repository
        self.user_repository = user_repository


    def _get_project_or_raise(
        self,
        project_id: int,
    ) -> Project:

        project = self.project_repository.get_by_id(project_id)

        if project is None:
            raise LookupError("Project not found")

        return project


    def _require_owner(
        self,
        project: Project,
        current_user_id: int,
    ) -> None:

        if project.owner_id != current_user_id:
            raise PermissionError(
                "Only the project owner can manage membership"
            )


    #adding the memeber to the project 

    def add_member(
        self,
        project_id: int,
        member_data: ProjectMemberCreate,
        current_user_id: int,
    ) -> ProjectMember:

        project = self._get_project_or_raise(project_id)

        self._require_owner(project, current_user_id)

        user = self.user_repository.get_by_id(member_data.user_id)

        if user is None:
            raise LookupError("User not found")

        existing = self.member_repository.get_membership(
            project_id,
            member_data.user_id,
        )

        if existing is not None:
            raise ValueError("User is already a project member")
 
        membership = ProjectMember( # call the repository to add the member
            project_id=project_id,
            user_id=member_data.user_id,
            role=ProjectRole(member_data.role),
        )

        return self.member_repository.add(membership)



    #get the members of the project 
    def get_members(
            self,
            project_id:int,
            current_user_id:int, 
    ) -> list[ProjectMember]:
        project = self._get_project_or_raise(project_id)

        membership = self.member_repository.get_membership(
            project_id,
            current_user_id,
        )

        is_owner = project.owner_id == current_user_id

        if not is_owner and membership is None:
            raise PermissionError(
                "You are not a member of this project"
            )

        return self.member_repository.get_by_project(project_id)


    #update role of the member 
    def update_member_role(
        self,
        project_id: int,
        user_id: int,
        new_role: str,
        current_user_id: int,
    ) -> ProjectMember:

        project = self._get_project_or_raise(project_id)

        self._require_owner(project, current_user_id)

        membership = self.member_repository.get_membership(
            project_id,
            user_id,
        )

        if membership is None:
            raise LookupError("Project membership not found")

        membership.role = ProjectRole(new_role)

        return self.member_repository.update(membership)


    #delet the member 

    def remove_member(
        self,
        project_id: int,
        user_id: int,
        current_user_id: int,
    ) -> None:

        project = self._get_project_or_raise(project_id)

        self._require_owner(project, current_user_id)

        if user_id == project.owner_id:
            raise ValueError(
                "The project owner cannot be removed as a member"
            )

        membership = self.member_repository.get_membership(
            project_id,
            user_id,
        )

        if membership is None:
            raise LookupError("Project membership not found")

        self.member_repository.delete(membership)


        

    







