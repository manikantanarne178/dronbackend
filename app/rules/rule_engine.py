from sqlalchemy.orm import Session

from app.rules.plot import PlotRule
from app.rules.fsi import FSIRule
from app.rules.coverage import CoverageRule
from app.rules.setback import SetbackRule

from app.services.rule_config_service import RuleConfigService


class RuleEngine:

    @staticmethod
    def validate(plot, building, db: Session):

        config = RuleConfigService(db)

        rules = [
            PlotRule.check(plot),
            FSIRule.check(plot, building, config),
            CoverageRule.check(plot, building, config),
            SetbackRule.check(plot, building, config),
        ]

        passed = sum(1 for r in rules if r["status"] == "PASS")
        failed = sum(1 for r in rules if r["status"] == "FAIL")
        warning = sum(1 for r in rules if r["status"] == "WARNING")

        return {
            "summary": {
                "total": len(rules),
                "passed": passed,
                "failed": failed,
                "warning": warning
            },
            "rules": rules
        }