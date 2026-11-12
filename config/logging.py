import json
import logging
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Emit one JSON object per log record without adding request or model payloads."""

    def format(self, record):
        item = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            item["exception"] = self.formatException(record.exc_info)
        return json.dumps(item, ensure_ascii=False)
