# concurrency_test.py
import argparse, asyncio, json, time
import httpx

async def worker(client, url, payload, results):
    t0 = time.perf_counter()
    try:
        r = await client.post(url, json=payload, timeout=20)
        ok = (r.status_code == 200) and ("answer" in r.json())
    except Exception:
        ok = False
    results.append((ok, time.perf_counter()-t0))

async def run(url, n, c, role):
    payload = {"q": "What is pneumonia?", "role": role}
    limits = httpx.Limits(max_keepalive_connections=c, max_connections=c)
    async with httpx.AsyncClient(limits=limits) as client:
        results = []
        sem = asyncio.Semaphore(c)
        async def limited():
            async with sem:
                await worker(client, url, payload, results)
        await asyncio.gather(*[limited() for _ in range(n)])
    lat = [t for ok,t in results if ok]
    ok = sum(1 for ok,_ in results if ok)
    print(f"sent={n} ok={ok} fail={n-ok}")
    if lat:
        lat_s = sorted(lat)
        def pct(p): return lat_s[int(len(lat_s)*p/100)]
        print(f"p50={pct(50):.3f}s p90={pct(90):.3f}s p95={pct(95):.3f}s max={max(lat):.3f}s")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8004/ml/qa")
    ap.add_argument("-n", type=int, default=100, help="total requests")
    ap.add_argument("-c", type=int, default=20, help="concurrency")
    ap.add_argument("--role", default="general", choices=["general","doctor","clinician"])
    args = ap.parse_args()
    asyncio.run(run(args.url, args.n, args.c, args.role))
