import os
import sys

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")
AUTH_ENDPOINT = os.getenv("AUTH_ENDPOINT", "/api/auth/login/")

CHECKS = [
    # Saúde
    {"method": "GET", "path": "/api/health/",               "expect_status": 200},
    {"method": "GET", "path": "/api/status/",               "expect_status": 200},
    # Dashboard
    {"method": "GET", "path": "/api/dashboard/kpis/",           "expect_status": 200},
    {"method": "GET", "path": "/api/dashboard/projects/",       "expect_status": 200},
    {"method": "GET", "path": "/api/dashboard/summary/",        "expect_status": 200},
    {"method": "GET", "path": "/api/dashboard/composition/",    "expect_status": 200},
    {"method": "GET", "path": "/api/dashboard/top-projects/",   "expect_status": 200},
    {"method": "GET", "path": "/api/dashboard/cost-evolution/", "expect_status": 200},
    # Materiais
    {"method": "GET", "path": "/api/compras/",                  "expect_status": 200},
    {"method": "GET", "path": "/api/materials/indicators/",     "expect_status": 200},
    {"method": "GET", "path": "/api/top-materials/",            "expect_status": 200},
    {"method": "GET", "path": "/api/cost-by-project/",          "expect_status": 200},
    {"method": "GET", "path": "/api/materials/filter-options/", "expect_status": 200},
    # Horas técnicas
    {"method": "GET", "path": "/api/horas-tecnicas/",           "expect_status": 200},
    {"method": "GET", "path": "/api/horas-tecnicas/kpis/",      "expect_status": 200},
    {"method": "GET", "path": "/api/horas-tecnicas/temporal/",  "expect_status": 200},
    # Budget / Custos / Consolidado
    {"method": "GET", "path": "/api/budget/",            "expect_status": 200},
    {"method": "GET", "path": "/api/budget/indicators/", "expect_status": 200},
    {"method": "GET", "path": "/api/costs/",             "expect_status": 200},
    {"method": "GET", "path": "/api/consolidated/",      "expect_status": 200},
]


def _login(client: httpx.Client) -> dict:
    resp = client.post(
        AUTH_ENDPOINT,
        json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )
    if resp.status_code != 200:
        print(f"[auth] Login falhou: {resp.status_code} {resp.text[:200]}")
        sys.exit(1)
    body = resp.json()
    token = body.get("access") or body.get("token")
    if not token:
        print(f"[auth] Token não encontrado na resposta: {list(body.keys())}")
        sys.exit(1)
    return {"Authorization": f"Bearer {token}"}


def run() -> None:
    failed: list[str] = []
    headers: dict = {}

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        if AUTH_USERNAME and AUTH_PASSWORD:
            headers = _login(client)
            print(f"  Autenticado como '{AUTH_USERNAME}'")

        for check in CHECKS:
            try:
                resp = client.request(check["method"], check["path"], headers=headers)
                if resp.status_code != check["expect_status"]:
                    failed.append(
                        f"FALHOU {check['method']} {check['path']}: "
                        f"esperado {check['expect_status']}, recebido {resp.status_code}"
                    )
                else:
                    print(f"  OK {check['method']} {check['path']} -> {resp.status_code}")
            except Exception as exc:
                failed.append(f"ERRO {check['method']} {check['path']}: {exc}")

    if failed:
        print("\n--- Smoke test FALHOU ---")
        for msg in failed:
            print(f"  X {msg}")
        sys.exit(1)

    print("\nTodos os smoke tests passaram.")


if __name__ == "__main__":
    run()
