"""Access log summarizer.

Usage:
    python src/log_parser.py data/access_2026-07-15.log
"""
import sys
from collections import Counter


def parse_line(line):
    parts = line.strip().split(" ")
    return {
        "date": parts[0],
        "time": parts[1],
        "method": parts[2],
        "path": parts[3],
        "status": int(parts[4]),
        "latency_ms": int(parts[5].removesuffix("ms")),
    }


def summarize(log_path):
    ok = redirect = client_error = server_error = 0
    total_latency = 0
    count = 0
    endpoints = Counter()
    endpoints_by_status = {
        "2xx": Counter(),
        "3xx": Counter(),
        "4xx": Counter(),
        "5xx": Counter(),
    }

    with open(log_path, encoding="utf-8") as f:
        for line in f:
            if len(line.strip().split(" ")) < 6:
                continue
            record = parse_line(line)
            status = record["status"]
            path = record["path"]
            if 200 <= status < 300:
                ok += 1
                endpoints_by_status["2xx"][path] += 1
            elif 300 <= status < 400:
                redirect += 1
                endpoints_by_status["3xx"][path] += 1
            elif 400 <= status < 500:
                client_error += 1
                endpoints_by_status["4xx"][path] += 1
            elif status >= 500:
                server_error += 1
                endpoints_by_status["5xx"][path] += 1
            total_latency += record["latency_ms"]
            endpoints[path] += 1
            count += 1

    top_endpoint_by_status = {
        bucket: (counter.most_common(1)[0] if counter else None)
        for bucket, counter in endpoints_by_status.items()
    }

    return {
        "total": count,
        "2xx": ok,
        "3xx": redirect,
        "4xx": client_error,
        "5xx": server_error,
        "avg_latency_ms": total_latency // count,
        "top_endpoints": endpoints.most_common(3),
        "top_endpoint_by_status": top_endpoint_by_status,
    }


def main():
    if len(sys.argv) != 2:
        print("usage: python src/log_parser.py <log_path>")
        sys.exit(1)
    stats = summarize(sys.argv[1])
    print(f"total requests : {stats['total']}")
    print(f"2xx / 3xx      : {stats['2xx']} / {stats['3xx']}")
    print(f"4xx / 5xx      : {stats['4xx']} / {stats['5xx']}")
    print(f"avg latency    : {stats['avg_latency_ms']}ms")
    print("top endpoints  :")
    for path, hits in stats["top_endpoints"]:
        print(f"  {path}  {hits}")
    print("top endpoint by status:")
    for bucket in ("2xx", "3xx", "4xx", "5xx"):
        top = stats["top_endpoint_by_status"][bucket]
        if top is None:
            print(f"  {bucket}: -")
        else:
            print(f"  {bucket}: {top[0]}  ({top[1]})")


if __name__ == "__main__":
    main()
