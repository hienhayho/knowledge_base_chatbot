from functools import lru_cache
from fastapi import Depends
from src.database.manager import DatabaseManager, QdrantVectorDB
from src.constants import GlobalConfig
import logging

def initialize_database(db_manager: DatabaseManager):
    # Check if admin user exists
    admin_user = db_manager.find_user("admin")
    
    if not admin_user:
        # Create admin user
        user_id = db_manager.create_user("admin", "admin@example.com", "123")
        logging.info("Admin user created.")
    else:
        user_id = admin_user.id

    # Check if default knowledge base exists
    default_kb = db_manager.find_knowledge_base("Default", user_id)
    if not default_kb:
        # Create default knowledge base
        db_manager.create_knowledge_base(user_id, "Default", "Default knowledge base")
        logging.info("Default knowledge base created.")

def get_database_manager() -> DatabaseManager:
    # You could load these configurations from environment variables or a config file
    vector_db = QdrantVectorDB("http://localhost:6333")
    db_manager = DatabaseManager(GlobalConfig.DATABASE_PATH, vector_db)
    
    # Create a user
    initialize_database(db_manager)
    
    return db_manager

@lru_cache()
def get_cache_db_manager() -> DatabaseManager:
    return get_database_manager()

def get_db_manager():
    db_manager = get_cache_db_manager()
    try:
        yield db_manager
    finally:
        # If DatabaseManager needs any cleanup, do it here
        pass
    
def get_current_user_id(db_manager: DatabaseManager = Depends(get_db_manager)):
    return db_manager.get_current_user_id()