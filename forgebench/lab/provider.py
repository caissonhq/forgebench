"""One bounded HTTP request per trial; no shell execution or provider SDK."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


DEFAULT_SETTINGS = {"base_url": "http://localhost:11434/v1", "model": "", "allow_remote": False}


def validate_settings(data):
    if not isinstance(data, dict):
        raise ValueError("Endpoint settings must be an object.")
    base = data.get("base_url", "").strip() if isinstance(data.get("base_url"), str) else ""
    model = data.get("model", "").strip() if isinstance(data.get("model"), str) else ""
    if len(base) > 2000 or not model or len(model) > 160:
        raise ValueError("Provide an endpoint URL and a model name (up to 160 characters).")
    url = urlsplit(base)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("Use an HTTP(S) base URL without credentials, query parameters, or fragments.")
    try:
        url.port
    except ValueError as exc:
        raise ValueError("The endpoint port is invalid.") from exc
    local = url.hostname in ("localhost", "127.0.0.1", "::1")
    if not local and (url.scheme != "https" or data.get("allow_remote") is not True):
        raise ValueError("Remote endpoints require HTTPS and explicit permission to send trial data.")
    return {"base_url": base.rstrip("/"), "model": model, "allow_remote": not local}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def complete(case, settings):
    config = validate_settings(settings)
    payload = {"model": config["model"], "messages": [
        {"role": "system", "content": case["system"]},
        {"role": "user", "content": case["prompt"]},
    ], "temperature": 0, "max_tokens": 512, "stream": False}
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("FORGEBENCH_LAB_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = Request(config["base_url"] + "/chat/completions", data=json.dumps(payload).encode(), headers=headers)
    # Do not forward credentials across redirects or through implicit environment proxies.
    opener = build_opener(NoRedirect(), ProxyHandler({}))
    try:
        with opener.open(request, timeout=45) as response:
            raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            raise ValueError("Provider response exceeded 1 MiB.")
        data = json.loads(raw)
        answer = data["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or len(answer) > 64000:
            raise ValueError("Provider must return a text completion of at most 64,000 characters.")
        return answer
    except HTTPError as exc:
        code = exc.code
        exc.close()
        raise ValueError(f"Provider returned HTTP {code}. Check endpoint, model, and server-side API key.") from None
    except (URLError, TimeoutError, OSError):
        raise ValueError("Could not reach the provider within 45 seconds. Check that the model server is running.") from None
    except (KeyError, IndexError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Provider returned an invalid chat-completion response.") from None
