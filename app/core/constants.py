"""Application-wide constants.

This module stores static, reusable values referenced across the
codebase. It intentionally contains no business logic and no
environment-dependent values — those belong in
:mod:`app.core.config`.
"""

from typing import Final

# General application metadata
DEFAULT_APP_NAME: Final[str] = "AI Consulting Firm"
DEFAULT_ENCODING: Final[str] = "utf-8"

# Logging
LOG_DIRECTORY_NAME: Final[str] = "logs"
LOG_FILE_NAME: Final[str] = "app.log"
LOG_ROTATION_SIZE: Final[str] = "10 MB"
LOG_RETENTION_PERIOD: Final[str] = "14 days"

# Filesystem
REPORTS_DIRECTORY_NAME: Final[str] = "reports"
