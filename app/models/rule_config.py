from sqlalchemy import Column, Integer, String, Text

from app.models.base import Base


class RuleConfig(Base):
    __tablename__ = "rule_config"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    parameter = Column(String(100), nullable=False)
    value = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)