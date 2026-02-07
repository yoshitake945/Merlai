"""
Additional tests to improve routes.py coverage.

This file focuses on covering edge cases and error paths in API routes.
"""

import base64
import pytest
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_generators():
    """Mock the generators for testing."""
    with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
        from merlai.core.music import MusicGenerator
        from merlai.core.midi import MIDIGenerator
        from merlai.core.plugins import PluginManager
        
        music_gen = MusicGenerator(use_ai_models=False)
        midi_gen = MIDIGenerator()
        plugin_mgr = PluginManager()
        
        yield {
            "music_generator": music_gen,
            "midi_generator": midi_gen,
            "plugin_manager": plugin_mgr,
        }


@pytest.mark.asyncio
async def test_generate_with_only_melody_no_other_parts(mock_generators):
    """Test generation with only melody, no harmony/bass/drums."""
    from merlai.api.main import app
    
    # Inject mocked generators
    app.state.music_generator = mock_generators["music_generator"]
    app.state.midi_generator = mock_generators["midi_generator"]
    app.state.plugin_manager = mock_generators["plugin_manager"]
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
        "generate_harmony": False,
        "generate_bass": False,
        "generate_drums": False,
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_generate_with_harmony_only(mock_generators):
    """Test generation with harmony only."""
    from merlai.api.main import app
    
    app.state.music_generator = mock_generators["music_generator"]
    app.state.midi_generator = mock_generators["midi_generator"]
    app.state.plugin_manager = mock_generators["plugin_manager"]
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
        "generate_harmony": True,
        "generate_bass": False,
        "generate_drums": False,
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("merlai.core.music.AutoTokenizer"), \
             patch("merlai.core.music.AutoModelForCausalLM"):
            response = await client.post("/api/v1/generate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


@pytest.mark.asyncio
async def test_generate_with_drums_only(mock_generators):
    """Test generation with drums only."""
    from merlai.api.main import app
    
    app.state.music_generator = mock_generators["music_generator"]
    app.state.midi_generator = mock_generators["midi_generator"]
    app.state.plugin_manager = mock_generators["plugin_manager"]
    
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
        "generate_harmony": False,
        "generate_bass": False,
        "generate_drums": True,
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_update_config_with_invalid_keys(mock_generators):
    """Test updating config with invalid keys."""
    from merlai.api.main import app
    
    app.state.music_generator = mock_generators["music_generator"]
    app.state.midi_generator = mock_generators["midi_generator"]
    app.state.plugin_manager = mock_generators["plugin_manager"]
    
    invalid_config = {
        "invalid_key": "value",
        "another_invalid": 123
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/config", json=invalid_config)
        
        # Should return 400 for invalid keys
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_config_with_invalid_temperature_type(mock_generators):
    """Test updating config with invalid temperature type."""
    from merlai.api.main import app
    
    app.state.music_generator = mock_generators["music_generator"]
    app.state.midi_generator = mock_generators["midi_generator"]
    app.state.plugin_manager = mock_generators["plugin_manager"]
    
    invalid_config = {
        "temperature": "not a number"  # Should be float
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/config", json=invalid_config)
        
        # Should return 422 for invalid types
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_config_with_invalid_max_length_type(mock_generators):
    """Test updating max_length with non-integer."""
    from merlai.api.main import app
    
    app.state.music_generator = mock_generators["music_generator"]
    app.state.midi_generator = mock_generators["midi_generator"]
    app.state.plugin_manager = mock_generators["plugin_manager"]
    
    invalid_config = {
        "max_length": 123.45  # Should be int, not float
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/config", json=invalid_config)
        
        # Should return 422
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_config_partial_update(mock_generators):
    """Test partial config update."""
    from merlai.api.main import app
    
    app.state.music_generator = mock_generators["music_generator"]
    app.state.midi_generator = mock_generators["midi_generator"]
    app.state.plugin_manager = mock_generators["plugin_manager"]
    
    partial_config = {
        "temperature": 0.75,
        "top_p": 0.95
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/config", json=partial_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Configuration updated successfully"
