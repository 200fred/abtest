import base64
import json
import random
import time
import uuid
import requests

MIXPANEL_TOKEN = "721dbfdb6f8f6efee6e89302a933edf4"
EXP_ID = "cart-ab-v1"

TRACK_URL = "https://api.mixpanel.com/track?verbose=1"

def mp_event(name: str, distinct_id: str, props: dict):
    p = {
        "token": MIXPANEL_TOKEN,
        "distinct_id": distinct_id,
        "time": int(time.time()),
        **props,
    }
    return {"event": name, "properties": p}

def send_batch(events: list[dict]) -> None:
    payload = base64.b64encode(json.dumps(events).encode("utf-8")).decode("utf-8")
    r = requests.post(TRACK_URL, data={"data": payload})
    if r.status_code != 200:
        raise RuntimeError(f"Mixpanel HTTP {r.status_code}: {r.text}")
    resp = r.json()
    if resp.get("status") != 1:
        raise RuntimeError(f"Mixpanel error: {resp}")
    # print(resp)  # opzionale

def main():
    random.seed(42)

    n_per_variant = 2276
    cr_a = 0.15
    cr_b = 0.18

    events = []

    for variant in ["A", "B"]:
        cr = cr_a if variant == "A" else cr_b

        for _ in range(n_per_variant):
            distinct_id = str(uuid.uuid4())

            # esposizione
            events.append(mp_event(
                "cart_viewed",
                distinct_id,
                {"experiment_id": EXP_ID, "variant": variant}
            ))

            # conversione
            if random.random() < cr:
                events.append(mp_event(
                    "checkout_started",
                    distinct_id,
                    {"experiment_id": EXP_ID, "variant": variant}
                ))

    # manda in batch piccoli (Mixpanel è più felice)
    batch_size = 50
    for i in range(0, len(events), batch_size):
        send_batch(events[i:i+batch_size])
        time.sleep(0.2)  # evita rate limit

    print(f"Sent events: {len(events)} (users: {n_per_variant*2})")

if __name__ == "__main__":
    main()
