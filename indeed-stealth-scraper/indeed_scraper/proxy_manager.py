"""
proxy_manager.py — Proxy loading, rotation, and health-checking.
"""

import asyncio
import os
import random
from pathlib import Path
from typing import Optional

import httpx

from .logger import get_logger

log = get_logger(__name__)


class ProxyManager:
    """
    Loads proxies from proxies.txt or the PROXY_LIST env var,
    health-checks them, and rotates on failure.
    """

    def __init__(self, proxy_file: str = "proxies.txt") -> None:
        self._all_proxies: list[str] = []
        self._healthy: list[str] = []
        self._current_index: int = 0
        self._proxy_file = proxy_file
        self._load_proxies()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_proxies(self) -> None:
        """Load proxies from file or env var."""
        raw: list[str] = []

        # Env var takes precedence: comma-separated list
        env_proxies = os.environ.get("PROXY_LIST", "")
        if env_proxies:
            raw = [p.strip() for p in env_proxies.split(",") if p.strip()]
            log.info(f"Loaded {len(raw)} proxies from PROXY_LIST env var.")
        else:
            path = Path(self._proxy_file)
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        raw.append(line)
                log.info(f"Loaded {len(raw)} proxies from {self._proxy_file}.")
            else:
                log.warning(
                    f"No proxy file found at '{self._proxy_file}' and PROXY_LIST is empty. "
                    "Running without proxies."
                )

        self._all_proxies = raw

    # ------------------------------------------------------------------
    # Health checking
    # ------------------------------------------------------------------

    async def _check_proxy(self, proxy: str) -> bool:
        """Return True if the proxy can reach a test URL within 5 s."""
        test_url = "https://httpbin.org/ip"
        proxy_url = proxy if "://" in proxy else f"http://{proxy}"
        try:
            async with httpx.AsyncClient(proxy=proxy_url, timeout=5.0) as client:
                resp = await client.head(test_url)
                return resp.status_code < 500
        except Exception as exc:
            log.debug(f"Proxy health-check failed for {proxy}: {exc}")
            return False

    async def refresh_healthy(self) -> None:
        """Re-validate all loaded proxies; populate self._healthy."""
        if not self._all_proxies:
            self._healthy = []
            return

        log.info(f"Health-checking {len(self._all_proxies)} proxies …")
        tasks = [self._check_proxy(p) for p in self._all_proxies]
        results = await asyncio.gather(*tasks)
        self._healthy = [p for p, ok in zip(self._all_proxies, results) if ok]
        log.info(f"{len(self._healthy)}/{len(self._all_proxies)} proxies are healthy.")
        random.shuffle(self._healthy)
        self._current_index = 0

    # ------------------------------------------------------------------
    # Rotation
    # ------------------------------------------------------------------

    def get_next(self) -> Optional[str]:
        """
        Return the next healthy proxy (round-robin) or None if none available.
        """
        if not self._healthy:
            return None
        proxy = self._healthy[self._current_index % len(self._healthy)]
        self._current_index += 1
        return proxy

    def mark_failed(self, proxy: str) -> None:
        """Remove a proxy from the healthy pool after a block/error."""
        if proxy in self._healthy:
            self._healthy.remove(proxy)
            log.warning(f"Proxy removed from pool: {proxy} | Remaining: {len(self._healthy)}")

    def has_proxies(self) -> bool:
        return bool(self._healthy)
