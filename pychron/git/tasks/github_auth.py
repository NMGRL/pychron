import json
import os


GITHUB_OAUTH_CONFIG = {
    "client_id": "05317d25974cd74eba4e",
    "client_secret": "be1fec163f573bfba2aea8dbd8b0452dad28bf95",
    "auth_uri": "https://github.com/login/oauth/authorize",
    "token_uri": "https://github.com/login/oauth/access_token",
}


def _oauth_file():
    from pychron.paths import paths

    return paths.oauth_file


def load_token():
    path = _oauth_file()
    if not path or not os.path.isfile(path):
        return {}

    try:
        with open(path, "r") as rfile:
            return json.load(rfile)
    except Exception:
        return {}


def save_token(token):
    path = _oauth_file()
    if not path:
        return False

    root = os.path.dirname(path)
    if root:
        os.makedirs(root, exist_ok=True)

    with open(path, "w") as wfile:
        json.dump(token, wfile, indent=2, sort_keys=True)
    return True


def get_access_token():
    token = load_token()
    return token.get("access_token")


def ensure_access_token(scopes=None, force=False):
    token = None if force else get_access_token()
    if token:
        return token

    from pychron.git.tasks.flow import InstalledAppFlow

    flow = InstalledAppFlow()
    token = flow.flow(GITHUB_OAUTH_CONFIG, scopes or ["repo"])
    if token:
        save_token(token)
        return token.get("access_token")


def authorization_headers(token=None):
    token = token or get_access_token()
    if token:
        return {"Authorization": "token {}".format(token)}
    return {}
