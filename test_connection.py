"""Smoke test: is the pipe to Qwen on Alibaba Cloud alive?

ALWAYS the first run after setup, and the check after any change.
GREEN = key + endpoint + model all work. RED lines say exactly what to fix.
If your configured model is retired, this script tries known fallbacks and
prints the exact line to put in .env.
"""

import os
import socket
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
FALLBACK_MODELS = ["qwen-turbo", "qwen-plus", "qwen-flash", "qwen3.7-plus", "qwen-max"]

_use_color = sys.stdout.isatty() and (os.name != "nt" or os.environ.get("WT_SESSION"))
C_GREEN = "\033[92m" if _use_color else ""
C_RED = "\033[91m" if _use_color else ""
C_END = "\033[0m" if _use_color else ""


def main() -> None:
    load_dotenv()
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    base_url = os.environ.get("QWEN_BASE_URL", DEFAULT_BASE_URL)
    preferred = os.environ.get("QWEN_MODEL", "qwen-turbo")

    if not api_key or "your-key" in api_key:
        print(f"{C_RED}RED: no API key.{C_END} Copy .env.example to .env and paste your DashScope key.")
        sys.exit(1)

    host = base_url.split("//")[-1].split("/")[0]
    try:
        socket.create_connection((host, 443), timeout=10).close()
        print(f"network ok: {host} reachable")
    except OSError as exc:
        print(f"{C_RED}RED: cannot reach {host} ({exc}).{C_END} Check internet / firewall / VPN.")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=30)
    candidates = [preferred] + [m for m in FALLBACK_MODELS if m != preferred]

    for model in candidates:
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Reply with exactly one word: pong"}],
                max_tokens=8,
            )
            latency = time.time() - t0
            text = (resp.choices[0].message.content or "").strip()
            print(f"{C_GREEN}GREEN: model '{model}' answered in {latency:.1f}s -> {text!r}{C_END}")
            if model != preferred:
                print(f"note: configured model '{preferred}' did NOT work. Put this line in .env:")
                print(f"    QWEN_MODEL={model}")
            sys.exit(0)
        except Exception as exc:
            msg = str(exc)
            low = msg.lower()
            if "401" in msg or "invalid_api_key" in low or "incorrect api key" in low:
                print(f"{C_RED}RED: 401 auth failed.{C_END} Fix: re-paste the key into .env "
                      "(no quotes, no spaces). The key must come from the SINGAPORE console "
                      "(modelstudio.console.alibabacloud.com/ap-southeast-1) - Beijing keys do not work here.")
                sys.exit(1)
            print(f"  model '{model}' failed: {msg[:140]}")

    print(f"{C_RED}RED: no candidate model worked.{C_END} Open Model Studio -> Models, copy an exact "
          "chat model name from the catalog, and set QWEN_MODEL in .env.")
    sys.exit(1)


if __name__ == "__main__":
    main()
