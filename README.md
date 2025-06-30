# Merlai 🎵

[![CI](https://github.com/yoshitake945/Merlai/actions/workflows/ci.yml/badge.svg)](https://github.com/yoshitake945/Merlai/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/yoshitake945/Merlai/branch/main/graph/badge.svg)](https://codecov.io/gh/yoshitake945/Merlai)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**AI-powered music creation assistant that helps fill in missing notes using AI.**

You provide the main melody – Merlai complements the rest with MIDI-ready suggestions.

## ⚠️ Important Notice / 重要な注記

**AI-Assisted Development / AIアシスト開発:**
本プロジェクトのほぼすべてのコード、設計、ドキュメントは、AIコーディングアシスタント（例: OpenAI GPT-4, GitHub Copilot等）を活用して作成されています。
開発者はPythonやその他の技術スタックに習熟しているわけではなく、AIの支援に大きく依存して開発を進めています。

Almost all code, design, and documentation in this project were created with the assistance of AI coding tools (e.g., OpenAI GPT-4, GitHub Copilot, etc.).
The developer is not proficient in Python or other technical stacks and heavily relies on AI assistance for development.

**Implementation Status / 実装状況:**
本プロジェクトは実装は完了していますが、**動作確認は未実施**です。

This project has been implemented but **has not been tested for functionality**.

**Language Proficiency / 言語能力:**
開発者は英語が堪能ではないため、英語表現に不自然な点や誤りが含まれる可能性があります。
技術的な議論や改善提案については、日本語でのコミュニケーションを推奨します。
英語学習中であり、コミュニティからの理解と支援をいただけると幸いです。

The developer is currently learning English and appreciates understanding and support from the community.

**Code Quality / コード品質:**
AI生成コードのため、ベストプラクティスに従っていない部分や、最適化されていない箇所が存在する可能性があります。
プロダクション環境での使用前に、十分なテストとレビューを推奨します。

As this is AI-generated code, there may be parts that don't follow best practices or are not optimized.
Thorough testing and review are recommended before use in production environments.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/yoshitake945/Merlai.git
cd Merlai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Docker Images

Merlai provides optimized Docker images for different use cases:

### Available Images

- **Lightweight Version** (~450MB): `ghcr.io/your-org/merlai:latest`
  - Minimal dependencies for basic music generation
  - Suitable for development and testing
  - 85% size reduction from original

- **GPU Version**: `ghcr.io/your-org/merlai:latest-gpu`
  - Full AI model support with GPU acceleration
  - Requires NVIDIA Docker runtime
  - For production AI-powered music generation

### Quick Start

```bash
# Lightweight version (recommended for most users)
docker run -p 8000:8000 ghcr.io/your-org/merlai:latest

# GPU version (requires NVIDIA Docker)
docker run --gpus all -p 8000:8000 ghcr.io/your-org/merlai:latest-gpu
```

### Image Tags

- `latest` - Latest lightweight version
- `v0.1.2` - Specific version (lightweight)
- `v0.1.2-gpu` - Specific version with GPU support

**Note**: Optimized CPU version (~2GB) is temporarily unavailable due to CI/CD constraints. The lightweight version provides excellent performance for most use cases.

### Usage

#### Docker (Recommended)
```bash
# Build from source (GitHub Container Registry images coming soon)
docker build -f docker/Dockerfile -t merlai:latest .

# Run the container
docker run -p 8000:8000 merlai:latest

# For GPU support (requires NVIDIA Docker)
docker build -f docker/Dockerfile.gpu -t merlai:gpu .
docker run --gpus all -p 8000:8000 merlai:gpu
```

#### CLI
```bash
# Start the API server
merlai serve

# Generate music from melody
merlai generate --melody "C4,1.0;E4,1.0;G4,1.0" --style pop --key C
```

#### API
```bash
# Health check
curl http://localhost:8000/health

# Generate music
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "melody": [
      {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0}
    ],
    "style": "pop",
    "key": "C"
  }'
```

## 📚 Documentation

詳細なドキュメントは [`docs/`](docs/) フォルダにあります：
Detailed documentation is available in the [`docs/`](docs/) folder:

- **[📖 Documentation Overview](docs/README.md)** - ドキュメント一覧 / Documentation index
- **[🏗️ Architecture](docs/ARCHITECTURE.md)** - システム設計 / System design
- **[🔌 API Reference](docs/API.md)** - API仕様書 / API specification
- **[🚀 Operations Guide](docs/OPERATIONS_GUIDE.md)** - 運用ガイド / Operations guide
- **[🔧 Troubleshooting](docs/TROUBLESHOOTING.md)** - トラブルシューティング / Troubleshooting guide

## 🎯 Features

- **AI-Powered Music Generation**: Generate harmony, bass, and drums from melody
- **Multiple Styles**: Support for pop, rock, jazz, electronic, classical
- **MIDI Output**: Direct MIDI file generation
- **Plugin Integration**: External sound plugin management
- **RESTful API**: Easy integration with other applications
- **CLI Interface**: Command-line tool for quick music generation

## 🏗️ Architecture

Merlai follows a modular architecture with clear separation of concerns:

- **Core Music Engine**: Handles music theory and generation
- **AI Models**: Manages different AI models for music generation
- **MIDI Processing**: Handles MIDI file creation and manipulation
- **Plugin System**: Manages external sound plugins
- **API Layer**: RESTful API for external integration

For detailed architecture information, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🔧 Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=merlai

# Run specific test file
pytest tests/test_api.py
```

### Code Quality
```bash
# Type checking
mypy merlai/

# Linting
flake8 merlai/

# Formatting
black merlai/
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Run tests: `pytest`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yoshitake945/Merlai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yoshitake945/Merlai/discussions)
- **Documentation**: [docs/](docs/)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 🙏 Acknowledgments

- AI coding assistants for development support
- Open source community for libraries and tools
- Music theory resources and research
- Contributors and users of Merlai

---

**Note**: This project is actively developed with AI assistance. Please be patient with the developer's English learning process and provide constructive feedback.
