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
