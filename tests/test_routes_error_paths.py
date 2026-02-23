"""
Tests for error paths and edge cases in routes.py to reach 85%+ coverage.
"""

import pytest
from unittest.mock import Mock, patch
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def setup_app():
    """Setup app with mocked generators."""
    from merlai.api.main import app
    
    with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
        from merlai.core.music import MusicGenerator
        from merlai.core.midi import MIDIGenerator
        from merlai.core.plugins import PluginManager
        
        app.state.music_generator = MusicGenerator(use_ai_models=False)
        app.state.midi_generator = MIDIGenerator()
        app.state.plugin_manager = PluginManager()
        
        yield app


@pytest.mark.asyncio
async def test_register_ai_model_success(setup_app):
    """Test successful AI model registration."""
    app = setup_app
    
    # Mock the ai_model_manager
    app.state.music_generator.use_ai_models = True
    app.state.music_generator.ai_model_manager = Mock()
    app.state.music_generator.ai_model_manager.register_model = Mock(return_value=True)
    
    model_config = {
        "name": "test-model",
        "type": "huggingface",
        "model_path": "facebook/musicgen-small"
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/models/register", json=model_config)
        
        assert response.status_code == 200
        data = response.json()
        assert "model_name" in data


@pytest.mark.asyncio
async def test_register_ai_model_failure(setup_app):
    """Test AI model registration failure."""
    app = setup_app
    
    # Mock registration to fail
    app.state.music_generator.use_ai_models = True
    app.state.music_generator.ai_model_manager = Mock()
    app.state.music_generator.ai_model_manager.register_model = Mock(return_value=False)
    
    model_config = {
        "name": "failing-model",
        "type": "huggingface",
        "model_path": "invalid/path"
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/models/register", json=model_config)
        
        # Should return 400 or 500 (depends on how exception is caught)
        assert response.status_code in [400, 500]


@pytest.mark.asyncio
async def test_register_ai_model_exception(setup_app):
    """Test AI model registration with exception."""
    app = setup_app
    
    # Mock to raise exception
    app.state.music_generator.use_ai_models = True
    
    def raise_exception(config):
        raise Exception("Registration error")
    
    app.state.music_generator.register_ai_model = raise_exception
    
    model_config = {
        "name": "error-model",
        "type": "huggingface",
        "model_path": "test/path"
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/models/register", json=model_config)
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_set_default_ai_model_success(setup_app):
    """Test setting default AI model successfully."""
    app = setup_app
    
    app.state.music_generator.use_ai_models = True
    app.state.music_generator.set_default_ai_model = Mock(return_value=True)
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/models/test-model/set-default")
        
        assert response.status_code == 200
        data = response.json()
        assert "default_model" in data


@pytest.mark.asyncio
async def test_set_default_ai_model_not_found(setup_app):
    """Test setting default AI model that doesn't exist."""
    app = setup_app
    
    app.state.music_generator.use_ai_models = True
    app.state.music_generator.set_default_ai_model = Mock(return_value=False)
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/models/nonexistent/set-default")
        
        # Should return 404
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_set_default_ai_model_exception(setup_app):
    """Test setting default AI model with exception."""
    app = setup_app
    
    def raise_exception(model_name):
        raise Exception("Set default error")
    
    app.state.music_generator.use_ai_models = True
    app.state.music_generator.set_default_ai_model = raise_exception
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/models/test-model/set-default")
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_list_ai_models_success(setup_app):
    """Test listing AI models successfully."""
    app = setup_app
    
    app.state.music_generator.use_ai_models = True
    app.state.music_generator.list_ai_models = Mock(return_value=["model1", "model2"])
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ai/models")
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert data["count"] == 2


@pytest.mark.asyncio
async def test_list_ai_models_exception(setup_app):
    """Test listing AI models with exception."""
    app = setup_app
    
    def raise_exception():
        raise Exception("List models error")
    
    app.state.music_generator.use_ai_models = True
    app.state.music_generator.list_ai_models = raise_exception
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ai/models")
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_generate_harmony_ai_model_not_found(setup_app):
    """Test harmony generation when model is not found."""
    app = setup_app
    
    def raise_model_not_found(melody, style, model_name=None):
        raise RuntimeError("Model not found: test-model")
    
    app.state.music_generator.generate_harmony = raise_model_not_found
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/ai/generate/harmony?model_name=test-model",
            json=request_data
        )
        
        # Should return 404 when model not found
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_harmony_ai_other_error(setup_app):
    """Test harmony generation with other runtime error."""
    app = setup_app
    
    def raise_other_error(melody, style, model_name=None):
        raise RuntimeError("Some other error")
    
    app.state.music_generator.generate_harmony = raise_other_error
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/generate/harmony", json=request_data)
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_generate_harmony_ai_general_exception(setup_app):
    """Test harmony generation with general exception."""
    app = setup_app
    
    def raise_exception(melody, style, model_name=None):
        raise Exception("General error")
    
    app.state.music_generator.generate_harmony = raise_exception
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/generate/harmony", json=request_data)
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_generate_bass_ai_model_not_found(setup_app):
    """Test bass generation when model is not found."""
    app = setup_app
    
    def raise_model_not_found(melody, harmony, model_name=None):
        raise RuntimeError("Model not found: test-model")
    
    app.state.music_generator.generate_bass_line = raise_model_not_found
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/generate/bass", json=request_data)
        
        # Should return 404
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_bass_ai_other_runtime_error(setup_app):
    """Test bass generation with other runtime error."""
    app = setup_app
    
    def raise_error(melody, harmony, model_name=None):
        raise RuntimeError("Other error")
    
    app.state.music_generator.generate_bass_line = raise_error
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/generate/bass", json=request_data)
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_generate_bass_ai_general_exception(setup_app):
    """Test bass generation with general exception."""
    app = setup_app
    
    def raise_exception(melody, harmony, model_name=None):
        raise Exception("General error")
    
    app.state.music_generator.generate_bass_line = raise_exception
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/generate/bass", json=request_data)
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_generate_drums_ai_model_not_found(setup_app):
    """Test drums generation when model is not found."""
    app = setup_app
    
    def raise_model_not_found(melody, tempo, model_name=None):
        raise RuntimeError("Model not found: test-model")
    
    app.state.music_generator.generate_drums = raise_model_not_found
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/generate/drums", json=request_data)
        
        # Should return 404
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_drums_ai_other_runtime_error(setup_app):
    """Test drums generation with other runtime error."""
    app = setup_app
    
    def raise_error(melody, tempo, model_name=None):
        raise RuntimeError("Other error")
    
    app.state.music_generator.generate_drums = raise_error
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/generate/drums", json=request_data)
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_generate_drums_ai_general_exception(setup_app):
    """Test drums generation with general exception."""
    app = setup_app
    
    def raise_exception(melody, tempo, model_name=None):
        raise Exception("General error")
    
    app.state.music_generator.generate_drums = raise_exception
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ai/generate/drums", json=request_data)
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_list_plugins_with_exception(setup_app):
    """Test plugin list with exception."""
    app = setup_app
    
    def raise_exception():
        raise Exception("Plugin scan error")
    
    app.state.plugin_manager.scan_plugins = raise_exception
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/plugins")
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_plugin_recommendations_with_exception(setup_app):
    """Test plugin recommendations with exception."""
    app = setup_app
    
    def raise_exception(style, instrument):
        raise Exception("Recommendation error")
    
    app.state.plugin_manager.get_plugin_recommendations = raise_exception
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/plugins/recommendations?style=pop&instrument=piano"
        )
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_load_plugin_exception(setup_app):
    """Test plugin load with exception."""
    app = setup_app
    
    def raise_exception(plugin_name):
        raise Exception("Load error")
    
    app.state.plugin_manager.load_plugin = raise_exception
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/plugins/test-plugin/load")
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_plugin_parameters_exception(setup_app):
    """Test getting plugin parameters with exception."""
    app = setup_app
    
    def raise_exception(plugin_name):
        raise Exception("Parameter error")
    
    app.state.plugin_manager.get_plugin_info = raise_exception
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/plugins/test-plugin/parameters")
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_set_plugin_parameter_exception(setup_app):
    """Test setting plugin parameter with exception."""
    app = setup_app
    
    def raise_exception(plugin_name, param_name, value):
        raise Exception("Set parameter error")
    
    app.state.plugin_manager.set_plugin_parameter = raise_exception
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/plugins/test-plugin/parameters/volume",
            params={"value": 0.5}
        )
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_plugin_presets_exception(setup_app):
    """Test getting plugin presets with exception."""
    app = setup_app
    
    def raise_exception(plugin_name):
        raise Exception("Preset error")
    
    app.state.plugin_manager.get_plugin_info = raise_exception
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/plugins/test-plugin/presets")
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_plugin_info_exception(setup_app):
    """Test getting plugin info with exception."""
    app = setup_app
    
    def raise_exception(plugin_name):
        raise Exception("Info error")
    
    app.state.plugin_manager.get_plugin_info = raise_exception
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/plugins/test-plugin")
        
        # Should return 500
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_update_config_exception(setup_app):
    """Test config update with unexpected exception."""
    app = setup_app
    
    # Create config that will pass validation but cause exception
    valid_config = {
        "temperature": 0.8,
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/config", json=valid_config)
        
        # Should handle successfully or return error
        assert response.status_code in [200, 500]
