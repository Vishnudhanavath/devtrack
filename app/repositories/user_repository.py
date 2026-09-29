from sqlalchemy import select
from sqlalchemy.orm import Session 


from app.models.user import User 


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    #repository rememebers this database section 

    def create_user(self, user: User) -> User: 
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user) 

        return user 


    def get_all(self) -> list[User]:
        statement = select(User)

        # trying to tell the sqlalchemy to the database
        result = self.db.scalars(statement)

        return result.all() # returns the list 

    
    def get_by_id(self,user_id:int) -> User| None:
        statement = select(User).where(User.id == user_id)

        return self.db.scalars(statement).first()

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)

        return self.db.scalars(statement).first()




    

