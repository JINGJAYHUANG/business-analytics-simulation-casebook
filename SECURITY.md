# Security policy

This project processes local files and produces local reports. It does not require network access or credentials.

## Supported version

Security fixes are accepted for the latest released minor version.

## Reporting

Open a private GitHub security advisory for vulnerabilities involving path traversal, unsafe file replacement, arbitrary command execution, HTML injection, manifest bypass, or leakage of non-synthetic data.

## Trust boundary

- The verifier detects changes after a run bundle is generated.
- It does not prove that original source data was truthful.
- The CLI does not sandbox untrusted files beyond its explicit parsers.
- Never use real sensitive data in a public clone without separate access controls.
