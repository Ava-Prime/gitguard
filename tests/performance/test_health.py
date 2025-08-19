import httpx


def test_health_benchmark(benchmark):
    def _call():
        with httpx.Client(timeout=2.0) as c:
            r = c.get("http://localhost:8000/healthz")
            assert r.status_code == 200

    benchmark(_call)
