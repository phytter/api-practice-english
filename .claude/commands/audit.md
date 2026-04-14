
# your goal is to Audit Dependencies for Vulnerabilities

## Commands

### Run Security Audit
```bash
pip install safety
safety check
```

### Check for Outdated Packages
```bash
pip list --outdated
```

### Detailed Vulnerability Report
```bash
pip install bandit
bandit -r app/
```

### Check Requirements Files
```bash
safety check -r requirements.txt
safety check -r requirements/develop.txt
```

## Alternative Tools

**Using pip-audit** (recommended by Python Packaging Authority):
```bash
pip install pip-audit
pip-audit
```

**Using OWASP Dependency-Check**:
```bash
pip install owasp-dependency-check
dependency-check --project "api-practice-english" --scan .
```
