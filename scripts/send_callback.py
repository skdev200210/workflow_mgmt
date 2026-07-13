import requests  # type: ignore

BASE_URL = "http://localhost:8000"
API_KEY = "changeme-dev-key"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

AGENT_EXECUTIONS = {
    # "sam": "62811f8f-482f-40cc-9e46-eea2db3ca6f7",
    "sam": "bbfaff51-b46e-46a8-8021-a58b6a4ea2dc",
    # "ravi": "f25a2565-d212-4b37-a58a-8d7b2ffb4978",
    "ravi": "6266f4f8-6e8e-4264-b0fd-f5d37e2073e6",
    # "arjun": "b17d5d7c-a2d3-4bb5-853f-72e691ba6d61",
    "arjun": "c13bdf5d-6d16-4d97-af71-5722ce382ddc",
    # "priya": "9a30f30d-0e5c-4f27-b666-11d83a49aaa8",
    "priya": "6d96e8c3-7392-4a5c-a090-1b37da8e4a50",
    "meera": "fc51b4ca-aab8-42bb-bae7-4b97bf965eb5",
    "sam_whatsapp": "bbfaff51-b46e-46a8-8021-a58b6a4ea2dc",
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
            "ptp_given_bser": False,
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


send_callback(
    "sam_whatsapp",
    {
        "source": "whatsapp",
        "outcome": "success",
        "result": {
            "provider": "mock",
            "delivered": True,
        },
    },
)
