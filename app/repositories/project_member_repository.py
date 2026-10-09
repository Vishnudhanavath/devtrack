from sqlalchemy import select 
from sqlalchemy.orm import Session 

from app.models.project_member import ProjectMember


class  ProjectMemberRepository:

    def __init__(self,db:Session):
        self.db = db 


    
    def get_membership(
            self,
            project_id:int,
            user_id:int,
    ) -> ProjectMember | None:
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )

        return self.db.scalars(statement).first()



    # ------ get by project id ---------------

    def get_by_project(
            self,
            project_id:int,
    ) -> list[ProjectMember]:

        statement = (select(ProjectMember)
                    .where(ProjectMember.project_id == project_id)
                    .order_by(ProjectMember.id)

            )
        return self.db.scalars(statement).all() 


    #add project members 
    def add(
        self,
        membership: ProjectMember,
    ) -> ProjectMember:

        try:
            self.db.add(membership)
            self.db.commit()
            self.db.refresh(membership)
            return membership
        except Exception:
            self.db.rollback()
            raise


    #UPDATE  membership 

    def update(
            self,
            membership: ProjectMember
    ) -> ProjectMember:

        try:
            self.db.commit()
            self.db.refresh(membership)
            return membership

        except Exception:
            self.db.rollback()
            raise 


    def delete(
        self,
        membership: ProjectMember,
    ) -> None:

        try:
            self.db.delete(membership)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    

    
        








