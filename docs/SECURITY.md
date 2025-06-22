# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| 0.9.x   | :white_check_mark: |
| 0.8.x   | :x:                |
| < 0.8   | :x:                |

## Reporting a Vulnerability

We take the security of Merlai seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Reporting Process

1. **DO NOT** create a public GitHub issue for the vulnerability
2. **DO** create a private security advisory on GitHub
3. **DO** include detailed information about the vulnerability
4. **DO** provide steps to reproduce the issue

### What to Include in Your Report

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Environment**: OS, Python version, Merlai version
- **Proof of Concept**: If possible, include a proof of concept
- **Suggested Fix**: If you have ideas for fixing the issue

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 1 week
- **Resolution**: Depends on severity and complexity

### Severity Levels

- **Critical**: Immediate action required, potential for data breach or system compromise
- **High**: Significant security impact, should be addressed quickly
- **Medium**: Moderate security impact, should be addressed in next release
- **Low**: Minor security impact, can be addressed in future releases

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest stable version
2. **Secure Environment**: Run in a secure, isolated environment
3. **Input Validation**: Validate all input data before processing
4. **Network Security**: Use HTTPS for API communications
5. **Access Control**: Implement proper authentication and authorization

### For Developers

1. **Dependency Management**: Regularly update dependencies
2. **Code Review**: All code changes must be reviewed
3. **Security Testing**: Include security tests in CI/CD
4. **Input Sanitization**: Always sanitize user inputs
5. **Error Handling**: Don't expose sensitive information in error messages

### For Contributors

1. **Security Review**: Security-focused code review for all changes
2. **Vulnerability Scanning**: Run security scans on dependencies
3. **Secure Coding**: Follow secure coding practices
4. **Documentation**: Document security considerations

## Security Features

### Current Security Measures

- **Input Validation**: Pydantic models for request validation
- **Type Safety**: mypy for type checking
- **Dependency Scanning**: Regular dependency vulnerability checks
- **Container Security**: Minimal container images with security updates
- **API Security**: Rate limiting and input sanitization

### Planned Security Enhancements

- [ ] Authentication and authorization system
- [ ] API key management
- [ ] Request signing and verification
- [ ] Audit logging
- [ ] Encryption at rest
- [ ] Secure plugin loading

## Disclosure Policy

When a security vulnerability is discovered:

1. **Private Fix**: Fix the vulnerability privately
2. **Testing**: Thoroughly test the fix
3. **Release**: Release a security update
4. **Disclosure**: Publicly disclose the vulnerability after users have had time to update
5. **Documentation**: Update security documentation

## Security Contacts

- **Security Team**: Create a private security advisory on GitHub
- **Maintainer**: [@yoshitake945](https://github.com/yoshitake945)
- **PGP Key**: Available upon request

## Acknowledgments

We would like to thank all security researchers and contributors who help keep Merlai secure by responsibly reporting vulnerabilities.

---

**Note**: This security policy is a living document and will be updated as the project evolves. 