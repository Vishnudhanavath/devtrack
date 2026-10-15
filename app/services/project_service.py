
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate,ProjectUpdate 
from sqlalchemy.orm import Session


class ProjectService: 

    def __init__(self, repository: ProjectRepository, db: Session):
        self.repository = repository
        self.db = db 


    # def create_project(
    #         self,
    #         project_data: ProjectCreate,
    #         owner_id:int,
    # ) -> Project:

    #     project = Project(
    #         name = project_data.name,
    #         description = project_data.description,
    #         owner_id = owner_id,
    #     )

    #     return self.repository.create_with_owner(project) 

    def create_project(
    self,
    project_data: ProjectCreate,
    owner_id: int,
    ) -> Project:
        project = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=owner_id,
        )

        try:
            # Stage the project and owner membership.
            project = self.repository.create_with_owner(project)

            # Commit both inserts as one database transaction.
            self.db.commit()

            # Refresh the project after the successful commit.
            self.db.refresh(project)

            return project

        except Exception:
            # Undo all uncommitted changes if anything fails.
            self.db.rollback()
            raise



    def get_project(
            self,
            project_id: int,
    )-> Project | None:
        
        return self.repository.get_by_id(project_id) 


    def get_my_projects(
            self,
            owner_id:int 
    ) -> list[Project]:

        return self.repository.get_by_owner(owner_id) 

    
    def update_project(
            self,
            project_id:int,
            project_data:ProjectUpdate,
            current_user_id:int, 
    ) -> Project|None :
        project = self.repository.get_by_id(project_id)

        if(project is None):
            return None 
        
        if project.owner_id != current_user_id:
            raise PermissionError(
                "You are not allowed to update this project"
            )

        project.name = project_data.name
        project.description = project_data.description

        try:
            project = self.repository.update(project)
            self.db.commit()
            self.db.refresh(project)
            return project
        except Exception:
            self.db.rollback()
            raise

    def delete_project(
        self,
        project_id: int,
        current_user_id: int,
    ) -> bool:
        project = self.repository.get_by_id(project_id)

        if project is None:
            return False

        if project.owner_id != current_user_id:
            raise PermissionError(
                "You are not allowed to delete this project"
            )

        try:
            self.repository.delete(project)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise True



    







