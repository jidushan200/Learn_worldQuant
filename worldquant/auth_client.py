from os import environ
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv


def load_credentials(env_file: str = ".env"):
    load_dotenv(env_file)
    username = environ.get("BRAIN_USERNAME")
    password = environ.get("BRAIN_PASSWORD")
    if not username or not password:
        raise RuntimeError("请在 .env 中配置 BRAIN_USERNAME / BRAIN_PASSWORD")
    return username, password


def create_authenticated_session(env_file: str = ".env") -> requests.Session:
    # 作用：创建并返回“已登录”的 session，后续提交 alpha 都复用它
    username, password = load_credentials(env_file)
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)

    resp = sess.post("https://api.worldquantbrain.com/authentication", timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"认证失败: {resp.status_code} {resp.text}")
    return sess