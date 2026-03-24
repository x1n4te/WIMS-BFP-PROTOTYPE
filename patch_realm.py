# patch_realm.py
import json
from pathlib import Path

def enforce_otp():
    realm_path = Path("src/keycloak/bfp-realm.json")
    
    with open(realm_path, "r", encoding="utf-8") as f:
        realm_data = json.load(f)

    # 1. Enforce standard TOTP policy (FreeOTP / Google Authenticator)
    realm_data["otpPolicyType"] = "totp"
    realm_data["otpPolicyAlgorithm"] = "HmacSHA1"
    realm_data["otpPolicyDigits"] = 6
    realm_data["otpPolicyPeriod"] = 30

    # 2. Force the Browser Authentication Flow to mandate OTP for all users
    for flow in realm_data.get("authenticationFlows", []):
        if flow.get("alias") == "forms":
            for execution in flow.get("authenticationExecutions", []):
                if execution.get("flowAlias", "").endswith("Conditional OTP"):
                    execution["requirement"] = "REQUIRED"

    with open(realm_path, "w", encoding="utf-8") as f:
        json.dump(realm_data, f, indent=2)

if __name__ == "__main__":
    enforce_otp()
