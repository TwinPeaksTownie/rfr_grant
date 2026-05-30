import json, os, time, urllib.request, urllib.parse, pathlib
import boto3

HERE = pathlib.Path(__file__).parent
TOKENS = HERE / "box_tokens.json"
PARAMETER_NAME = "/reachforward/box_tokens"

def _env(k):
    # In Lambda, prefer real environment variables
    if k in os.environ:
        return os.environ[k]
    # Fallback to local .env
    env_file = HERE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip()
    raise KeyError(k)

CLIENT_ID = _env("BOX_CLIENT_ID")
CLIENT_SECRET = _env("BOX_CLIENT_SECRET")

def _post(data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request("https://api.box.com/oauth2/token", data=body)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

def _get_tokens():
    try:
        ssm = boto3.client('ssm', region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        resp = ssm.get_parameter(Name=PARAMETER_NAME, WithDecryption=True)
        return json.loads(resp['Parameter']['Value'])
    except Exception as e:
        print("SSM token fetch failed, falling back to local file:", e)
        return json.loads(TOKENS.read_text())

def _save(tok):
    tok["obtained_at"] = int(time.time())
    val = json.dumps(tok)
    
    try:
        ssm = boto3.client('ssm', region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        ssm.put_parameter(Name=PARAMETER_NAME, Value=val, Type='SecureString', Overwrite=True)
    except Exception as e:
        print("SSM token save failed:", e)
        
    try:
        TOKENS.write_text(val)
    except OSError:
        pass # Expected in AWS Lambda (Read-only file system)

def get_access_token():
    tok = _get_tokens()
    age = time.time() - tok.get("obtained_at", 0)
    # refresh a few minutes early
    if "access_token" in tok and age < tok.get("expires_in", 3600) - 300:
        return tok["access_token"]
    new = _post({
        "grant_type": "refresh_token",
        "refresh_token": tok["refresh_token"],
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    })
    _save(new)
    return new["access_token"]

if __name__ == "__main__":
    print(get_access_token()[:8] + "...(works)")
