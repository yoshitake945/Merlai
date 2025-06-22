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

## Authentication

Currently, the API does not require authentication. Future versions will implement JWT-based authentication.

## Endpoints

### Health Check

#### GET /health

Check if the API server is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### Readiness Check

#### GET /ready

Check if the API server is ready to handle requests.

**Response:**
```json
{
  "status": "ready",
  "services": {
    "ai_model": "ready",
    "midi_generator": "ready",
    "plugin_manager": "ready"
  }
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
      "note": "C4",
      "duration": 1.0,
      "velocity": 80,
      "start_time": 0.0
    },
    {
      "note": "E4", 
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
  - `note` (string): Note name (e.g., "C4", "F#3")
  - `duration` (float): Note duration in seconds
  - `velocity` (integer, optional): MIDI velocity (0-127, default: 80)
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
  "status": "success",
  "midi_data": "base64_encoded_midi_data",
  "duration": 4.0,
  "tracks": {
    "melody": 1,
    "harmony": 2,
    "bass": 3,
    "drums": 10
  },
  "metadata": {
    "style": "pop",
    "tempo": 120,
    "key": "C",
    "generated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Invalid melody format",
  "details": "Melody must contain at least one note"
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
      "id": "plugin_001",
      "name": "Piano Plugin",
      "type": "instrument",
      "category": "piano",
      "version": "1.0.0",
      "path": "/plugins/piano.vst3"
    }
  ]
}
```

#### GET /plugins/{plugin_id}

Get detailed information about a specific plugin.

**Response:**
```json
{
  "id": "plugin_001",
  "name": "Piano Plugin",
  "type": "instrument",
  "category": "piano",
  "version": "1.0.0",
  "path": "/plugins/piano.vst3",
  "parameters": [
    {
      "name": "reverb",
      "type": "float",
      "min": 0.0,
      "max": 1.0,
      "default": 0.3
    }
  ],
  "presets": [
    {
      "name": "Concert Hall",
      "parameters": {
        "reverb": 0.8,
        "brightness": 0.6
      }
    }
  ]
}
```

#### POST /plugins/scan

Scan for new plugins in specified directories.

**Request Body:**
```json
{
  "directories": [
    "/Library/Audio/Plug-Ins/VST3",
    "/Library/Audio/Plug-Ins/Components"
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "scanned_plugins": 15,
  "new_plugins": 3,
  "errors": []
}
```

### Plugin Recommendations

#### POST /plugins/recommend

Get plugin recommendations based on music style and requirements.

**Request Body:**
```json
{
  "style": "electronic",
  "instrument": "lead",
  "mood": "energetic",
  "tempo": 140
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "plugin_id": "plugin_002",
      "name": "Synth Plugin",
      "score": 0.95,
      "reason": "Perfect for electronic lead sounds",
      "parameters": {
        "oscillator": "saw",
        "filter_cutoff": 0.7
      }
    }
  ]
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a JSON object with:
- `status`: "error"
- `message`: Human-readable error message
- `details`: Additional error details (optional)

## Rate Limiting

Currently, no rate limiting is implemented. Future versions will include rate limiting based on API keys.

## CORS

CORS is enabled for development. Production configuration will be more restrictive.

## Examples

### Generate Music with cURL

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "melody": [
      {"note": "C4", "duration": 1.0, "velocity": 80, "start_time": 0.0},
      {"note": "E4", "duration": 1.0, "velocity": 80, "start_time": 1.0},
      {"note": "G4", "duration": 1.0, "velocity": 80, "start_time": 2.0}
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
response = requests.post('http://localhost:8000/generate', json={
    'melody': [
        {'note': 'C4', 'duration': 1.0, 'velocity': 80, 'start_time': 0.0},
        {'note': 'E4', 'duration': 1.0, 'velocity': 80, 'start_time': 1.0}
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