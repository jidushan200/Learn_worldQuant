from os import environ
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from setting import API_AUTH_URL
from http_utils import request_with_retry


def load_credentials(env_file: str = ".env", account: str = None):
    load_dotenv(env_file, override=False)

    if not account:
        account = (environ.get("ACTIVE_ACCOUNT") or "").strip()
        if not account:
            raise RuntimeError("请在 .env 配置 ACTIVE_ACCOUNT，或直接传入 account 参数")

    username_key = f"BRAIN_USERNAME_{account}"
    password_key = f"BRAIN_PASSWORD_{account}"

    username = (environ.get(username_key) or "").strip()
    password = (environ.get(password_key) or "").strip()

    if not username or not password:
        raise RuntimeError(f"未找到 {username_key} / {password_key}，请检查 .env")

    return username, password


def create_authenticated_session(env_file: str = ".env", account: str = None):
    username, password = load_credentials(env_file, account)
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)

    resp = request_with_retry(sess, "POST", API_AUTH_URL, label="认证")
    if resp is None:
        raise RuntimeError("认证失败：重试耗尽仍无响应")
    if resp.status_code >= 400:
        raise RuntimeError(f"认证失败: {resp.status_code} {resp.text}")

    return sess, resp.status_code