# Merlai 🎵

**AI-powered music creation assistant that helps fill in missing notes using AI.**

You provide the main melody – Merlai complements the rest with MIDI-ready suggestions.

**注記 / Note:**
本プロジェクトのほぼ全てのコード、設計、ドキュメントは、AIコーディングアシスタント（例: OpenAI GPT-4, GitHub Copilot等）を活用して作成されています。
また、開発者は英語が堪能ではないため、英語表現に不自然な点や誤りが含まれる可能性があります。

Almost all code, design, and documentation in this project were created with the assistance of AI coding tools (e.g., OpenAI GPT-4, GitHub Copilot, etc.).
Also, the developer is not fluent in English, so there may be unnatural expressions or mistakes in English.

## 🚀 Features

- **AI-assisted harmony and rhythm completion** - Generate complementary parts based on your melody
- **MIDI export for DAW integration** - Seamless workflow with your favorite DAW
- **Lightning-fast draft generation** - Real-time AI suggestions
- **Extensible with external sound plugins** - Automatic plugin recommendations
- **GPU-accelerated processing** - Optimized for performance
- **Container-ready deployment** - Docker and Kubernetes support
- **Edge computing support** - Local GPU server deployment

## 🏗️ Architecture

### Technology Stack

- **AI/ML**: Python + PyTorch/TensorFlow + Transformers
- **Performance**: Rust (for critical audio processing)
- **API**: FastAPI with async support
- **Type Safety**: mypy, pydantic, dataclasses
- **Infrastructure**: Docker, Kubernetes, NVIDIA Container Runtime
- **Storage**: MinIO (S3-compatible), PostgreSQL, Redis

### System Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Auth Service  │
│   (React/Vue)   │◄──►│   (Kong/Nginx)  │◄──►│   (JWT/OAuth)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  MIDI Generator │    │  AI Orchestrator│    │  Plugin Manager │
│   (Rust)        │◄──►│   (Python)      │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Model Service  │    │  Training       │    │  Data Pipeline  │
│   (GPU)         │    │  Service        │    │   (ETL)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Installation

### Prerequisites

- Python 3.9+
- NVIDIA GPU (optional, for acceleration)
- Docker (for containerized deployment)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/merlai.git
   cd merlai
   ```

2. **Setup development environment**
   ```bash
   ./scripts/setup_dev.sh
   ```

3. **Activate virtual environment**
   ```bash
   source venv/bin/activate
   ```

4. **Run the development server**
   ```bash
   merlai serve --reload
   ```

## 📖 Usage

### Command Line Interface

Generate complementary music parts from a melody:

```bash
# Generate with sample melody
merlai generate --style pop --key C --tempo 120

# Generate from existing MIDI file
merlai generate -i input.mid -o output.mid --style rock

# Generate specific parts only
merlai generate --generate-harmony --generate-bass --no-generate-drums
```

Scan for available plugins:

```bash
# Scan default plugin directories
merlai scan-plugins

# Scan specific directory
merlai scan-plugins -d /path/to/plugins -o plugins.json
```

Get plugin recommendations:

```bash
merlai recommend-plugins --style electronic --instrument lead
```

### API Usage

Start the API server:

```bash
merlai serve --host 0.0.0.0 --port 8000
```

API endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Generate music
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "melody": [
      {"pitch": 60, "velocity": 80, "duration": 0.5, "start_time": 0.0},
      {"pitch": 62, "velocity": 80, "duration": 0.5, "start_time": 0.5}
    ],
    "style": "pop",
    "tempo": 120,
    "key": "C"
  }'
```

## 🐳 Docker Deployment

### CPU-only Image (Apple Silicon/Mac/Non-GPU Environments)

```bash
docker compose up --build merlai-cpu
```

- Use the `merlai-cpu` service for Apple Silicon or environments without a GPU.
- The `version` attribute in `docker-compose.yml` is deprecated and has been removed for compatibility.

### Debug Container

```bash
docker compose up --build merlai-debug
```
- The `merlai-debug` service supports the `--log-level` option for detailed logging.

### Run Instructions (Local / Container)

#### Local Execution

```bash
source venv/bin/activate
merlai serve --reload
```

#### Docker (CPU-only)

```bash
docker compose up --build merlai-cpu
```

- The server will be available at http://localhost:8000

### Production

```bash
# Build production image
docker build --target production -t merlai:latest .

# Run with GPU support
docker run --gpus all -p 8000:8000 merlai:latest
```

### Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods -n merlai
```

## 🎯 Edge Computing

Deploy Merlai as a local GPU server for composers:

### Benefits

- **Low Latency**: Real-time generation without network delays
- **Privacy**: Keep your music data local
- **Customization**: Personalize AI models for your style
- **Offline Work**: Generate music without internet connection

### Setup

```bash
# Build edge computing image
docker build --target gpu-inference -t merlai:edge .

# Run local GPU server
docker run --gpus all -p 8002:8000 \
  -v /path/to/models:/app/models \
  -v /path/to/data:/app/data \
  merlai:edge
```

## 🔧 Development

### Project Structure

```
merlai/
├── merlai/
│   ├── core/           # Core music generation logic
│   │   ├── music.py    # AI music generation
│   │   ├── midi.py     # MIDI processing
│   │   ├── plugins.py  # Plugin management
│   │   └── types.py    # Data structures
│   ├── api/            # FastAPI application
│   │   ├── main.py     # App configuration
│   │   └── routes.py   # API endpoints
│   └── cli.py          # Command-line interface
├── docker/             # Docker configurations
├── k8s/               # Kubernetes manifests
├── scripts/           # Setup and utility scripts
└── tests/             # Test suite
```

### Code Quality

```bash
# Run type checking
mypy merlai/

# Run linting
black merlai/
isort merlai/
flake8 merlai/

# Run tests
pytest tests/

# Run with coverage
pytest --cov=merlai tests/
```

### Adding New Features

1. **Music Generation**: Extend `MusicGenerator` class in `core/music.py`
2. **MIDI Processing**: Add methods to `MIDIGenerator` class in `core/midi.py`
3. **Plugin Support**: Enhance `PluginManager` in `core/plugins.py`
4. **API Endpoints**: Add routes in `api/routes.py`

## 🚀 Performance Optimization

### GPU Acceleration

- **TensorRT Optimization**: Automatic model optimization
- **Batch Processing**: Process multiple requests efficiently
- **Memory Management**: Efficient GPU memory usage

### Caching Strategy

- **Redis**: Cache generated results
- **CDN**: Distribute plugins and models
- **Local Cache**: Store frequent patterns

### Scalability

- **Horizontal Scaling**: Multiple GPU instances
- **Load Balancing**: Distribute requests across nodes
- **Auto-scaling**: Kubernetes HPA for demand-based scaling

## 🔮 Roadmap

### v0.1.0: Foundation
- [x] Basic CLI + MIDI generator
- [x] Docker containerization
- [x] Type-safe Python codebase
- [x] Plugin scanning system

### v0.2.0: AI Integration
- [ ] AI draft filler (melody, bass, drums)
- [ ] GPU-optimized inference
- [ ] Real-time generation API
- [ ] Plugin recommendation engine

### v0.3.0: Advanced Features
- [ ] Style transfer and adaptation
- [ ] Multi-track generation
- [ ] Advanced plugin integration
- [ ] DAW plugin development

### v1.0.0: Production Release
- [ ] Web-based GUI
- [ ] Cloud deployment
- [ ] Enterprise features
- [ ] Community plugin marketplace

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- PyTorch and Transformers for AI capabilities
- Pretty MIDI and MIDIUtil for MIDI processing
- FastAPI for the web framework
- Docker and Kubernetes communities

---

**Made with ❤️ for musicians and creators everywhere.**
