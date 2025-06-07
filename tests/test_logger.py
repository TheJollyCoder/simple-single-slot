import os
import sys
import importlib
import logging
from unittest import TestCase

class LoggerWithoutSettingsTest(TestCase):
    def test_logger_works_without_settings_file(self):
        # Temporarily rename settings.json if it exists
        settings_file = 'settings.json'
        backup_file = settings_file + '.bak'
        restored = False
        if os.path.exists(settings_file):
            os.rename(settings_file, backup_file)
            restored = True
        try:
            if 'logger' in sys.modules:
                del sys.modules['logger']
            logger = importlib.import_module('logger')
            log = logger.get_logger('some_module')
            self.assertIsInstance(log, logging.Logger)
        finally:
            if restored:
                os.rename(backup_file, settings_file)
                if 'logger' in sys.modules:
                    del sys.modules['logger']

