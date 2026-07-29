from sqlalchemy.orm import Session

from app.models.rule_config import RuleConfig


class RuleConfigService:

    def __init__(self, db: Session):
        self.db = db

    def get_value(self, rule_name: str, parameter: str):
        config = (
            self.db.query(RuleConfig)
            .filter(
                RuleConfig.rule_name == rule_name,
                RuleConfig.parameter == parameter,
            )
            .first()
        )

        if not config:
            raise Exception(
                f"Rule configuration not found: {rule_name}.{parameter}"
            )

        return float(config.value)

    def get_all(self):
        return self.db.query(RuleConfig).all()