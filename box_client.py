"""Thin Box API client for the Reach Forward agent. Uses box_auth for tokens.
Handles the Box AI 412-while-indexing case with retry/backoff."""
import json, time, io, urllib.request, urllib.error
import box_auth

API = "https://api.box.com/2.0"
UPLOAD = "https://upload.box.com/api/2.0"

def _req(method, url, token, data=None, headers=None, raw=False):
    h = {"Authorization": f"Bearer {token}"}
    if headers: h.update(headers)
    body = None
    if data is not None and not raw:
        body = json.dumps(data).encode(); h["Content-Type"] = "application/json"
    elif raw:
        body = data
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try: return e.code, json.load(e)
        except Exception: return e.code, {"raw": e.read().decode(errors="replace")}

def create_folder(name, parent="0"):
    tok = box_auth.get_access_token()
    st, d = _req("POST", f"{API}/folders", tok, {"name": name, "parent": {"id": parent}})
    if st == 201: return d["id"]
    if st == 409:  # already exists -> return existing id
        return d["context_info"]["conflicts"][0]["id"]
    raise RuntimeError(f"create_folder {name}: {st} {d}")

def upload_text(name, text, parent="0"):
    tok = box_auth.get_access_token()
    boundary = "----rfboundary7f3a"
    attrs = json.dumps({"name": name, "parent": {"id": parent}})
    parts = [
        f"--{boundary}", 'Content-Disposition: form-data; name="attributes"', "", attrs,
        f"--{boundary}",
        f'Content-Disposition: form-data; name="file"; filename="{name}"',
        "Content-Type: text/plain", "", text, f"--{boundary}--", "",
    ]
    body = "\r\n".join(parts).encode()
    st, d = _req("POST", f"{UPLOAD}/files/content", tok, data=body, raw=True,
                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    if st == 201: return d["entries"][0]["id"]
    if st == 409:  # exists: upload new version
        fid = d["context_info"]["conflicts"]["id"]
        st2, d2 = _req("POST", f"{UPLOAD}/files/{fid}/content", tok, data=body, raw=True,
                       headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        return d2["entries"][0]["id"]
    raise RuntimeError(f"upload {name}: {st} {d}")

def _ai(endpoint, payload, tries=6):
    for i in range(tries):
        tok = box_auth.get_access_token()
        st, d = _req("POST", f"{API}/ai/{endpoint}", tok, payload)
        if st == 200: return d
        if st in (412, 429) or (st == 503):  # indexing / rate -> backoff
            time.sleep(5 + i*3); continue
        raise RuntimeError(f"ai/{endpoint}: {st} {d}")
    raise RuntimeError(f"ai/{endpoint}: gave up after {tries} tries (last {st} {d})")

def ai_ask(prompt, file_id):
    return _ai("ask", {"mode": "single_item_qa", "prompt": prompt,
                       "items": [{"id": file_id, "type": "file"}]})["answer"]

def ai_text_gen(prompt, file_ids):
    items = [{"id": f, "type": "file"} for f in file_ids]
    return _ai("text_gen", {"prompt": prompt, "items": items})["answer"]

def ai_extract(fields_prompt, file_id):
    return _ai("extract", {"prompt": fields_prompt,
                           "items": [{"id": file_id, "type": "file"}]})

if __name__ == "__main__":
    print("box_client ok, token:", box_auth.get_access_token()[:6] + "...")
