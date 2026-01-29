"""App-level configuration: APP_NAME, LDAP. Used by routers and services."""
import os

from conduit.core.auth.auth import LDAPAuthService

APP_NAME = os.getenv("APP_NAME", "Conduit")

LDAP_SERVER = os.getenv("LDAP_SERVER", "ldap://localhost:1389")
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")
LDAP_USE_SSL = os.getenv("LDAP_USE_SSL", "false").lower() == "true"
LDAP_USERS_DN = os.getenv("LDAP_USER_DN", None)

ldap_auth = LDAPAuthService(LDAP_SERVER, LDAP_BASE_DN, LDAP_USERS_DN, LDAP_USE_SSL)
