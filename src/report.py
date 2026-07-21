import datetime


def f1(d):
    s = ""
    s = s + "========================================" + "\n"
    s = s + " DAILY TRAFFIC REPORT" + "\n"
    s = s + "========================================" + "\n"
    s = s + " generated: " + str(datetime.date.today()) + "\n"
    s = s + "----------------------------------------" + "\n"
    s = s + " total     : " + str(d["total"]) + "\n"
    s = s + " success   : " + str(d["2xx"]) + " (" + str(round(d["2xx"] / d["total"] * 100, 1)) + "%)" + "\n"
    s = s + " redirect  : " + str(d["3xx"]) + " (" + str(round(d["3xx"] / d["total"] * 100, 1)) + "%)" + "\n"
    s = s + " client err: " + str(d["4xx"]) + " (" + str(round(d["4xx"] / d["total"] * 100, 1)) + "%)" + "\n"
    s = s + " server err: " + str(d["5xx"]) + " (" + str(round(d["5xx"] / d["total"] * 100, 1)) + "%)" + "\n"
    return s


def f2(d):
    x = ""
    if d["5xx"] / d["total"] * 100 >= 5:
        x = x + " [!] server error rate over 5% - check on-call" + "\n"
    if d["avg_latency_ms"] >= 300:
        x = x + " [!] avg latency over 300ms - check slow queries" + "\n"
    if x == "":
        x = " no alerts" + "\n"
    return x


def f3(d):
    s = ""
    s = s + "----------------------------------------" + "\n"
    s = s + " TOP ENDPOINTS" + "\n"
    s = s + "----------------------------------------" + "\n"
    for t in d["top_endpoints"]:
        s = s + " " + t[0] + "  " + str(t[1]) + "\n"
    s = s + "========================================" + "\n"
    return s


def f4(d):
    s = ""
    s = s + "----------------------------------------" + "\n"
    s = s + " TOP ENDPOINT BY STATUS" + "\n"
    s = s + "----------------------------------------" + "\n"
    for bucket in ("2xx", "3xx", "4xx", "5xx"):
        top = d["top_endpoint_by_status"][bucket]
        if top is None:
            s = s + " " + bucket + " : -" + "\n"
        else:
            s = s + " " + bucket + " : " + top[0] + "  (" + str(top[1]) + ")" + "\n"
    return s


def make(d):
    r = f1(d)
    r = r + "----------------------------------------" + "\n"
    r = r + " ALERTS" + "\n"
    r = r + "----------------------------------------" + "\n"
    r = r + f2(d)
    r = r + f4(d)
    r = r + f3(d)
    return r


if __name__ == "__main__":
    sample = {
        "total": 31,
        "2xx": 21,
        "3xx": 2,
        "4xx": 4,
        "5xx": 4,
        "avg_latency_ms": 311.3,
        "top_endpoints": [("/api/orders", 16), ("/api/products", 7), ("/api/login", 2)],
        "top_endpoint_by_status": {
            "2xx": ("/api/orders", 12),
            "3xx": ("/legacy/export", 2),
            "4xx": ("/api/users/42", 2),
            "5xx": ("/api/orders", 4),
        },
    }
    print(make(sample))
