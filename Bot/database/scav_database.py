from sqlalchemy.orm import registry, relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean

mapper_registry = registry()
Base = mapper_registry.generate_base()

class Question(Base):
    __tablename__ = "scav_question"

    id = Column(Integer, primary_key=True)
    text = Column(String(100))
    answer = Column(String(30))
    file = Column(String(100))
    file_display_name = Column(String(100))
    hint = Column(String(100))
    hint_file = Column(String(100))
    hint_file_display_name = Column(String(100))
    enabled = Column(Boolean, default=True)
    weight = Column(Integer)
    identifier = Column(String(30))


class Team(Base):
    __tablename__ = "scav_team"

    id = Column(Integer, primary_key=True)
    role = Column(Integer)
    current_question = Column(Integer, ForeignKey('scav_question.id'))
    finished = Column(Boolean, default=False)

    