"""Render the Keycloak realm import for the fixed client hostname.

Reads the shared realm export (src/keycloak/import/bfp-realm.json), keeps only
https://<host> redirect URIs / web origins / post-logout URIs for the two web clients, and
writes it for Keycloak's --import-realm. Realm users stay empty.

usage: render_realm.py <in.json> <out.json> <host>
"""

import json
import sys


def render(realm: dict, host: str) -> dict:
    base = f"https://{host}"
    for client in realm.get("clients", []):
        if client.get("clientId") not in ("wims-web", "bfp-client"):
            continue
        client["redirectUris"] = [f"{base}/callback", f"{base}/*"]
        client["webOrigins"] = [base]
        attrs = client.setdefault("attributes", {})
        attrs["post.logout.redirect.uris"] = f"{base}/*"
    realm["users"] = []
    return realm


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    src, dst, host = sys.argv[1:4]
    with open(src, encoding="utf-8") as fh:
        realm = json.load(fh)
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(render(realm, host), fh, indent=2)
    print(f"realm rendered for https://{host} -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
