from typing import List, Dict, Any
from conduit.core.http_client.http_client import http_client
from ldap3 import Server, Connection, ALL, SUBTREE

class LDAPAuthService:
    def __init__(self, server_url: str, base_dn: str, users_dn: str, use_ssl: bool = True):
        # todo: need to uncomment to unable LDAP authentication
        self.server = Server(server_url, use_ssl=use_ssl, get_info=ALL)
        self.base_dn = base_dn
        self.users_dn = users_dn
        self.connection = None

    def login(self, username: str, password: str) -> bool:
        user_dn = f"uid={username},ou=users,{self.base_dn}"
        if self.users_dn:
            user_dn = f"{self.users_dn}{username}"
        self.connection = Connection(self.server, user=user_dn, password=password)
        return self.connection.bind()

    def logout(self) -> bool:
        if self.connection:
            self.connection.unbind()
        return True

    def search_users_and_groups(self, query: str, search_type: str = "all") -> List[Dict[str, Any]]:
        """
        Search LDAP for users and/or groups matching the query.
        
        Args:
            query: Search string to match against cn, uid, or sAMAccountName
            search_type: "user", "group", or "all"
        
        Returns:
            List of dicts with dn, name, and type fields
        """
        results = []
        
        if not self.connection or not self.connection.bound:
            # Create an anonymous connection for search (or use service account)
            search_conn = Connection(self.server, auto_bind=True)
        else:
            search_conn = self.connection

        try:
            # Search for users
            if search_type in ("user", "all"):
                user_filter = f"(&(objectClass=person)(|(cn=*{query}*)(uid=*{query}*)(sAMAccountName=*{query}*)))"
                search_conn.search(
                    search_base=f"ou=users,{self.base_dn}",
                    search_filter=user_filter,
                    search_scope=SUBTREE,
                    attributes=["cn", "uid", "distinguishedName"]
                )
                for entry in search_conn.entries:
                    results.append({
                        "dn": str(entry.entry_dn),
                        "name": str(entry.cn) if hasattr(entry, "cn") else str(entry.uid),
                        "type": "user"
                    })

            # Search for groups
            if search_type in ("group", "all"):
                group_filter = f"(&(objectClass=groupOfNames)(cn=*{query}*))"
                search_conn.search(
                    search_base=f"ou=groups,{self.base_dn}",
                    search_filter=group_filter,
                    search_scope=SUBTREE,
                    attributes=["cn", "distinguishedName"]
                )
                for entry in search_conn.entries:
                    results.append({
                        "dn": str(entry.entry_dn),
                        "name": str(entry.cn),
                        "type": "group"
                    })

        except Exception as e:
            print(f"LDAP search error: {e}")

        return results
