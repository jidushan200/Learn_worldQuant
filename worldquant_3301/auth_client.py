from os import environ
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv


def load_credentials(env_file: str = ".env"):
    load_dotenv(env_file, override=False)

    active = (environ.get("ACTIVE_ACCOUNT") or "").strip()
    if not active:
        raise RuntimeError("请在 .env 配置 ACTIVE_ACCOUNT，例如 ACC1")

    username_key = f"BRAIN_USERNAME_{active}"
    password_key = f"BRAIN_PASSWORD_{active}"

    username = (environ.get(username_key) or "").strip()
    password = (environ.get(password_key) or "").strip()

    if not username or not password:
        raise RuntimeError(f"未找到 {username_key} / {password_key}，请检查 .env")

    return username, password


def create_authenticated_session(env_file: str = ".env"):
    # 返回 (session, auth_status_code)
    username, password = load_credentials(env_file)
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)

    resp = sess.post("https://api.worldquantbrain.com/authentication", timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"认证失败: {resp.status_code} {resp.text}")

    return sess, resp.status_code