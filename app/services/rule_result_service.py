import json
from pathlib import Path


class RuleResultService:

    @staticmethod
    def save(project_path: Path, rules):

        project_path = Path(project_path)
        project_path.mkdir(parents=True, exist_ok=True)

        rules_file = project_path / "rules.json"

        overall_status = "PASS"

        for rule in rules:
            if rule.get("status", "").upper() == "FAIL":
                overall_status = "FAIL"
                break

        data = {
            "overall_status": overall_status,
            "rules": rules
        }

        with open(rules_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return rules_file

    @staticmethod
    def load(project_path: Path):

        rules_file = Path(project_path) / "rules.json"

        if not rules_file.exists():
            return {
                "overall_status": "UNKNOWN",
                "rules": []
            }

        with open(rules_file, "r", encoding="utf-8") as f:
            return json.load(f)