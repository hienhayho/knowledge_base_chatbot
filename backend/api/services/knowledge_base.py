from src.database import DatabaseManager
from src.utils import get_formatted_logger
from src.database.sql_model import Users, KnowledgeBases

logger = get_formatted_logger(__file__)


class KnowledgeBaseService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_knowledge_base(self, user: Users, name: str, description: str):
        """
        Create a new knowledge base for the user

        Args:
            user (Users): User object
            name (str): Knowledge base name
            description (str): Knowledge base description

        Returns:
            KnowledgeBases: Knowledge base object
        """
        logger.info("UserID: %s, Name: %s, Description: %s", user.id, name, description)

        knowledge_base = KnowledgeBases(name=name, description=description, user=user)
        self.db_manager.session.add(knowledge_base)
        self.db_manager.session.commit()

        return knowledge_base
