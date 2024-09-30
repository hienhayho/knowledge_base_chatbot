from fastapi import HTTPException
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from .models import Base, User, KnowledgeBase, Document, DocumentChunk, Assistant, Conversation, Message, DocumentStatus
from .vector_store import VectorDB, QdrantVectorDB
from datetime import datetime
import uuid 

# Database manager class
class DatabaseManager:
    def __init__(self, db_path, vector_db: VectorDB):
        self.engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.vector_db = vector_db

    ## User methods
    def create_user(self, username, email, password_hash):
        with self.Session() as session:
            user = User(username=username, email=email, password_hash=password_hash)
            session.add(user)
            session.commit()
            return user.id

    def find_user(self, identifier):
        with self.Session() as session:
            user = session.query(User).filter(
                or_(User.username == identifier, User.email == identifier)
            ).first()
            return user

    def get_current_user_id(self):
        return 1  # Placeholder implementation

    ## Knowledge Base methods
    def create_knowledge_base(self, user_id, name, description):
        with self.Session() as session:
            kb = KnowledgeBase(user_id=user_id, name=name, description=description)
            session.add(kb)
            session.commit()
            self.vector_db.create_collection(f"kb_{kb.id}")
            return kb.id

    def get_knowledge_base(self, knowledge_base_id: int, user_id: int):
        with self.Session() as session:
            kb = session.query(KnowledgeBase).filter_by(id=knowledge_base_id, user_id=user_id).first()
            if not kb:
                raise HTTPException(status_code=404, detail="Knowledge base not found or access denied")
            return kb

    def find_knowledge_base(self, knowledge_base_name: str, user_id: int):
        with self.Session() as session:
            kb = session.query(KnowledgeBase).filter_by(name=knowledge_base_name, user_id=user_id).first()
            return kb


    ## Document and DocumentChunk methods
    def add_document(self, knowledge_base_id, file_name, file_type, file_path, status=DocumentStatus.UPLOADED):
        with self.Session() as session:
            doc = Document(knowledge_base_id=knowledge_base_id, file_name=file_name,
                           file_type=file_type, file_path=file_path, status=status)
            session.add(doc)
            session.commit()
            return doc.id, doc.file_type, doc.created_at

    def add_document_chunk(self, document_id, chunk_index, content, vector, metadata = None):
        vector_id = str(uuid.uuid4())
        with self.Session() as session:
            document = session.query(Document).filter_by(id=document_id).first()
            if not document:
                raise ValueError("Document not found")
            
            knowledge_base_id = document.knowledge_base_id
            
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk_index,
                content=content, 
                vector_id=vector_id
            )
            session.add(chunk)
            session.commit()
            
            self.vector_db.add_vector(
                collection_name=f"kb_{knowledge_base_id}",
                vector_id=vector_id,
                vector=vector,
                payload={
                    "document_chunk_id": chunk.id,
                    "text": content,
                    "metadata": metadata
                }
            )
            return chunk.id

    def update_document_status(self, document_id: int, status: DocumentStatus):
        with self.Session() as session:
            document = session.query(Document).filter_by(id=document_id).first()
            if not document:
                raise ValueError("Document not found")
            document.status = status
            document.updated_at = datetime.utcnow()
            session.commit()

    def get_document(self, document_id: int):
        with self.Session() as session:
            document = session.query(Document).filter_by(id=document_id).first()
            return document

    def get_document_by_name(self, knowledge_base_id: int, file_name: str):
        with self.Session() as session:
            document = session.query(Document).filter_by(
                knowledge_base_id=knowledge_base_id,
                file_name=file_name
            ).first()
            return document
        
    def delete_document(self, document_id: int):
        with self.Session() as session:
            document = session.query(Document).filter_by(id=document_id).first()
            if not document:
                return False
            # Delete the document chunks
            session.query(DocumentChunk).filter_by(document_id=document_id).delete()
            # Delete the document
            session.delete(document)
            session.commit()
            return True

    def search_similar_chunks(self, query_vector, knowledge_base_id, limit=5):
        search_result = self.vector_db.search_vectors(
            collection_name=f"kb_{knowledge_base_id}",
            query_vector=query_vector,
            limit=limit
        )
        return [(hit.payload["document_chunk_id"], hit.payload["content"]) for hit in search_result]

    def get_document_task_id(self, document_id: int):
        with self.Session() as session:
            document = session.query(Document).filter_by(id=document_id).first()
            return document.task_id if document else None

    def set_document_task_id(self, document_id: int, task_id: str):
        with self.Session() as session:
            document = session.query(Document).filter_by(id=document_id).first()
            if document:
                document.task_id = task_id
                session.commit()

    ## Assistant and Conversation methods
    def create_assistant(self, user_id, name, description, systemprompt, knowledge_base_id, configuration):
        with self.Session() as session:
            assistant = Assistant(user_id=user_id, name=name, description=description, systemprompt=systemprompt,
                                  knowledge_base_id=knowledge_base_id, configuration=configuration)
            session.add(assistant)
            session.commit()
            return assistant
        
    def delete_assistant(self, assistant_id, user_id):
        with self.Session() as session:
            assistant = session.query(Assistant).filter_by(id=assistant_id, user_id=user_id).first()
            if not assistant:
                return False
            # Delete the messages associated with the conversation
            session.query(Message).filter_by(conversation_id=assistant_id).delete()
            
            # Delete the conversation
            session.query(Conversation).filter_by(assistant_id=assistant_id).delete()
            
            # Delete the assistant
            session.delete(assistant)
            session.commit()
            return True

    def start_conversation(self, user_id, assistant_id):
        with self.Session() as session:
            conv = Conversation(user_id=user_id, assistant_id=assistant_id)
            session.add(conv)
            session.commit()
            return conv.id

    def add_message(self, conversation_id, sender_type, content):
        with self.Session() as session:
            message = Message(conversation_id=conversation_id, sender_type=sender_type, content=content)
            session.add(message)
            session.commit()
            return message.id    


# Usage example
if __name__ == "__main__":
    
    vector_db = QdrantVectorDB("http://localhost:6333")
    db_manager = DatabaseManager("/home/bachngo/Desktop/code/Knowledge_Base_Agent/backend/DB/knowledge_base.db", vector_db)
    
    # Create a user
    user_id = db_manager.create_user("admin", "admin@example.com", "123")
    
    # Create a knowledge base
    kb_id = db_manager.create_knowledge_base(user_id, "General Knowledge", "A broad knowledge base")
    
    # Add a document
    # doc_id = db_manager.add_document(kb_id, "sample.txt", "text/plain", "/path/to/sample.txt")
    
    # Add a document chunk (you'd typically do this after processing the document)
    # chunk_id = db_manager.add_document_chunk(doc_id, 0, "This is a sample text", [0.1, 0.2, 0.3, 0.4])  # Simplified vector
    
    # Create an assistant
    # assistant_id = db_manager.create_assistant(user_id, "General Assistant", "A helpful AI assistant",
    #                                            kb_id, {"model": "gpt-3.5-turbo"})
    
    # # Start a conversation
    # conv_id = db_manager.start_conversation(user_id, assistant_id)
    
    # # Add messages to the conversation
    # db_manager.add_message(conv_id, "user", "Hello, can you help me?")
    # db_manager.add_message(conv_id, "assistant", "Of course! How can I assist you today?")
    
    # # Search for similar chunks (you'd typically do this when processing a user query)
    # similar_chunks = db_manager.search_similar_chunks([0.15, 0.25, 0.35, 0.45], kb_id)  # Simplified query vector
    # print("Similar chunks:", similar_chunks)