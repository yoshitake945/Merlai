# Contributing to Merlai

Thank you for your interest in contributing to Merlai! 🎵

## 👨‍💻 Project Maintainer

**Yoshitake Asano**
- GitHub: [@yoshitake945](https://github.com/yoshitake945)
- Role: Product Design & Architecture
- Contact: Create an issue on GitHub for questions or support

## 🤖 AI-Assisted Development Notice

This project is developed with significant assistance from AI coding tools including:
- **Cursor** (AI-powered code editor)
- **OpenAI GPT-4** (via Cursor integration)
- **OpenAI ChatGPT** (for ideation and concept development)
- **GitHub Copilot** (when available)

The human developer focuses on:
- Product vision and user experience
- System architecture and technology choices
- Project direction and feature prioritization
- Overall project management

AI tools handle:
- Code implementation and technical details
- Library integration and API design
- Documentation and testing
- Code quality and optimization

## 🌟 How to Contribute

### Before You Start

1. **Check existing issues**: Look for existing issues or discussions
2. **Discuss your idea**: Create an issue to discuss your proposed changes
3. **Understand the project**: Review the architecture and documentation

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yoshitake945/merlai.git
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

4. **Run tests**
   ```bash
   pytest
   ```

## 📋 Branch Strategy

- `main`: Stable release branch (vX.Y.Z tags)
- `dev`: Development integration branch
- `feature/xxx`: New feature branches based on `dev`
- `release/vX.Y.Z`: Release preparation branches
- `hotfix/xxx`: Emergency fixes, from `main`

Please submit pull requests to the `dev` branch unless otherwise instructed.

## 🎯 Contribution Areas

### High Priority
- **Bug fixes**: Critical issues and bugs
- **Documentation**: Improving docs and examples
- **Testing**: Adding tests and improving coverage
- **Performance**: Optimizations and improvements

### Medium Priority
- **New features**: Well-planned and discussed features
- **API improvements**: Better API design and usability
- **Plugin system**: Enhanced plugin management

### Low Priority
- **Experimental features**: Proof of concepts
- **UI/UX improvements**: Interface enhancements
- **Advanced AI features**: Complex AI integrations

## 📝 Code Style

- Follow PEP8 (Black recommended)
- Use type hints with mypy
- Write docstrings with Google-style format
- Keep functions small and focused
- Add comments for complex logic

### Pre-commit Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

## 🧪 Testing

- Write tests for new features
- Ensure all tests pass
- Add integration tests for API endpoints
- Test with different Python versions

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=merlai

# Run specific test file
pytest tests/test_music.py
```

## 📚 Documentation

- Update README.md for user-facing changes
- Add API documentation for new endpoints
- Update architecture docs for system changes
- Include examples and use cases

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment**: OS, Python version, dependencies
2. **Steps to reproduce**: Clear, step-by-step instructions
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Additional context**: Logs, screenshots, etc.

## 💡 Feature Requests

When requesting features, please include:

1. **Problem description**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Use cases**: Who would benefit from this?
4. **Alternatives considered**: What other approaches were considered?

## 🤝 Pull Request Process

1. **Create a feature branch** from `dev`
2. **Make your changes** following the code style
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Run tests** and ensure they pass
6. **Submit a pull request** to `dev`
7. **Wait for review** and address feedback

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other (please describe)

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Documentation
- [ ] README updated
- [ ] API docs updated
- [ ] Architecture docs updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No breaking changes
- [ ] Dependencies updated if needed
```

## 🏷️ Release Process

1. **Feature freeze**: Stop adding new features
2. **Testing phase**: Comprehensive testing
3. **Documentation review**: Update all docs
4. **Release branch**: Create release/vX.Y.Z
5. **Tag release**: Create git tag
6. **Deploy**: Update main branch
7. **Announce**: Update release notes

## 📞 Communication

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for general questions
- **Direct contact**: Create an issue mentioning @yoshitake945

### Language Support / 言語サポート

**English**: The developer is currently learning English. While English communication is welcome, there may be some unnatural expressions or mistakes. Please be patient and understanding.

**日本語**: 開発者は日本語が母語です。技術的な議論や詳細な説明については、日本語でのコミュニケーションを推奨します。

**Multilingual Support**: Feel free to communicate in either English or Japanese. The developer appreciates support from the community while learning English.

## 🙏 Acknowledgments

Thank you for contributing to Merlai! Your contributions help make AI-assisted music creation more accessible to everyone.

---

**Note**: This project embraces AI-assisted development. Feel free to use AI tools in your contributions, but please ensure human review and understanding of all changes.
