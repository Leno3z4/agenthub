import requests

GATEWAY_API = "https://gateway-api-testnet.circle.com/v1"
ARC_GATEWAY_DOMAIN = 26

SUPPORTED_EVM_DOMAINS = [
    0,   # Ethereum
    1,   # Avalanche
    2,   # Optimism
    3,   # Arbitrum
    6,   # Base
    7,   # Polygon
    10,  # Unichain
    13,  # Sonic
    14,  # World Chain
    16,  # Sei
    19,  # HyperEVM
    26,  # Arc
]


def get_gateway_balances(address: str):
    if not address or not address.startswith("0x") or len(address) != 42:
        raise ValueError("Invalid EVM wallet address")

    response = requests.post(
        f"{GATEWAY_API}/balances",
        json={
            "token": "USDC",
            "sources": [
                {
                    "domain": domain,
                    "depositor": address,
                }
                for domain in SUPPORTED_EVM_DOMAINS
            ],
        },
        timeout=15,
    )

    response.raise_for_status()

    body = response.json()
    balances = body.get("balances", [])

    total = sum(
        float(item.get("balance", 0))
        for item in balances
    )

    arc_balance = next(
        (
            float(item.get("balance", 0))
            for item in balances
            if item.get("domain") == ARC_GATEWAY_DOMAIN
        ),
        0,
    )

    return {
        "total": total,
        "available": total,
        "arc_balance": arc_balance,
        "balances": balances,
    }
