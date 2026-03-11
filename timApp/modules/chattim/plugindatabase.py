from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from models import User, Instance, StudentPolicy, GlobalPolicy, APIKey


class PluginDatabase:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, id: int, role: str) -> User:
        user = User(id=id, role=role)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def get_user(self, tim_id: str) -> User | None:
        stmt = select(User).where(User.tim_id == tim_id)
        return self.db.scalar(stmt)

    def get_or_create_user(self, tim_id: str, role: str) -> User:
        user = self.get_user(tim_id)
        if user:
            return user

        user = User(tim_id=tim_id, role=role)
        self.db.add(user)
        try:
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError:
            self.db.rollback()
            user = self.get_user(tim_id)
        return user

    def create_instance(
        self, teacher_id: int, document_id: int, gp: GlobalPolicy
    ) -> Instance:
        self.db.add(gp)
        self.db.flush()

        instance = Instance(
            teacher_id=teacher_id, document_id=document_id, global_policy_id=gp.id
        )

        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)

        return instance

    def get_instance(self, document_id: str) -> Instance | None:
        stmt = select(Instance).where(Instance.document_id == document_id)

        return self.db.scalar(stmt)

    def delete_instance(self, document_id: str):
        stmt = delete(Instance).where(Instance.document_id == document_id)

        self.db.execute(stmt)
        self.db.commit()

    def set_student_policy(
        self, instance_id: int, student_id: int, policy: StudentPolicy
    ) -> StudentPolicy:
        policy.instance_id = instance_id
        policy.student_id = student_id

        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)

        return policy

    def create_api_key(
        self, user_id: int, key: str, instance_id: int, description: str
    ) -> APIKey:
        apikey = APIKey(
            user_id=user_id, key=key, instance_id=instance_id, description=description
        )

        self.db.add(apikey)
        self.db.commit()
        self.db.refresh(apikey)

        return apikey
