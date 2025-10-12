import asyncio, random
async def run_cover(send_fragment, mean_rate_per_min:int):
    lam = mean_rate_per_min / 60.0
    while True:
        dt = random.expovariate(lam) if lam>0 else 1.0
        await asyncio.sleep(dt)
        await send_fragment(cover=True)
