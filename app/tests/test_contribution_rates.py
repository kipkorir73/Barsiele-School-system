import os
import tempfile
import unittest
from pathlib import Path

from app.core import config


class ContributionRateUpdateTests(unittest.TestCase):
    def setUp(self):
        self._original_rates = dict(config.DEFAULT_RATES)
        self._original_env = {
            key: os.environ.get(key)
            for key in ('RATE_MAIZE', 'RATE_MILLET', 'RATE_BEANS')
        }

    def tearDown(self):
        config.DEFAULT_RATES.clear()
        config.DEFAULT_RATES.update(self._original_rates)
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_update_applies_rates_immediately_for_shared_importers(self):
        """Payment recording imports DEFAULT_RATES; Save must mutate that dict in place."""
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / '.env'
            env_path.write_text(
                "RATE_MAIZE=30.0\nRATE_MILLET=40.0\nRATE_BEANS=25.0\n",
                encoding='utf-8',
            )
            config.DEFAULT_RATES.update({'maize': 30.0, 'millet': 40.0, 'beans': 25.0})

            # Simulate payment_tab holding a reference to the shared dict.
            live_rates = config.DEFAULT_RATES

            config.update_contribution_rates(
                {'maize': 50.0, 'millet': 60.0, 'beans': 70.0},
                env_path=env_path,
            )

            self.assertEqual(live_rates['maize'], 50.0)
            self.assertEqual(live_rates['millet'], 60.0)
            self.assertEqual(live_rates['beans'], 70.0)
            # Concrete contribution math that would have stayed at 30*100=3000 before the fix.
            self.assertEqual(100 * live_rates['maize'], 5000.0)

    def test_update_upserts_env_without_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / '.env'
            env_path.write_text(
                "DB_TYPE=sqlite\n"
                "RATE_MAIZE=30.0\n"
                "RATE_MILLET=40.0\n"
                "RATE_BEANS=25.0\n"
                "RATE_MAIZE=100.0\n"
                "SECRET_KEY=test\n",
                encoding='utf-8',
            )

            config.update_contribution_rates(
                {'maize': 55.0, 'millet': 65.0, 'beans': 75.0},
                env_path=env_path,
            )

            text = env_path.read_text(encoding='utf-8')
            self.assertEqual(text.count('RATE_MAIZE='), 1)
            self.assertEqual(text.count('RATE_MILLET='), 1)
            self.assertEqual(text.count('RATE_BEANS='), 1)
            self.assertIn('RATE_MAIZE=55.0', text)
            self.assertIn('RATE_MILLET=65.0', text)
            self.assertIn('RATE_BEANS=75.0', text)
            self.assertIn('DB_TYPE=sqlite', text)
            self.assertIn('SECRET_KEY=test', text)
            self.assertEqual(os.environ['RATE_MAIZE'], '55.0')

    def test_settings_save_rates_uses_update_helper(self):
        """Guard the UI path so it cannot regress to append-only .env writes.

        Avoid importing the desktop package (PyQt/libEGL unavailable in CI images).
        """
        import ast

        source = Path('app/ui/desktop_frontend/settings_tab.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        imported_names = set()
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)

        self.assertIn('update_contribution_rates', imported_names)
        self.assertNotIn("open('.env', 'a')", source)
        self.assertIn('update_contribution_rates(new_rates)', source)


if __name__ == '__main__':
    unittest.main()
