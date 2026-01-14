import base64
import json
import random
import time
import uuid
import requests
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
MIXPANEL_TOKEN = "721dbfdb6f8f6efee6e89302a933edf4"
TRACK_URL = "https://api.mixpanel.com/track?verbose=1"

EXP_ID = "cart-ab-v2-realistic"
N_PER_VARIANT = 2276

BASE_CR = 0.146     # A
UPLIFT = 0.258      # B relative uplift (~18.4%)

START_TIME = datetime.now() - timedelta(days=7)

# =========================
# DISTRIBUTIONS
# =========================
COUNTRIES = [
    ("US", 0.55),
    ("IT", 0.15),
    ("UK", 0.10),
    ("DE", 0.10),
    ("FR", 0.10),
]

DEVICES = [
    ("web", 0.60),
    ("ios", 0.25),
    ("android", 0.15),
]

BROWSERS = ["Chrome", "Safari", "Firefox", "Edge"]

# =========================
# HELPERS
# =========================
def weighted_choice(options):
    r = random.random()
    cum = 0
    for value, weight in options:
        cum += weight
        if r <= cum:
            return value
    return options[-1][0]

def mp_event(name, distinct_id, timestamp, props):
    return {
        "event": name,
        "properties": {
            "token": MIXPANEL_TOKEN,
            "distinct_id": distinct_id,
            "time": int(timestamp.timestamp()),
            **props
        }
    }

def send_batch(events):
    payload = base64.b64encode(json.dumps(events).encode()).decode()
    r = requests.post(TRACK_URL, data={"data": payload})
    if r.status_code != 200:
        raise RuntimeError(r.text)
    if r.json().get("status") != 1:
        raise RuntimeError(r.json())

# =========================
# MAIN
# =========================
def main():
    random.seed(42)
    events = []

    for variant in ["A", "B"]:
        for _ in range(N_PER_VARIANT):
            distinct_id = str(uuid.uuid4())

            country = weighted_choice(COUNTRIES)
            device = weighted_choice(DEVICES)
            browser = random.choice(BROWSERS)

            # baseline CR with device skew
            cr = BASE_CR
            if device != "web":
                cr *= 0.85  # mobile worse

            if variant == "B":
                cr *= (1 + UPLIFT)

            # timestamps
            t_cart = START_TIME + timedelta(
                seconds=random.randint(0, 7 * 24 * 3600)
            )

            # cart viewed
            events.append(mp_event(
                "cart_viewed",
                distinct_id,
                t_cart,
                {
                    "experiment_id": EXP_ID,
                    "variant": variant,
                    "country": country,
                    "device_type": device,
                    "browser": browser,
                }
            ))

            # conversion
            if random.random() < cr:
                delay = random.randint(15, 180) if variant == "B" else random.randint(30, 300)
                t_checkout = t_cart + timedelta(seconds=delay)

                events.append(mp_event(
                    "checkout_started",
                    distinct_id,
                    t_checkout,
                    {
                        "experiment_id": EXP_ID,
                        "variant": variant,
                        "country": country,
                        "device_type": device,
                        "browser": browser,
                        "time_to_checkout_sec": delay,
                    }
                ))

    # send in batches
    for i in range(0, len(events), 50):
        send_batch(events[i:i+50])
        time.sleep(0.15)

    print(f"Sent {len(events)} events for experiment {EXP_ID}")

if __name__ == "__main__":
    main()
