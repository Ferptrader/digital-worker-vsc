"""Read-only reachability probe for the ORIGINAL Atlas site.

No authentication, no project API writes, no cookies, and no assertions about
private map state or browser navigation. Exit nonzero if public access fails.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SITE = "https://atlas-ideias-fernando.ferpmorales.chatgpt.site"


def probe(fetch=urlopen):
    evidence = {
        "site": SITE,
        "method": "GET_PUBLIC_READ_ONLY",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "navigation_tested": False,
        "private_project_accessed": False,
        "deployment_changed": False,
        "result": "UNVERIFIED",
    }
    try:
        request = Request(
            SITE, headers={"User-Agent": "AENV-REAL-001-Atlas-ReadOnly-Probe/1.0"}
        )
        with fetch(request, timeout=12) as response:
            data = response.read(1_000_001)
            status = response.getcode()
            final = response.geturl()
        evidence["http_status"] = status
        evidence["final_url"] = final
        evidence["sample_sha256"] = hashlib.sha256(data).hexdigest()
        evidence["sample_size"] = len(data)
        if status == 200 and "chatgpt.site" in final and b"Atlas" in data:
            evidence["result"] = "PUBLIC_SITE_CONTENT_REACHABLE"
        elif status == 200:
            evidence["result"] = "HTTP_OK_CONTENT_NOT_VERIFIED"
        else:
            evidence["result"] = "HTTP_UNEXPECTED_STATUS"
    except HTTPError as exc:
        evidence["http_status"] = exc.code
        evidence["result"] = "HTTP_ACCESS_OR_SERVER_ERROR"
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        evidence["result"] = "PUBLIC_PROBE_UNAVAILABLE"
        evidence["error_type"] = type(exc).__name__
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="atlas_public_probe.json")
    args = parser.parse_args()
    result = probe()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "PUBLIC_SITE_CONTENT_REACHABLE" else 2


if __name__ == "__main__":
    sys.exit(main())
