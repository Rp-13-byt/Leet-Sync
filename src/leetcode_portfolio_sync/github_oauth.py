from __future__ import annotations

import os
import time
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class DeviceCode:
    device_code: str
    user_code: str
    verification_uri: str
    interval: int


class GitHubOAuthDeviceFlow:
    def __init__(self, client_id_env: str) -> None:
        self.client_id = os.getenv(client_id_env, "")
        if not self.client_id:
            raise RuntimeError(f"Set {client_id_env} to use GitHub OAuth device login.")

    def start(self) -> DeviceCode:
        response = requests.post(
            "https://github.com/login/device/code",
            data={"client_id": self.client_id, "scope": "repo"},
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return DeviceCode(
            device_code=payload["device_code"],
            user_code=payload["user_code"],
            verification_uri=payload["verification_uri"],
            interval=int(payload.get("interval", 5)),
        )

    def poll(self, device_code: str, interval: int) -> str:
        while True:
            response = requests.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if token := payload.get("access_token"):
                return str(token)
            error = payload.get("error")
            if error == "authorization_pending":
                time.sleep(interval)
                continue
            if error == "slow_down":
                interval += 5
                time.sleep(interval)
                continue
            raise RuntimeError(
                str(payload.get("error_description") or error or "OAuth failed")
            )
