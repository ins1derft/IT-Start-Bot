import atexit
import logging
import os
import sys
from typing import Optional, Set

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.stdlib import StdlibIntegration
except ImportError:
    sentry_sdk = None  # type: ignore
    LoggingIntegration = None  # type: ignore
    StdlibIntegration = None  # type: ignore

# Track which services have already been initialized to avoid double init.
_sentry_initialized: Set[str] = set()
# Track which services already configured file logging to avoid duplicate handlers.
_log_initialized: Set[str] = set()
# Track services for which we hooked excepthook.
_excepthook_installed: Set[str] = set()
# Track services that encountered unhandled exceptions.
_run_failed: Set[str] = set()
# Track services for which we installed atexit success logger.
_atexit_installed: Set[str] = set()


def _ensure_file_logging(service_name: str) -> None:
    """
    Configure a per-parser file handler so every run leaves a TXT log.
    Log directory can be overridden via PARSERS_LOG_DIR env var,
    defaults to <repo>/parsers/logs next to this file.
    """
    global _log_initialized

    if service_name in _log_initialized:
        return

    log_dir = os.getenv("PARSERS_LOG_DIR") or os.path.join(os.path.dirname(__file__), "logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        # If custom path is invalid, fall back to current working directory.
        log_dir = os.getcwd()
        os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, f"{service_name}.txt")
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))

    root_logger = logging.getLogger()
    # Ensure INFO and below are emitted (default WARNING would drop our messages).
    if root_logger.level > logging.INFO or root_logger.level == logging.NOTSET:
        root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    _log_initialized.add(service_name)
    root_logger.info("File logging initialized for %s at %s", service_name, log_path)

    # Log warnings that would normally go to stderr.
    logging.captureWarnings(True)

    # Ensure uncaught exceptions end up in the file too.
    if service_name not in _excepthook_installed:
        previous_hook = sys.excepthook

        def _logging_excepthook(exc_type, exc_value, exc_traceback):
            _run_failed.add(service_name)
            logging.getLogger(service_name).exception(
                "Unhandled exception in %s",
                service_name,
                exc_info=(exc_type, exc_value, exc_traceback),
            )
            if previous_hook:
                previous_hook(exc_type, exc_value, exc_traceback)

        sys.excepthook = _logging_excepthook
        _excepthook_installed.add(service_name)


def _env_key_from_name(service_name: str) -> str:
    slug = "".join(ch if ch.isalnum() else "_" for ch in service_name).upper()
    return f"SENTRY_DSN_{slug}"


def get_service_logger(service_name: str) -> logging.Logger:
    """
    Helper to get a named logger for a parser.
    Ensures file logging/levels are configured via init_sentry beforehand.
    """
    return logging.getLogger(service_name)


def init_sentry(
    service_name: str,
    dsn_env: Optional[str] = None,
    default_dsn_env: str = "SENTRY_DSN",
    traces_sample_rate: float = 0.0,
) -> None:
    """
    Initialize Sentry for a parser.

    Priority for DSN:
    1. Explicit dsn_env argument.
    2. SENTRY_DSN_<SERVICE_NAME> (non-alnum replaced with "_").
    3. default_dsn_env (SENTRY_DSN by default).
    If sentry-sdk is missing or DSN is not configured, this is a no-op.
    """
    global _sentry_initialized

    # Always prepare file logging, even if Sentry is unavailable/misconfigured.
    _ensure_file_logging(service_name)
    logging.getLogger(service_name).info("Starting parser run: %s", service_name)

    # Register graceful-exit info log (only once per service).
    if service_name not in _atexit_installed:

        def _log_success(service: str = service_name) -> None:
            if service not in _run_failed:
                logging.getLogger(service).info("Parser finished successfully: %s", service)

        atexit.register(_log_success)
        _atexit_installed.add(service_name)

    if service_name in _sentry_initialized or sentry_sdk is None:
        return

    env_keys = []
    if dsn_env:
        env_keys.append(dsn_env)
    env_keys.append(_env_key_from_name(service_name))
    env_keys.append(default_dsn_env)

    dsn = None
    for key in env_keys:
        dsn = os.getenv(key)
        if dsn:
            break

    if not dsn:
        return

    integrations = []
    if StdlibIntegration:
        integrations.append(StdlibIntegration())
    if LoggingIntegration:
        integrations.append(LoggingIntegration(level=logging.INFO, event_level=logging.ERROR))

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=traces_sample_rate,
        environment=os.getenv("ENVIRONMENT", "local"),
        release=os.getenv("RELEASE_VERSION"),
        server_name=service_name,
        integrations=integrations,
    )
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("service", service_name)
        scope.set_tag("parser", service_name)
        scope.set_extra("service_name", service_name)

    _sentry_initialized.add(service_name)
