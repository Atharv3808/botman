from django.test import TestCase
from monitoring.models import SystemLog
from monitoring.utils import Logger

class LoggerTest(TestCase):
    def test_log_creation(self):
        # Test creating logs via Logger utility
        Logger.info('SYSTEM', "Test Info Log", {'foo': 'bar'})
        Logger.error('AI', "Test Error Log", {'error_code': 500})
        
        # Verify logs in DB
        self.assertEqual(SystemLog.objects.count(), 2)
        
        info_log = SystemLog.objects.get(level='INFO')
        self.assertEqual(info_log.category, 'SYSTEM')
        self.assertEqual(info_log.message, "Test Info Log")
        self.assertEqual(info_log.metadata, {'foo': 'bar'})
        
        error_log = SystemLog.objects.get(level='ERROR')
        self.assertEqual(error_log.category, 'AI')
        self.assertEqual(error_log.message, "Test Error Log")
