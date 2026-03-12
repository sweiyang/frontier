"""
Load application configuration from a YAML file.

Config file path: set CONFIG_FILE env var, or default to config.yaml in current
working directory. If the file is missing, defaults are used so the app can run
without a config file.
"""

import os
from pathlib import Path
from typing import Any, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

def _config_path() -> Path:
    """
    Determine the configuration file path.
    
    Returns CONFIG_FILE environment variable if set, otherwise defaults
    to config.yaml in the current working directory.
    """
    path = os.getenv("CONFIG_FILE")
    if path:
        return Path(path)
    return Path.cwd() / "config.yaml"


def _load_yaml(path: Path) -> dict:
    """
    Load and parse a YAML configuration file.
    
    Args:
        path: Path to the YAML file.
        
    Returns:
        Parsed configuration as a dictionary, or empty dict if file
        doesn't exist or contains non-dict data.
        
    Raises:
        RuntimeError: If PyYAML is not installed.
    """
    if not path.exists():
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required for config file support. Install with: pip install pyyaml")
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _get(raw: dict, key: str, default: Any = None) -> Any:
    """Get nested key like 'database.url' from a dict."""
    keys = key.split(".")
    v = raw
    for k in keys:
        if isinstance(v, dict) and k in v:
            v = v[k]
        else:
            return default
    return v


class Config:
    """
    Application configuration loaded from YAML config file.
    
    Provides typed access to all configuration settings with sensible defaults.
    Settings are organized by category: app, database, jwt, ldap, cors, contact,
    faq, admin, and logging.
    
    Attributes:
        _raw: Raw configuration dictionary loaded from YAML.
        _path: Path to the configuration file.
    """

    _raw: dict
    _path: Path

    def __init__(self) -> None:
        """Initialize configuration by loading from the config file path."""
        self._path = _config_path()
        self._raw = _load_yaml(self._path)

    # --- App ---
    @property
    def app_name(self) -> str:
        return _get(self._raw, "app.name") or "Frontier"

    @property
    def splash_text(self) -> str:
        return _get(self._raw, "app.splash_text") or "Welcome to Frontier"

    @property
    def default_project(self) -> Optional[str]:
        """Project name to show when user lands on /. None if not set."""
        v = _get(self._raw, "app.default_project")
        return str(v).strip() if v else None

    @property
    def footnote(self) -> Optional[str]:
        """Footnote to show in the frontend (e.g. 'Powered by team X')."""
        return _get(self._raw, "app.footnote")

    @property
    def logo(self) -> Optional[str]:
        """Path to a logo image file (relative to config file or absolute)."""
        return _get(self._raw, "app.logo")

    # --- Environment ---
    @property
    def app_env(self) -> str:
        """Return the active environment from APP_ENV env var. Defaults to 'dev'."""
        return os.getenv("APP_ENV", "dev").lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "prod"

    @property
    def is_preprod(self) -> bool:
        """Check if running in preprod environment."""
        return self.app_env == "preprod"

    # --- Database ---
    def _db_env(self) -> str:
        """Return the active database environment based on APP_ENV."""
        return self.app_env

    @property
    def database_host(self) -> str:
        return _get(self._raw, f"database.{self._db_env()}.host") or "localhost"

    @property
    def database_port(self) -> int:
        return int(_get(self._raw, f"database.{self._db_env()}.port") or 5432)

    @property
    def database_name(self) -> str:
        return _get(self._raw, f"database.{self._db_env()}.dbname") or "frontier"

    @property
    def database_user(self) -> str:
        return _get(self._raw, f"database.{self._db_env()}.user") or "postgres"

    @property
    def database_credential(self) -> str:
        return _get(self._raw, f"database.{self._db_env()}.credential") or ""

    @property
    def database_schema(self) -> Optional[str]:
        return _get(self._raw, f"database.{self._db_env()}.schema")

    # --- JWT ---
    @property
    def jwt_secret_key(self) -> str:
        return _get(self._raw, "jwt.secret_key") or "frontier-dev-secret-key-change-in-production"

    @property
    def jwt_expire_minutes(self) -> int:
        return int(_get(self._raw, "jwt.expire_minutes") or 60)

    # --- LDAP ---
    @property
    def ldap_server(self) -> str:
        return _get(self._raw, "ldap.server") or "ldap://localhost:1389"

    @property
    def ldap_base_dn(self) -> str:
        return _get(self._raw, "ldap.base_dn") or "dc=example,dc=com"

    @property
    def ldap_use_ssl(self) -> bool:
        v = _get(self._raw, "ldap.use_ssl")
        if v is None:
            return False
        return str(v).lower() in ("true", "1", "yes")

    @property
    def ldap_users_dn(self) -> Optional[str]:
        return _get(self._raw, "ldap.users_dn")

    # --- CORS ---
    @property
    def cors_allow_origins(self) -> List[str]:
        origins = _get(self._raw, "cors.allow_origins")
        if origins is None:
            return ["http://localhost:5173"]
        if isinstance(origins, list):
            return [str(o) for o in origins]
        return [str(origins)]

    # --- Contact ---
    @property
    def contact_email_enabled(self) -> bool:
        v = _get(self._raw, "contact.email.enabled")
        if v is None:
            return False
        return str(v).lower() in ("true", "1", "yes")

    @property
    def contact_email_address(self) -> Optional[str]:
        return _get(self._raw, "contact.email.address")

    @property
    def contact_email_subject_prefix(self) -> str:
        return _get(self._raw, "contact.email.subject_prefix") or "[Support]"

    @property
    def contact_jira_enabled(self) -> bool:
        v = _get(self._raw, "contact.jira.enabled")
        if v is None:
            return False
        return str(v).lower() in ("true", "1", "yes")

    @property
    def contact_jira_url(self) -> Optional[str]:
        return _get(self._raw, "contact.jira.url")

    @property
    def contact_jira_button_text(self) -> str:
        return _get(self._raw, "contact.jira.button_text") or "Create Support Ticket"

    # --- FAQ ---
    @property
    def faq_enabled(self) -> bool:
        v = _get(self._raw, "faq.enabled")
        if v is None:
            return False
        return str(v).lower() in ("true", "1", "yes")

    @property
    def faq_url(self) -> Optional[str]:
        return _get(self._raw, "faq.url")

    @property
    def faq_button_text(self) -> str:
        return _get(self._raw, "faq.button_text") or "FAQ"

    # --- Admin ---
    @property
    def admin_username(self) -> Optional[str]:
        return _get(self._raw, "admin.username")

    @property
    def admin_password(self) -> Optional[str]:
        return _get(self._raw, "admin.password")

    # --- Logging ---
    @property
    def log_level(self) -> str:
        """Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL. Defaults to INFO."""
        return _get(self._raw, "logging.level") or "INFO"

    @property
    def log_format(self) -> str:
        """Log format string for Python logging."""
        return _get(self._raw, "logging.format") or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # --- Approval Workflow ---
    @property
    def approval_enabled(self) -> bool:
        """Whether approval workflow is globally enabled."""
        v = _get(self._raw, "approval.enabled")
        if v is None:
            return True
        return str(v).lower() in ("true", "1", "yes")

    @property
    def approval_require_for_agent_config(self) -> bool:
        """Whether agent configuration changes require approval in prod."""
        v = _get(self._raw, "approval.require_approval_for.agent_config")
        if v is None:
            return True
        return str(v).lower() in ("true", "1", "yes")

    @property
    def approval_require_for_project_settings(self) -> bool:
        """Whether project settings changes require approval in prod."""
        v = _get(self._raw, "approval.require_approval_for.project_settings")
        if v is None:
            return False
        return str(v).lower() in ("true", "1", "yes")

    @property
    def approval_require_for_access_control(self) -> bool:
        """Whether access control changes require approval in prod."""
        v = _get(self._raw, "approval.require_approval_for.access_control")
        if v is None:
            return False
        return str(v).lower() in ("true", "1", "yes")


_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the singleton Config instance.
    
    Creates the instance on first call and returns the same instance
    on subsequent calls.
    
    Returns:
        The application Config singleton.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
