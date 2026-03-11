from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tim_id: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)

    instances: Mapped[list["Instance"]] = relationship(
        "Instance", back_populates="teacher"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user"
    )
    apikeys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="teacher")
    student_policies: Mapped[list["StudentPolicy"]] = relationship(
        "StudentPolicy", back_populates="student"
    )
    student_usages: Mapped[list["StudentUsage"]] = relationship(
        "StudentUsage", back_populates="student"
    )


class Instance(Base):
    __tablename__ = "instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    current_mode: Mapped[str] = mapped_column(String, default="summary")
    global_policy_id: Mapped[int] = mapped_column(
        ForeignKey("global_policy.id"), nullable=False
    )
    total_tokens_spent: Mapped[int] = mapped_column(Integer, default=0)
    indexed_doc_ids: Mapped[int] = mapped_column(Integer, default=list)

    teacher: Mapped["User"] = relationship("User", back_populates="instances")
    student_policies: Mapped[list["StudentPolicy"]] = relationship(
        "StudentPolicy", back_populates="instance"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="instance"
    )
    apikeys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="instance")
    global_policy: Mapped["GlobalPolicy"] = relationship(
        "GlobalPolicy", back_populates="instance", uselist=False
    )


class APIKey(Base):
    __tablename__ = "apikeys"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    instance_id: Mapped[int] = mapped_column(ForeignKey("instances.id"))
    description: Mapped[str] = mapped_column(String)

    user: Mapped["User"] = relationship("teacher", back_populates="apikeys")
    instance: Mapped["Instance"] = relationship("Instance", back_populates="apikeys")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agent.id"))
    plugin_instance_id: Mapped[int] = mapped_column(
        ForeignKey("instances.id"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="conversations")
    instance: Mapped["Instance"] = relationship(
        "Instance", back_populates="conversations"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"), nullable=False
    )
    sender_type: Mapped[str] = mapped_column(String)
    content_reference: Mapped[int] = mapped_column(Integer)
    tokens: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )


class PolicyBase(Base):
    __abstract__ = True

    token_time_window_type: Mapped[str] = mapped_column(
        String(3), nullable=False
    )  # 'd','h','min','sec'
    token_time_window_num: Mapped[int] = mapped_column(Integer, nullable=False)
    time_window_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # token limit for this window
    max_tokens: Mapped[int] = mapped_column(Integer)


class StudentPolicy(PolicyBase):
    __tablename__ = "student_policy"

    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("instances.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    instance: Mapped["Instance"] = relationship(
        "Instance", back_populates="student_policies"
    )
    student: Mapped["User"] = relationship("student", back_populates="student_policies")


class GlobalPolicy(PolicyBase):
    __tablename__ = "global_policy"

    id: Mapped[int] = mapped_column(primary_key=True)
    instance: Mapped["Instance"] = relationship(
        "Instance", back_populates="global_policy", uselist=False
    )


class Agent(Base):
    __tablename__ = "agent"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    instances: Mapped[list["Instance"]] = relationship(
        "Instance", back_populates="agent"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="agent"
    )


class StudentUsage(Base):
    __tablename__ = "student_usage"

    instance_id: Mapped[int] = mapped_column(
        ForeignKey("instances.id"), primary_key=True
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    used_tokens: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    student: Mapped["User"] = relationship("student", back_populates="student_usages")
