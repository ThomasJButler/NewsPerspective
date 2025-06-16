import logging
import logging.handlers
import os
from datetime import datetime

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

def setup_logger(name="NewsPerspective"):
    """Configure and return a logger instance with file and console handlers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f'logs/news_perspective_{datetime.now().strftime("%Y%m%d")}.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for errors only
    error_handler = logging.handlers.RotatingFileHandler(
        filename='logs/errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

# Performance tracking decorator
def log_performance(logger):
    """Decorator to log function execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.debug(f"Starting {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"{func.__name__} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"{func.__name__} failed after {duration:.2f}s: {str(e)}")
                raise
                
        return wrapper
    return decorator

# Stats tracking class
class StatsTracker:
    """Track and log application statistics"""
    
    def __init__(self, logger):
        self.logger = logger
        self.stats = {
            'articles_fetched': 0,
            'articles_processed': 0,
            'articles_skipped': 0,
            'rewrites_successful': 0,
            'rewrites_failed': 0,
            'api_calls': 0,
            'api_errors': 0,
            'search_queries': 0,
            'uploads_successful': 0,
            'uploads_failed': 0
        }
        self.start_time = datetime.now()
    
    def increment(self, stat_name, count=1):
        """Increment a statistic counter"""
        if stat_name in self.stats:
            self.stats[stat_name] += count
            self.logger.debug(f"Stat updated: {stat_name} = {self.stats[stat_name]}")
    
    def log_summary(self):
        """Log a summary of all statistics"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        self.logger.info("=" * 60)
        self.logger.info("📊 SESSION STATISTICS SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Duration: {duration:.2f} seconds")
        
        for stat, value in self.stats.items():
            if value > 0:  # Only log non-zero stats
                self.logger.info(f"{stat.replace('_', ' ').title()}: {value}")
        
        # Calculate rates
        if self.stats['articles_processed'] > 0:
            success_rate = (self.stats['rewrites_successful'] / self.stats['articles_processed']) * 100
            self.logger.info(f"Rewrite Success Rate: {success_rate:.1f}%")
        
        if self.stats['api_calls'] > 0:
            error_rate = (self.stats['api_errors'] / self.stats['api_calls']) * 100
            self.logger.info(f"API Error Rate: {error_rate:.1f}%")
        
        self.logger.info("=" * 60)

# Error tracking function
def log_error_details(logger, error, context=None):
    """Log detailed error information with context"""
    logger.error(f"Error Type: {type(error).__name__}")
    logger.error(f"Error Message: {str(error)}")
    
    if context:
        logger.error(f"Context: {context}")
    
    # Log stack trace for debugging
    import traceback
    logger.debug(f"Stack Trace:\n{traceback.format_exc()}")
