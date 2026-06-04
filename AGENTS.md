# AGENTS

This repository accepts AI-assisted contributions.

## Guardrails
- Keep changes small and reviewable.
- Treat all credential and password-handling paths as sensitive; do not change their behavior without explicit intent.
- Do not commit secrets, API keys, or password data.
- Run the public artifact hygiene guard (pre-commit) before publishing PR text, commits, or docs.

## Required Human Checks
- Review every AI-generated change before merge.
- Validate authentication (password and key-based) and request handling.
- Ensure docs match implemented methods.

## Attribution
A concise note such as "AI-assisted" in the PR description is recommended for transparency.
