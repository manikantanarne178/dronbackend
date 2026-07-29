from app.models.rule_config import RuleConfig


DEFAULT_RULES = [
    ("setback", "min_front", "3", "Minimum front setback"),
    ("setback", "min_rear", "2", "Minimum rear setback"),
    ("setback", "min_side", "1.5", "Minimum side setback"),
    ("height", "max_height", "15", "Maximum building height"),
    ("coverage", "max_coverage", "70", "Maximum plot coverage"),
    ("fsi", "max_fsi", "2.5", "Maximum Floor Space Index"),
]


def seed_rules(db):
    for rule_name, parameter, value, description in DEFAULT_RULES:

        exists = (
            db.query(RuleConfig)
            .filter(
                RuleConfig.rule_name == rule_name,
                RuleConfig.parameter == parameter,
            )
            .first()
        )

        if not exists:
            db.add(
                RuleConfig(
                    rule_name=rule_name,
                    parameter=parameter,
                    value=value,
                    description=description,
                )
            )

    db.commit()