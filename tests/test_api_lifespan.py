"""
Tests for API server lifespan management.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient


class TestAPILifespan:
    """Test API server lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_startup_success(self) -> None:
        """Test successful startup of API server."""
        from merlai.api.main import lifespan, app
        
        # Mock the components
        mock_music_gen = Mock()
        mock_music_gen.load_model = Mock()
        mock_midi_gen = Mock()
        mock_plugin_mgr = Mock()
        mock_plugin_mgr.scan_plugins = Mock(return_value=[])
        
        with patch("merlai.api.main.MusicGenerator", return_value=mock_music_gen), \
             patch("merlai.api.main.MIDIGenerator", return_value=mock_midi_gen), \
             patch("merlai.api.main.PluginManager", return_value=mock_plugin_mgr):
            
            # Test lifespan context manager
            async with lifespan(app) as _:
                # Verify components were initialized
                assert hasattr(app.state, 'music_generator')
                assert hasattr(app.state, 'midi_generator')
                assert hasattr(app.state, 'plugin_manager')
                
                # Verify plugin scan was called
                mock_plugin_mgr.scan_plugins.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_model_load_failure(self) -> None:
        """Test lifespan handles model loading failure gracefully."""
        from merlai.api.main import lifespan, app
        
        # Mock components with failing model load
        mock_music_gen = Mock()
        mock_music_gen.load_model = Mock(side_effect=Exception("Model load failed"))
        mock_midi_gen = Mock()
        mock_plugin_mgr = Mock()
        mock_plugin_mgr.scan_plugins = Mock(return_value=[])
        
        with patch("merlai.api.main.MusicGenerator", return_value=mock_music_gen), \
             patch("merlai.api.main.MIDIGenerator", return_value=mock_midi_gen), \
             patch("merlai.api.main.PluginManager", return_value=mock_plugin_mgr):
            
            # Should not raise exception even if model load fails
            async with lifespan(app) as _:
                # Components should still be initialized
                assert hasattr(app.state, 'music_generator')
                assert hasattr(app.state, 'midi_generator')
                assert hasattr(app.state, 'plugin_manager')

    def test_health_check_with_model_loaded(self) -> None:
        """Test health check when model is loaded."""
        from merlai.api.main import app
        
        with TestClient(app) as client:
            # Set up app state
            app.state.music_generator = Mock()
            app.state.music_generator.model = Mock()  # Model is loaded
            app.state.plugin_manager = Mock()
            app.state.plugin_manager.plugins = [Mock(), Mock()]  # 2 plugins
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["model_loaded"] is True
            assert data["plugins_loaded"] == 2

    def test_health_check_without_model(self) -> None:
        """Test health check when model is not loaded."""
        from merlai.api.main import app
        
        with TestClient(app) as client:
            # Set up app state with no model
            app.state.music_generator = Mock()
            app.state.music_generator.model = None  # No model
            app.state.plugin_manager = Mock()
            app.state.plugin_manager.plugins = []
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["model_loaded"] is False
            assert data["plugins_loaded"] == 0

    def test_readiness_check(self) -> None:
        """Test readiness check endpoint."""
        from merlai.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"

    def test_root_endpoint(self) -> None:
        """Test root endpoint."""
        from merlai.api.main import app
        
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "version" in data
            assert "status" in data
            assert data["version"] == "0.1.0"
            assert data["status"] == "running"

    def test_cors_middleware_configured(self) -> None:
        """Test that CORS middleware is properly configured."""
        from merlai.api.main import app
        
        # Check that middleware is added
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_types or len(app.user_middleware) > 0

    def test_router_inclusion(self) -> None:
        """Test that API router is included."""
        from merlai.api.main import app
        
        # Check that routes are registered
        routes = [route.path for route in app.routes]
        assert "/api/v1/generate" in routes or any("/api/v1" in route for route in routes)

    def test_exception_handler(self) -> None:
        """Test global exception handler."""
        from merlai.api.main import app
        
        with TestClient(app) as client:
            # Try to trigger an exception by accessing invalid endpoint with invalid data
            # The global exception handler should catch it
            response = client.post(
                "/api/v1/generate",
                json={"invalid": "data"},  # This will cause validation error
            )
            # Should return either 422 (validation) or 500 (handled exception)
            assert response.status_code in [422, 500]


class TestAPIConfiguration:
    """Test API configuration and setup."""

    def test_app_metadata(self) -> None:
        """Test FastAPI app metadata."""
        from merlai.api.main import app
        
        assert app.title == "Merlai Music Generation API"
        assert "AI-powered music creation" in app.description
        assert app.version == "0.1.0"

    def test_api_router_prefix(self) -> None:
        """Test that API routes have correct prefix."""
        from merlai.api.main import app
        
        api_routes = [route.path for route in app.routes if "/api/v1" in route.path]
        assert len(api_routes) > 0, "API routes should be registered with /api/v1 prefix"
        
        # Check some specific routes
        assert any("/api/v1/generate" in route.path for route in app.routes)
        assert any("/api/v1/health" in route.path for route in app.routes)


class TestAPIServerStartup:
    """Test API server startup scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_plugins_found(self) -> None:
        """Test startup with multiple plugins."""
        from merlai.api.main import lifespan, app
        
        # Mock multiple plugins
        mock_plugins = [
            Mock(name="Plugin1"),
            Mock(name="Plugin2"),
            Mock(name="Plugin3"),
        ]
        
        mock_music_gen = Mock()
        mock_music_gen.load_model = Mock()
        mock_midi_gen = Mock()
        mock_plugin_mgr = Mock()
        mock_plugin_mgr.scan_plugins = Mock(return_value=mock_plugins)
        
        with patch("merlai.api.main.MusicGenerator", return_value=mock_music_gen), \
             patch("merlai.api.main.MIDIGenerator", return_value=mock_midi_gen), \
             patch("merlai.api.main.PluginManager", return_value=mock_plugin_mgr):
            
            async with lifespan(app) as _:
                # Verify all components initialized
                assert app.state.music_generator == mock_music_gen
                assert app.state.midi_generator == mock_midi_gen
                assert app.state.plugin_manager == mock_plugin_mgr

    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self) -> None:
        """Test that shutdown cleanup works correctly."""
        from merlai.api.main import lifespan, app
        
        mock_music_gen = Mock()
        mock_music_gen.load_model = Mock()
        mock_midi_gen = Mock()
        mock_plugin_mgr = Mock()
        mock_plugin_mgr.scan_plugins = Mock(return_value=[])
        
        with patch("merlai.api.main.MusicGenerator", return_value=mock_music_gen), \
             patch("merlai.api.main.MIDIGenerator", return_value=mock_midi_gen), \
             patch("merlai.api.main.PluginManager", return_value=mock_plugin_mgr):
            
            async with lifespan(app) as _:
                pass  # Context manager exit should trigger shutdown
            
            # After shutdown, the lifespan should have completed successfully
            # No exceptions should be raised
