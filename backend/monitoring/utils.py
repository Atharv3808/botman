import logging
from .models import SystemLog

logger = logging.getLogger(__name__)

class Logger:
    @staticmethod
    def log(level, category, message, metadata=None):
        """
        Logs an event to the database and standard logging.
        """
        if metadata is None:
            metadata = {}
            
        # Standard logging
        log_msg = f"[{category}] {message} | {metadata}"
        if level == 'ERROR':
            logger.error(log_msg)
        elif level == 'WARNING':
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
            
        # DB Logging
        try:
            SystemLog.objects.create(
                level=level,
                category=category,
                message=message,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Failed to write to SystemLog: {e}")

    @staticmethod
    def info(category, message, metadata=None):
        Logger.log('INFO', category, message, metadata)

    @staticmethod
    def warning(category, message, metadata=None):
        Logger.log('WARNING', category, message, metadata)

    @staticmethod
    def error(category, message, metadata=None):
        Logger.log('ERROR', category, message, metadata)

    @staticmethod
    def debug(category, message, metadata=None):
        # Map debug to INFO for now, or add DEBUG level to model
        Logger.log('INFO', category, message, metadata)

