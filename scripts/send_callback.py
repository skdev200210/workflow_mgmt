import requests #type: ignore

BASE_URL = "http://localhost:8000"
API_KEY = "changeme-dev-key"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

AGENT_EXECUTIONS = {
    "sam": "0cee0ca0-683b-4872-8178-32064f30968b",
    "ravi": "f2b18ebf-58dc-487c-a96c-6a3a3b8bd264",
    "arjun": "d91954bd-d6bc-40c1-8792-53c5c1ce7866",
    "priya": "841236de-df0b-4f41-bfb0-28f9eeb1ad30",
    "meera": "bc3df2f9-db45-4488-abd3-db7b399653af",
}


def send_callback(name: str, payload: dict):
    payload["agent_execution_id"] = AGENT_EXECUTIONS[name]

    response = requests.post(
        f"{BASE_URL}/callbacks",
        headers=HEADERS,
        json=payload,
    )

    print(f"\n{name.upper()}")
    print(response.status_code)
    print(response.json())


send_callback(
    "sam",
    {
        "source": "calling",
        "outcome": "success", 
        "outputs": {
            "ptp": True,
        },
        "result": {
            "provider": "mock",
            "duration_sec": 42,
        },
    },
)

send_callback(
    "ravi",
    {
        "source": "calling",
        "outcome": "success",
        "outputs": {
            "ptp": False,
        },
        "result": {
            "provider": "mock",
            "duration_sec": 18,
        },
    },
)

send_callback(
    "arjun",
    {
        "source": "calling",
        "outcome": "retry",
        "status": "no_answer",
    },
)

send_callback(
    "priya",
    {
        "source": "sms",
        "outcome": "success",
        "result": {
            "provider": "mock",
            "delivered": True,
        },
    },
)

send_callback(
    "meera",
    {
        "source": "sms",
        "outcome": "failure",
        "status": "undeliverable",
        "result": {
            "provider": "mock",
            "error_code": "E42",
        },
    },
)