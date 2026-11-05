import json
import sys
import urllib.request


def main():
    if len(sys.argv) != 3:
        print("Usage: check_http.py BASE_URL EXPECTED_VERSION", file=sys.stderr)
        return 2

    base_url = sys.argv[1].rstrip("/")
    expected_version = sys.argv[2]

    def read_json(path):
        with urllib.request.urlopen(base_url + path, timeout=3) as response:
            if response.status != 200:
                raise RuntimeError(f"{path}: HTTP {response.status}")
            return json.load(response)

    try:
        health = read_json("/health")
        if health != {"status": "ok"}:
            raise RuntimeError(f"Unexpected /health response: {health!r}")

        version = read_json("/version")
        if version != {"version": expected_version}:
            raise RuntimeError(f"Unexpected /version response: {version!r}")
    except (OSError, ValueError, RuntimeError) as error:
        print(f"HTTP CHECK FAILED: {error}", file=sys.stderr)
        return 1

    print(f"HTTP CHECK PASSED: /health OK, version={expected_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())