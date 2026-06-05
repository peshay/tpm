# Contributing

Thanks for contributing to tpm.py.

## Requirements
- Python 3.x
- `pip`

## Development Setup
```bash
pip install -e .
pip install -r tests/requirements.txt
pre-commit install --install-hooks
pytest
```

## Branch and Commit Guidelines
- Create a feature branch from `master`.
- Use Conventional Commits, e.g.:
  - `feat: add file upload endpoint`
  - `fix: handle locked password unlock reason`
  - `docs: document v5 endpoints`

## Pull Request Checklist
- Keep changes focused and minimal.
- Add or update tests for behavior changes.
- Update docs when behavior changes.
- Run `pre-commit run --all-files` before opening a PR.
- Ensure CI is green.

## Security and Secrets
- Never commit real TeamPasswordManager credentials, keys, or password data.
- For vulnerabilities, follow `SECURITY.md`.

## Review Policy
- All PRs require human review before merge.
- AI-assisted changes are welcome, but maintainers are responsible for final correctness.
