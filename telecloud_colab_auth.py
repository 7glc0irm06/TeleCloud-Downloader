"""
TeleCloud-Downloader — Google Drive Auth Script
================================================
Run this notebook cell-by-cell in Google Colab to:
  1. Authenticate with your Google account
  2. Create the "TeleCloud-Downloads" folder if it doesn't exist
  3. Generate a ready-to-use rclone.conf locked to that folder
  4. Download the config file automatically to your device

After the file downloads, send it to the bot via Telegram — it will
be stored as your personal rclone config and all uploads will go
straight to YOUR Google Drive.

Token expiry note:
  The OAuth2 tokens embedded in the generated rclone.conf include a
  refresh_token. rclone will automatically exchange it for a new
  access_token whenever needed, so the config stays valid indefinitely
  as long as you don't revoke access from your Google Account settings.
"""

# ─────────────────────────────────────────────────────────────
# Cell 1 — Install dependencies (run once per Colab session)
# ─────────────────────────────────────────────────────────────
# !pip install -q google-auth google-auth-oauthlib google-api-python-client

# ─────────────────────────────────────────────────────────────
# Cell 2 — Authenticate & build Drive config
# ─────────────────────────────────────────────────────────────
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ── Colab-specific import (only works inside Google Colab) ──
try:
    from google.colab import auth as colab_auth
    from google.colab import files as colab_files
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

# Scopes required: full Drive access so rclone can read/write files
SCOPES = [
    "https://www.googleapis.com/auth/drive",
]

# ── rclone OAuth2 client credentials (the public "rclone" app) ──
# These are the official rclone client credentials that Google has approved
# for the out-of-band (OOB) flow; they're embedded in every rclone binary.
RCLONE_CLIENT_ID     = "202264815644.apps.googleusercontent.com"
RCLONE_CLIENT_SECRET = "X4Z3ca8xfWDb1Voo-F9a7ZxJ"

# Token endpoint used by rclone
RCLONE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def _get_credentials_via_colab() -> Credentials:
    """Use Colab's built-in auth popup (recommended path)."""
    colab_auth.authenticate_user()
    # After authenticate_user(), the runtime has valid application-default
    # credentials; however those use Colab's own client ID, not rclone's.
    # We therefore do a separate InstalledAppFlow to obtain rclone-compatible
    # tokens that include a proper refresh_token.
    return _get_credentials_via_flow()


def _get_credentials_via_flow() -> Credentials:
    """
    Run an OAuth2 InstalledAppFlow using rclone's public client credentials.
    Colab intercepts the redirect and shows an authorisation code in the cell
    output — the user pastes it back.
    """
    client_config = {
        "installed": {
            "client_id":                  RCLONE_CLIENT_ID,
            "client_secret":              RCLONE_CLIENT_SECRET,
            "auth_uri":                   "https://accounts.google.com/o/oauth2/auth",
            "token_uri":                  RCLONE_TOKEN_URL,
            "redirect_uris":              ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
            "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)

    # Colab cannot open a local browser, so we use the console flow which
    # prints a URL and waits for the user to paste the auth code.
    creds = flow.run_console()
    return creds


def _get_credentials_via_flow() -> Credentials:
    """
    Run an OAuth2 flow manually using localhost redirect workaround.
    """
    client_config = {
        "installed": {
            "client_id":                  RCLONE_CLIENT_ID,
            "client_secret":              RCLONE_CLIENT_SECRET,
            "auth_uri":                   "https://accounts.google.com/o/oauth2/auth",
            "token_uri":                  RCLONE_TOKEN_URL,
            "redirect_uris":              ["http://localhost"],
            "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = "http://localhost"

    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

    print("\n" + "🌐 " + "-"*60)
    print("۱. لطفاً روی لینک زیر کلیک کنید و اکانت گوگل خود را انتخاب کنید:")
    print(auth_url)
    print("-" * 62 + "\n")
    print("⚠️ نکته بسیار مهم: بعد از دادن دسترسی، مرورگر شما به یک صفحه خطا (مثلاً Site cannot be reached یا Localhost) می‌رود.")
    print("این کاملاً طبیعی است! در آن صفحه هیچ کاری نکنید، فقط کل آدرس (URL) آن صفحه را از بالای مرورگر کپی کنید.\n")

    response_url = input("🔗 لطفاً کل آدرس (URL) آن صفحه خطا را اینجا پیست کنید و Enter بزنید: ").strip()

    # استخراج هوشمندانه کد از آدرس URL
    from urllib.parse import urlparse, parse_qs
    parsed_url = urlparse(response_url)
    code_list = parse_qs(parsed_url.query).get('code')

    if code_list:
        code = code_list[0]
    elif response_url.startswith("4/"):
        # در صورتی که کاربر فقط خود کد را وارد کرده باشد
        code = response_url
    else:
        raise ValueError("❌ کد تایید در لینکی که دادید پیدا نشد! مطمئن شوید کل آدرس مرورگر را کپی کرده‌اید.")

    flow.fetch_token(code=code)
    return flow.credentials

def _build_rclone_conf(creds: Credentials, root_folder_id: str) -> str:
    """
    Construct a valid rclone.conf string for a Google Drive remote
    locked to `root_folder_id`.

    Token structure expected by rclone:
      {"access_token": "...", "token_type": "Bearer",
       "refresh_token": "...", "expiry": "2006-01-02T15:04:05.999999999Z07:00"}
    """
    token_dict = {
        "access_token":  creds.token or "",
        "token_type":    "Bearer",
        "refresh_token": creds.refresh_token or "",
        # rclone accepts an empty expiry string; it will refresh automatically.
        "expiry": (
            creds.expiry.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")
            if creds.expiry else "0001-01-01T00:00:00Z"
        ),
    }
    token_json = json.dumps(token_dict)

    conf = f"""\
[gdrive]
type = drive
client_id = {RCLONE_CLIENT_ID}
client_secret = {RCLONE_CLIENT_SECRET}
scope = drive
root_folder_id = {root_folder_id}
token = {token_json}
"""
    return conf


def main():
    print("=" * 60)
    print("  TeleCloud-Downloader — Google Drive Setup")
    print("=" * 60)
    print()

    # Step 1: Authenticate
    print("🔐 Step 1: Authenticating with Google…")
    if IN_COLAB:
        creds = _get_credentials_via_colab()
    else:
        creds = _get_credentials_via_flow()
    print("   Authentication successful.\n")

    # Step 2: Build Drive service & locate/create folder
    print("🔍 Step 2: Checking Google Drive for 'TeleCloud-Downloads' folder…")
    service = build("drive", "v3", credentials=creds)
    folder_id = _get_or_create_folder(service)
    print()

    # Step 3: Build rclone.conf
    print("📝 Step 3: Generating rclone.conf…")
    conf_text = _build_rclone_conf(creds, folder_id)
    print("   Config generated.\n")

    # Step 4: Save & trigger download
    output_path = Path("/tmp/rclone.conf") if IN_COLAB else Path("rclone.conf")
    output_path.write_text(conf_text, encoding="utf-8")
    print(f"💾 Config written to: {output_path}")

    if IN_COLAB:
        print("📥 Step 4: Triggering file download to your device…")
        colab_files.download(str(output_path))
        print()
        print("✅ Done! Send the downloaded 'rclone.conf' to the Telegram bot.")
    else:
        print()
        print("✅ Done! Send 'rclone.conf' (in the current directory) to the Telegram bot.")

    print()
    print("─" * 60)
    print("  After connecting, all your downloads will appear in:")
    print("  My Drive → TeleCloud-Downloads → <source platform>")
    print("─" * 60)


if __name__ == "__main__":
    main()
