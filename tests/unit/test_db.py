"""Tests for the database session factory module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from netpalm.backend.core.db import get_db_session, get_engine, get_session_factory


class TestDbModule:
    @patch("netpalm.backend.core.db.get_settings")
    @patch("netpalm.backend.core.db.create_async_engine")
    def test_get_engine(self, mock_create_engine, mock_get_settings):
        # Clear the lru_cache
        get_engine.cache_clear()

        mock_settings = MagicMock()
        mock_settings.database_url = "postgresql+asyncpg://test:test@localhost/test"
        mock_get_settings.return_value = mock_settings

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        result = get_engine()

        mock_create_engine.assert_called_once_with(
            "postgresql+asyncpg://test:test@localhost/test",
            echo=False,
            pool_pre_ping=True,
        )
        assert result == mock_engine

        # Clean up cache
        get_engine.cache_clear()

    @patch("netpalm.backend.core.db.get_engine")
    @patch("netpalm.backend.core.db.async_sessionmaker")
    def test_get_session_factory(self, mock_sessionmaker, mock_get_engine):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        get_session_factory()

        mock_sessionmaker.assert_called_once_with(mock_engine, expire_on_commit=False)

    @patch("netpalm.backend.core.db.get_session_factory")
    async def test_get_db_session_yields_session(self, mock_factory_fn):
        mock_session = MagicMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session

        mock_factory = MagicMock()
        mock_factory.return_value = mock_context
        mock_factory_fn.return_value = mock_factory

        # Collect yielded value
        gen = get_db_session()
        session = await gen.__anext__()
        assert session == mock_session
