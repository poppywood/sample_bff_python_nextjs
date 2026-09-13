# Copilot Instructions

## General Code Review Standards

### Purpose
These instructions guide Copilot code review across all files in this repository.

### Security Critical Issues
- Check for hardcoded secrets, API keys, or credentials
- Look for SQL injection and XSS vulnerabilities
- Verify proper input validation and sanitization (checked for injection attacks)
- Review authentication and authorization logic
- Check for SSRS and CSRF vulnerabilities 
- Check for possible timing attacks and side-channel vulnerabilities
- Check for all known vulnerabilities in dependencies and libraries
- Check OWASP Top 10 vulnerabilities relevant to the codebase:
  - A01:2025 - Broken Access Control
  - A02:2025 - Security Misconfiguration
  - A03:2025 - Software Supply Chain Failures
  - A04:2025 - Cryptographic Failures
  - A05:2025 - Injection
  - A06:2025 - Insecure Design
  - A07:2025 - Authentication Failures
  - A08:2025 - Software or Data Integrity Failures
  - A09:2025 - Security Logging and Alerting Failures
  - A10:2025 - Mishandling of Exceptional Conditions

### Performance Red Flags
- Identify N+1 database query problems
- Spot inefficient loops and algorithmic issues
- Check for memory leaks and resource cleanup
- Review caching opportunities for expensive operations

### Code Quality Essentials
- Functions should be focused and appropriately sized (under 50 lines)
- Use clear, descriptive naming conventions
- Ensure proper error handling throughout
- Remove dead code and unused imports
- Generate validator documentation to be human-readable and non-technical; summarize sanitizer checks and present whitelist constraints in plain language (e.g., ASC/DESC).

### Review Style
- Be specific and actionable in feedback
- Explain the "why" behind recommendations
- Acknowledge good patterns when you see them
- Ask clarifying questions when code intent is unclear

Always prioritize security vulnerabilities and performance issues that could impact users.
