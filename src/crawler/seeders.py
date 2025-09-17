from __future__ import annotations

SEEDS_EN = [
    "tapmad live",
    "tapmad sports",
    "live cricket tapmad",
    "free match stream",
    "live match hd",
]

SEEDS_BN = [
    "ট্যাপম্যাড লাইভ",
    "ফ্রি খেলা লাইভ",
    "লাইভ ম্যাচ এইচডি",
    "খেলা ফ্রি স্ট্রিম",
]

def expanded_daily_keywords(llm_client) -> list[str]:
    # event_meta could include date; llm_client caches by date
    return llm_client.expand_keywords({"seeds": SEEDS_EN + SEEDS_BN, "date": "today"})


