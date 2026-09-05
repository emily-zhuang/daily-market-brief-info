import os


def smtp_config_from_env() -> tuple[str, str]:
    address = os.getenv("GMAIL_ADDRESS", "").strip()
    app_password = "".join(os.getenv("GMAIL_APP_PASSWORD", "").split())
    if not address or not app_password:
        raise RuntimeError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be configured")
    return address, app_password
