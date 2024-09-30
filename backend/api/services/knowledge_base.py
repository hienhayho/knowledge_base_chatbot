from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from src.database.manager import DatabaseManager
from api.models.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from src.database.models import KnowledgeBase
from src.dependencies import get_db_manager

class KnowledgeBaseService:
    def __init__(self, db_manager: DatabaseManager = Depends(get_db_manager)):
        self.db_manager = db_manager

    def create_knowledge_base(self, user_id: int, kb: KnowledgeBaseCreate) -> KnowledgeBaseResponse:
        with self.db_manager.Session() as session:
            new_kb = KnowledgeBase(user_id=user_id, name=kb.name, description=kb.description)
            session.add(new_kb)
            session.commit()
            session.refresh(new_kb)
            return KnowledgeBaseResponse.model_validate(new_kb)

    def get_knowledge_base(self, kb_id: int, user_id: int) -> KnowledgeBaseResponse:
        with self.db_manager.Session() as session:
            kb = session.query(KnowledgeBase).options(joinedload(KnowledgeBase.documents)).filter_by(id=kb_id, user_id=user_id).first()
            if kb:
                return KnowledgeBaseResponse.model_validate(kb)
            return None

    def list_knowledge_bases(self, user_id: int) -> list[KnowledgeBaseResponse]:
        with self.db_manager.Session() as session:
            kbs = session.query(KnowledgeBase).filter_by(user_id=user_id).all()
            return [KnowledgeBaseResponse.model_validate(kb) for kb in kbs]

    def update_knowledge_base(self, kb_id: int, user_id: int, kb_update: KnowledgeBaseUpdate) -> KnowledgeBaseResponse:
        with self.db_manager.Session() as session:
            kb = session.query(KnowledgeBase).filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                raise HTTPException(status_code=404, detail="Knowledge base not found")
            
            for key, value in kb_update.model_dump(exclude_unset=True).items():
                setattr(kb, key, value)
            
            session.commit()
            session.refresh(kb)
            return KnowledgeBaseResponse.model_validate(kb)

    def delete_knowledge_base(self, kb_id: int, user_id: int) -> bool:
        with self.db_manager.Session() as session:
            kb = session.query(KnowledgeBase).filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                return False
            session.delete(kb)
            session.commit()
            return True