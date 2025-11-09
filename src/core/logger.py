import logging
import logging.config
import os

from .ctx_vars import request_id_ctx_var
from .settings import settings


# Custom logging filter to add UUID from context
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx_var.get()
        return True


request_id_filter = RequestIdFilter()

os.makedirs(os.path.join(settings.LOG_DIR), exist_ok=True)
os.makedirs(os.path.join(settings.LOG_DIR, "payment"), exist_ok=True)

# Load logging configuration from ini file
logging.config.fileConfig(
    os.path.join(settings.ROOT_DIR, "logging.ini"),
    disable_existing_loggers=False,
)

logger = logging.getLogger()
payment_logger = logging.getLogger("payment")

for _handler in [
    *logger.handlers,
    *payment_logger.handlers,
]:
    _handler.addFilter(request_id_filter)
