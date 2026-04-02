from typing import Any, Dict, Optional

from ldap3 import ALL, Connection, Server

from core.logging import get_logger

logger = get_logger(__name__)


class LDAPAuthService:
    """
    LDAP authentication service for user login and directory queries.

    Provides methods to authenticate users against an LDAP server and
    retrieve user details including group memberships.

    Attributes:
        server: LDAP server connection object.
        base_dn: Base distinguished name for LDAP searches.
        users_dn: DN prefix for user lookups.
        user_connection: Dict mapping usernames to active LDAP connections.
    """

    def __init__(self, server_url: str, base_dn: str, users_dn: str, use_ssl: bool = True):
        """
        Initialize the LDAP authentication service.

        Args:
            server_url: LDAP server URL (e.g., 'ldap://localhost:389').
            base_dn: Base DN for searches (e.g., 'dc=example,dc=com').
            users_dn: DN prefix for user lookups (e.g., 'uid=').
            use_ssl: Whether to use SSL/TLS for connections.
        """
        self.server = Server(server_url, use_ssl=use_ssl, get_info=ALL)
        self.base_dn = base_dn
        self.users_dn = users_dn
        self.user_connection = {}

    def login(self, username: str, password: str) -> bool:
        """Authenticate user against LDAP server.

        Returns:
            True if authentication successful, False otherwise.
        """
        user_dn = f"uid={username},ou=users,{self.base_dn}"
        if self.users_dn:
            user_dn = f"{self.users_dn}{username}"

        # Close any stale connection for this username before creating a new one
        old_conn = self.user_connection.pop(username, None)
        if old_conn is not None:
            try:
                old_conn.unbind()
            except Exception:
                logger.debug("Failed to unbind stale LDAP connection for user {}", username)

        connection = None
        try:
            connection = Connection(
                self.server,
                user=user_dn,
                password=password,
                auto_bind=True,
                receive_timeout=30,  # 30-second TTL to prevent connection leaks
            )
            self.user_connection[username] = connection
            return True
        except Exception:
            logger.opt(exception=True).error("LDAP bind error for user {}", username)
            # Clean up the connection object if it was partially created
            if connection is not None:
                try:
                    connection.unbind()
                except Exception:
                    pass
            return False

    def logout(self):
        """Clear all user connections."""
        for conn in self.user_connection.values():
            try:
                conn.unbind()
            except Exception:
                logger.opt(exception=True).debug("Error unbinding LDAP connection during logout")
        self.user_connection.clear()

    def search_users_and_groups(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Search LDAP for user details including group memberships.

        Args:
            username: The username (sAMAccountName) to search for

        Returns:
            Dict with username, name, email, and member_of fields, or None if not found
        """
        connection = self.user_connection.get(username, None)
        if not connection:
            logger.warning("LDAP search connection not found for user {}, login first", username)
            return None

        try:
            connection.search(
                self.base_dn,
                search_filter=f"(&(objectClass=user)(sAMAccountName={username}))",
                attributes=["displayName", "mail", "memberOf", "cn"],
            )
            logger.debug(
                "LDAP search completed for {}, found {} entries",
                username,
                len(connection.entries),
            )
        except Exception:
            logger.opt(exception=True).error("LDAP search error for user {}", username)
            return None

        if not connection.entries:
            logger.warning("LDAP no entries found for user: {}", username)
            return None

        metadata = connection.entries[0]
        logger.debug("LDAP entry DN: {}", metadata.entry_dn)
        logger.debug("LDAP entry attributes: {}", metadata.entry_attributes_as_dict)

        # Get displayName, falling back to cn if not available
        display_name = None
        if hasattr(metadata, "displayName") and metadata.displayName.value:
            display_name = metadata.displayName.value
        elif hasattr(metadata, "cn") and metadata.cn.value:
            display_name = metadata.cn.value

        # Get email
        email = None
        if hasattr(metadata, "mail") and metadata.mail.value:
            email = metadata.mail.value

        # Get memberOf - normalize to list
        member_of = None
        if hasattr(metadata, "memberOf"):
            member_of_value = metadata.memberOf.value
            if member_of_value:
                if isinstance(member_of_value, list):
                    member_of = member_of_value
                else:
                    member_of = [member_of_value]

        result = {
            "username": username,
            "name": display_name,
            "email": email,
            "member_of": member_of,
        }
        logger.debug("LDAP user details: {}", result)
        return result
