from os import environ
import requests
import os
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from setting import API_AUTH_URL
from http_utils import request_with_retry


def load_credentials(env_file: str = ".env", account: str = None):
    load_dotenv(env_file, override=False)
    username = get_required_env("BRAIN_USERNAME_ACC7")
    password = get_required_env("BRAIN_PASSWORD_ACC7")

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

def get_required_env(key: str) -> str:
    """
    从环境变量获取指定 key 的值，若不存在或为空则抛出 RuntimeError。
    会自动调用 load_dotenv() 加载 .env 文件（可放在函数外全局调用一次）。
    """
    load_dotenv()  # 可放在模块顶层只调用一次，此处为保险
    value = os.getenv(key)
    if not value or not value.strip():
        raise RuntimeError(f"环境变量 {key} 未设置或为空，请检查 .env 文件")
    return value.strip()
