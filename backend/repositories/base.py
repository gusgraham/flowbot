from typing import Generic, TypeVar, Type, List, Optional
from sqlmodel import Session, select, SQLModel

T = TypeVar("T", bound=SQLModel)

class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get(self, id: int) -> Optional[T]:
        return self.session.get(self.model, id)

    def list(self, offset: int = 0, limit: int = 100) -> List[T]:
        statement = select(self.model).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def create(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def update(self, id: int, obj_in: SQLModel) -> Optional[T]:
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        obj_data = obj_in.dict(exclude_unset=True)
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
            
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        db_obj = self.get(id)
        if not db_obj:
            return False
        
        self.session.delete(db_obj)
        self.session.commit()
        return True
