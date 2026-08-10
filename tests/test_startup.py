import asyncio

import pytest
from pydantic import ValidationError


def test_lifespan_rejects_missing_api_key_before_install(monkeypatch, tmp_path):
    from app.config import get_settings
    from app.lifecycle import lifecycle
    from app.main import app, lifespan

    installed = False

    def install():
        nonlocal installed
        installed = True

    async def start():
        async with lifespan(app):
            pass

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENT_API_KEY", raising=False)
    monkeypatch.setattr(lifecycle, "install", install)
    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError):
            asyncio.run(start())
        assert not installed
    finally:
        get_settings.cache_clear()
