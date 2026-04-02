from pathlib import Path
import tempfile
import unittest

from content_hub.bootstrap.settings import HubSettings


class HubSettingsTestCase(unittest.TestCase):
    def test_loads_settings_from_yaml_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.yaml"
            config_path.write_text(
                """
llm:
  provider: OpenRouter
  model: openrouter/test-model
workflow:
  publish_platform: wechat
  article_format: markdown
rewrite:
  enabled: true
template:
  root_dir: knowledge/templates
storage:
  root_dir: output
publish:
  wechat_credentials:
    - appid: demo-app
      appsecret: demo-secret
      author: demo-author
""".strip(),
                encoding="utf-8",
            )

            settings = HubSettings.load(config_path)

            self.assertEqual(settings.llm.provider, "OpenRouter")
            self.assertEqual(settings.llm.model, "openrouter/test-model")
            self.assertEqual(settings.workflow.publish_platform, "wechat")
            self.assertEqual(settings.template.root_dir.as_posix(), "knowledge/templates")
            self.assertEqual(settings.publish.wechat_credentials[0].author, "demo-author")


if __name__ == "__main__":
    unittest.main()
