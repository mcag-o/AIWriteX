from __future__ import annotations

from pathlib import Path

import yaml

from content_hub.bootstrap.settings import HubSettings


class ConfigService:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def load_legacy_settings(self) -> HubSettings:
        config_path = self.project_root / "src" / "ai_write_x" / "config" / "config.yaml"
        config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return HubSettings.from_legacy_config(config_data, self.project_root)

    def save_hub_settings(self, settings: HubSettings, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            yaml.safe_dump(settings.to_dict(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return output_path
