from sqlalchemy.orm import registry, relationship
from sqlalchemy import Column, ForeignKey, Integer, String

mapper_registry = registry()
Base = mapper_registry.generate_base()


class UserInvite(Base):
    __tablename__ = "auth_user_invite"

    id = Column(Integer, primary_key=True)
    invite_code = Column(String(10))
    nickname = Column(String(50))

    roles = relationship("UserInviteRole", back_populates="user_invite")

class UserInviteRole(Base):
    __tablename__ = "auth_user_invite_role"

    id = Column(Integer, primary_key=True)
    user_invite_id = Column(Integer, ForeignKey('auth_user_invite.id'))
    role = Column(Integer)

    user_invite = relationship("UserInvite", back_populates="roles")