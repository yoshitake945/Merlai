# Merlai API Documentation

## ⚠️ Important Notice / 重要な注記

**AI-Assisted Development / AIアシスト開発:**
このAPI仕様書は、AIコーディングアシスタントの支援を受けて作成されています。
開発者はAPI設計に習熟しているわけではなく、AIの提案に基づいて仕様を策定しています。
実装前に十分な技術検証とレビューを推奨します。

This API documentation was created with the assistance of AI coding tools.
The developer is not proficient in API design and relies on AI suggestions for specification decisions.
Thorough technical validation and review are recommended before implementation.

## Overview

Merlai provides a RESTful API for AI-powered music generation. The API allows you to generate complementary music parts (harmony, bass, drums) from a given melody.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://api.merlai.com` (planned)

Most endpoints are versioned under `/api/v1`:
- Development API base: `http://localhost:8000/api/v1`

## Authentication

Currently, the API does not require authentication. Future versions will implement JWT-based authentication.

## Endpoints

Unless noted, endpoints below are under `/api/v1`.

### Health Check

#### GET /health

Check if the API server is running.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "plugins_loaded": 0
}
```

### Readiness Check

#### GET /ready

Check if the API server is ready to handle requests.

**Response:**
```json
{
  "status": "ready"
}
```

### Music Generation

#### POST /generate

Generate complementary music parts from a melody.

**Request Body:**
```json
{
  "melody": [
    {
      "pitch": 60,
      "duration": 1.0,
      "velocity": 80,
      "start_time": 0.0
    },
    {
      "pitch": 64,
      "duration": 1.0,
      "velocity": 80,
      "start_time": 1.0
    }
  ],
  "style": "pop",
  "tempo": 120,
  "key": "C",
  "generate_harmony": true,
  "generate_bass": true,
  "generate_drums": true
}
```

**Parameters:**
- `melody` (array): Array of note objects
  - `pitch` (integer): MIDI pitch (0-127)
  - `duration` (float): Note duration in seconds
  - `velocity` (integer): MIDI velocity (0-127)
  - `start_time` (float): Start time in seconds
- `style` (string, optional): Music style ("pop", "rock", "jazz", "classical", default: "pop")
- `tempo` (integer, optional): Tempo in BPM (default: 120)
- `key` (string, optional): Key signature (default: "C")
- `generate_harmony` (boolean, optional): Generate harmony parts (default: true)
- `generate_bass` (boolean, optional): Generate bass parts (default: true)
- `generate_drums` (boolean, optional): Generate drum parts (default: true)

**Response:**
```json
{
  "success": true,
  "harmony": [
    {
      "root": 60,
      "chord_type": "major",
      "duration": 1.0,
      "start_time": 0.0,
      "voicing": [60, 64, 67]
    }
  ],
  "bass_line": [
    {
      "pitch": 48,
      "velocity": 64,
      "duration": 1.0,
      "start_time": 0.0,
      "channel": 0
    }
  ],
  "drums": [
    {
      "pitch": 36,
      "velocity": 80,
      "duration": 0.25,
      "start_time": 0.0,
      "channel": 9
    }
  ],
  "midi_data": "base64_encoded_midi_data",
  "duration": 4.0,
  "error_message": null
}
```

**Error Response:**
```json
{
  "detail": "Melody cannot be empty. Please provide at least one note."
}
```

### Plugin Management

#### GET /plugins

List available plugins.

**Response:**
```json
{
  "plugins": [
    {
      "name": "Piano Plugin",
      "version": "1.0.0",
      "manufacturer": "Unknown",
      "plugin_type": "VST3",
      "category": "Synth",
      "file_path": "/plugins/piano.vst3",
      "is_loaded": false
    }
  ],
  "count": 1
}
```

#### GET /plugins/{plugin_name}

Get detailed information about a specific plugin.

**Response:**
```json
{
  "name": "Piano Plugin",
  "version": "1.0.0",
  "manufacturer": "Unknown",
  "plugin_type": "VST3",
  "category": "Synth",
  "file_path": "/plugins/piano.vst3",
  "is_loaded": false,
  "description": "",
  "parameters": ["Volume", "Cutoff"],
  "presets": ["Default", "Bright"]
}
```

#### GET /plugins/{plugin_name}/parameters

Get plugin parameters.

**Response:**
```json
{
  "plugin_name": "Piano Plugin",
  "parameters": [
    {
      "name": "Volume",
      "value": 0.5,
      "min_value": 0.0,
      "max_value": 1.0,
      "default_value": 0.5,
      "unit": "dB",
      "is_automated": false
    }
  ]
}
```

#### POST /plugins/{plugin_name}/parameters/{parameter_name}

Set a plugin parameter (query parameter `value`).

**Example:**
`POST /api/v1/plugins/Piano%20Plugin/parameters/Volume?value=0.7`

**Response:**
```json
{
  "message": "Parameter Volume set to 0.7 for plugin Piano Plugin"
}
```

#### GET /plugins/{plugin_name}/presets

Get plugin presets.

**Response:**
```json
{
  "plugin_name": "Piano Plugin",
  "presets": [
    {
      "name": "Default",
      "parameters": {
        "Volume": 0.5,
        "Cutoff": 0.7
      },
      "category": "Default"
    }
  ]
}
```

#### POST /plugins/{plugin_name}/load

Load a plugin into memory.

**Response:**
```json
{
  "message": "Plugin Piano Plugin loaded successfully"
}
```

### Plugin Recommendations

#### GET /plugins/recommendations

Get plugin recommendations using query parameters `style` and `instrument`.

**Example:**
`GET /api/v1/plugins/recommendations?style=electronic&instrument=lead`

**Response:**
```json
{
  "style": "electronic",
  "instrument": "lead",
  "recommendations": [
    {
      "name": "Synth Plugin",
      "manufacturer": "Unknown",
      "plugin_type": "VST3",
      "category": "Synth",
      "file_path": "/plugins/synth.vst3"
    }
  ]
}
```

### AI Model Management

#### POST /ai/models/register

Register a new AI model.

**Request Body:**
```json
{
  "name": "default-hf",
  "type": "huggingface",
  "model_path": "microsoft/DialoGPT-medium"
}
```

**Response:**
```json
{
  "message": "AI model default-hf registered successfully",
  "model_name": "default-hf",
  "model_type": "huggingface"
}
```

#### POST /ai/models/{model_name}/set-default

Set the default AI model.

**Response:**
```json
{
  "message": "Default AI model set to default-hf",
  "default_model": "default-hf"
}
```

#### GET /ai/models

List registered AI models.

**Response:**
```json
{
  "models": ["default-hf"],
  "count": 1,
  "ai_models_enabled": true
}
```

#### POST /ai/generate/harmony

Generate harmony using AI models (optional query parameter `model_name`).

**Response:**
```json
{
  "harmony": [
    {
      "root": 60,
      "chord_type": "major",
      "duration": 1.0,
      "start_time": 0.0,
      "voicing": [60, 64, 67]
    }
  ],
  "success": true
}
```

#### POST /ai/generate/bass

Generate bass using AI models (optional query parameter `model_name`).

**Response:**
```json
{
  "bass_line": [
    {
      "pitch": 48,
      "velocity": 64,
      "duration": 1.0,
      "start_time": 0.0,
      "channel": 0
    }
  ],
  "success": true
}
```

#### POST /ai/generate/drums

Generate drums using AI models (optional query parameter `model_name`).

**Response:**
```json
{
  "drums": [
    {
      "pitch": 36,
      "velocity": 80,
      "duration": 0.25,
      "start_time": 0.0,
      "channel": 9
    }
  ],
  "success": true
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses follow FastAPI defaults and include a JSON object with:
- `detail`: Human-readable error message

## Rate Limiting

Currently, no rate limiting is implemented. Future versions will include rate limiting based on API keys.

## CORS

CORS is enabled for development. Production configuration will be more restrictive.

## Examples

### Generate Music with cURL

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "melody": [
      {"pitch": 60, "duration": 1.0, "velocity": 80, "start_time": 0.0},
      {"pitch": 64, "duration": 1.0, "velocity": 80, "start_time": 1.0},
      {"pitch": 67, "duration": 1.0, "velocity": 80, "start_time": 2.0}
    ],
    "style": "pop",
    "tempo": 120
  }'
```

### Generate Music with Python

```python
import requests
import base64

# Generate music
response = requests.post('http://localhost:8000/api/v1/generate', json={
    'melody': [
        {'pitch': 60, 'duration': 1.0, 'velocity': 80, 'start_time': 0.0},
        {'pitch': 64, 'duration': 1.0, 'velocity': 80, 'start_time': 1.0}
    ],
    'style': 'pop',
    'tempo': 120
})

if response.status_code == 200:
    data = response.json()
    
    # Save MIDI file
    midi_data = base64.b64decode(data['midi_data'])
    with open('output.mid', 'wb') as f:
        f.write(midi_data)
    
    print(f"Generated music saved as output.mid")
else:
    print(f"Error: {response.json()}")
```

## Versioning

API versioning is planned for future releases. The current version is v1.0.0.

## Changelog

### v1.0.0
- Initial API release
- Basic music generation
- Plugin management
- Health and readiness endpoints 