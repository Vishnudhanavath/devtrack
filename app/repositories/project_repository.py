from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project 



class ProjectRepository:

    def __init__(self, db:Session):
        self.db = db 

    def create(self,project: Project) -> Project:

        try:
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            return project 

        except Exception:
            self.db.rollback()
            raise 

    # get the project by project id 
    def get_by_id(
            self,
            project_id:int,
    )-> Project | None:
        statement = select(Project).where(
            Project.id == project_id 
        )
        return self.db.scalars(statement).first() 


    # GET PROJECTS WITH THE PROJECT OWNERS 
    def get_by_owner(self,owner_id:int,) -> list[Project]:
        statement = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
        ) 

        return self.db.scalars(statement).all() 


    #get all projects 
    def get_all(self) -> list[Project]:
        statement = (
            select(Project)
            .order_by(Project.created_at.desc())
        )
        return self.db.scalars(statement).all() 
    

    #updates the project 
    def update(self, project: Project) -> Project:

        try:
            self.db.commit()
            self.db.refresh(project)
            return project
        except Exception:
            self.db.rollback()
            raise
    # deletes the project 
    def delete(self, project: Project) -> None:

        try:
            self.db.delete(project)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    


# --------------- explanation ----------------------

# The repository answers questions like:

# "Give me project 10."

# "Give me projects owned by user 5."

# "Save this project."

# It should not decide:

# "Is this user allowed to delete project 10?"

# That's application/business logic. -> services 