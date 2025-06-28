# Changelog

## ⚠️ Important Notice / 重要な注記

**Implementation Status / 実装状況:**
本プロジェクトは実装は完了していますが、**動作確認は未実施**です。

This project has been implemented but **has not been tested for functionality**.

**AI-Assisted Development / AIアシスト開発:**
この変更履歴は、AIコーディングアシスタントの支援を受けて作成されています。
開発者はプロジェクト管理に習熟しているわけではなく、AIの提案に基づいて履歴を記録しています。

This changelog was created with the assistance of AI coding tools.
The developer is not proficient in project management and relies on AI suggestions for changelog entries.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Enhanced AI model integration
- Real-time music generation
- Advanced plugin system
- Performance optimizations

## [0.1.2] - 2025-06-28

### Added
- GitHub Issue #24: Docker build PATH warnings documentation
- Comprehensive analysis of script installation warnings
- Multiple solution options for PATH configuration

### Changed
- **CI Pipeline Enhancement**: 
  - Improved Quick Check with proper outputs configuration
  - Enhanced job dependency management
  - Better error handling for pipeline execution
- **Documentation**: 
  - Added detailed issue tracking for Docker build improvements
  - Documented PATH warning solutions for next release

### Fixed
- CI pipeline not starting due to missing outputs section in quick-check job
- Job dependency issues in GitHub Actions workflow
- Pipeline execution flow optimization

### Performance
- **CI Pipeline Reliability**: Fixed pipeline startup issues
- **Development Workflow**: Improved job execution consistency

## [0.1.1] - 2025-01-XX

### Added
- Comprehensive CI/CD pipeline with GitHub Actions
- GitHub Container Registry integration for Docker images
- Automated Docker image building and pushing
- Slack notifications for CI/CD pipeline status
- Extensive test suite with unit, integration, and API tests
- Pre-commit hooks for code quality (black, flake8, mypy, isort)
- Release workflow for tagged releases
- Multi-architecture Docker support (CPU and GPU variants)

### Changed
- Improved error handling throughout the application
- Enhanced API response codes (proper 404 vs 500 handling)
- Optimized test performance with proper mocking
- Updated development environment configuration
- Optimized Dockerfile and significantly reduced image size (3.1GB → 2GB/450MB)
- Refactored Dockerfile structure: removed `cpu`, `optimized`, `debug`, and `multiarch` files; unified to `Dockerfile`, `Dockerfile.gpu`, and `Dockerfile.lightweight`
- Updated CI/CD pipeline to use the optimized Dockerfile
- Unified docker-compose.yml build targets to the current Dockerfile
- Updated documentation (README, DOCKER_OPTIMIZATION.md, etc.) to reflect the latest structure

### Fixed
- CLI test hanging issues by mocking heavy operations
- API error responses for missing AI models
- Docker build issues and casing warnings
- Integration test performance bottlenecks

### Removed
- Removed legacy Dockerfiles (`cpu`, `optimized`, `debug`, `multiarch`)

## [0.1.0] - 2025-06-27

### Added
- Initial release of Merlai AI music generation system
- FastAPI-based REST API
- Command-line interface (CLI)
- MIDI generation from melody input
- Harmony, bass, and drum generation
- Plugin management system
- Docker containerization support
- CPU-only Docker image for Apple Silicon
- Basic health and readiness endpoints
- Type-safe Python codebase with mypy
- Development environment setup script
- Comprehensive documentation

### Features
- **AI-Powered Music Generation**: Generate complementary music parts from melody
- **MIDI Export**: Export generated music as MIDI files
- **Plugin Management**: Scan and manage audio plugins
- **RESTful API**: FastAPI-based API for integration
- **CLI Interface**: Command-line interface for local development
- **Docker Support**: Containerized deployment with CPU/GPU support
- **Cloud Native**: Support for Docker, Podman, and containerd
- **Kubernetes Manifests**: Basic Kubernetes deployment manifests available
- **Multi-Architecture**: Support for AMD64, ARM64, and ARM32

### Technical Stack
- **AI/ML**: Python + PyTorch + Transformers
- **API**: FastAPI with async support
- **Type Safety**: mypy, pydantic, dataclasses
- **Infrastructure**: Docker (Kubernetes manifests available)
- **Development**: Pre-commit hooks, comprehensive testing

### Documentation
- README.md with setup and usage instructions
- ARCHITECTURE.md with technical design and roadmap
- OPERATIONS_GUIDE.md with cloud-native deployment guide
- API.md with comprehensive API documentation
- CONTRIBUTING.md with development guidelines

### Development Tools
- Python virtual environment setup
- Code quality tools (mypy, flake8, black, isort)
- Docker development environment
- Basic Kubernetes manifests for testing
- Pre-commit hooks for code quality

---

## Version History

### Version 0.1.2 (Current)
- **Status**: Alpha
- **Release Date**: 2025-06-28
- **Features**: CI/CD optimization, Docker improvements, development workflow enhancements
- **Target**: Improved development experience and deployment efficiency

### Version 0.1.1
- **Status**: Alpha
- **Release Date**: 2025-01-XX
- **Features**: CI/CD pipeline, Docker optimization, comprehensive testing
- **Target**: Production readiness and deployment automation

### Version 0.1.0
- **Status**: Alpha
- **Release Date**: 2025-06-27
- **Features**: Basic functionality implemented, internal testing phase
- **Target**: Development and internal validation

## Development Philosophy

This project is developed as open-source software with the following principles:

- **Transparency**: All development is done in the open
- **Community**: Welcomes contributions from the community
- **Learning**: Focuses on learning and experimentation
- **Practical**: Prioritizes working solutions over perfect architecture

## Contributing

This is an open-source project. Contributions are welcome and appreciated.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the API documentation in `docs/API.md`

## License

This project is open source. Please check the LICENSE file for details.

[Unreleased]: https://github.com/yoshitake945/Merlai/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/yoshitake945/Merlai/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/yoshitake945/Merlai/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/yoshitake945/Merlai/releases/tag/v0.1.0 