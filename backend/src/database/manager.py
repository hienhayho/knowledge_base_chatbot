from .minio import MinioClient
from .sql_model import Users, init_db
from .validators import validate_email
from sqlmodel import Session, select, or_
from .vector_database import BaseVectorDatabase


class DatabaseManager:
    def __init__(
        self,
        sql_url: str,
        minioClient: MinioClient,
        vector_db: BaseVectorDatabase,
    ):
        engine = init_db(sql_url)
        self.session = Session(engine)
        self.minioClient = minioClient
        self.vector_db = vector_db

    def create_user(self, username: str, email: str, hashed_password: str):
        """
        Create a new user

        Args:
            username (str): Username
            email (str): Email address
            hashed_password (str): Hashed password

        Returns:
            uuid: User ID
        """
        if not validate_email(email):
            raise ValueError("Invalid email address")

        with self.session as session:
            query = select(Users).where(
                or_(Users.username == username, Users.email == email)
            )
            user = session.exec(query).first()

            if user:
                raise Exception("User already exists")

            user = Users(
                username=username, email=email, hashed_password=hashed_password
            )

            session.add(user)
            session.commit()

            return user.id

    def get_user(self, username: str):
        with self.session as session:
            query = select(Users).where(Users.username == username)
            user = session.exec(query).first()

            return user
