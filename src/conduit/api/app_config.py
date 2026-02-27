"""App-level configuration: APP_NAME, LDAP, Contact. Used by routers and services."""
from conduit.core.auth.auth import LDAPAuthService
from conduit.core.config import get_config

_cfg = get_config()

APP_NAME = _cfg.app_name
SPLASH_TEXT = _cfg.splash_text
DEFAULT_PROJECT = _cfg.default_project
FOOTNOTE = _cfg.footnote
LOGO = _cfg.logo

LDAP_SERVER = _cfg.ldap_server
LDAP_BASE_DN = _cfg.ldap_base_dn
LDAP_USE_SSL = _cfg.ldap_use_ssl
LDAP_USERS_DN = _cfg.ldap_users_dn

# Contact configuration
CONTACT_EMAIL_ENABLED = _cfg.contact_email_enabled
CONTACT_EMAIL_ADDRESS = _cfg.contact_email_address
CONTACT_EMAIL_SUBJECT_PREFIX = _cfg.contact_email_subject_prefix
CONTACT_JIRA_ENABLED = _cfg.contact_jira_enabled
CONTACT_JIRA_URL = _cfg.contact_jira_url
CONTACT_JIRA_BUTTON_TEXT = _cfg.contact_jira_button_text

# FAQ configuration
FAQ_ENABLED = _cfg.faq_enabled
FAQ_URL = _cfg.faq_url
FAQ_BUTTON_TEXT = _cfg.faq_button_text

ldap_auth = LDAPAuthService(LDAP_SERVER, LDAP_BASE_DN, LDAP_USERS_DN, LDAP_USE_SSL)
