import unittest
from src.research.integrations.nexus_local import prepare_html
class InstalledLocalHelperTests(unittest.TestCase):
    def test_pinned_html_projection_offline(self):
        out=prepare_html(b'<html><title>Fixture</title><body><p>Visible evidence.</p><script>secret hidden</script></body></html>')
        text=out['projection']['document']['visible_text']
        self.assertIn('Visible evidence.',text);self.assertNotIn('secret hidden',text);self.assertEqual(out['upstream_version'],'1.42.0')
