# Repository structure, packaging, tests, CI audit

Scope: `peshay/tpm`

## Findings
- Repo is a single-module package: `tpm.py`, `setup.py`, `requirements.txt`, `tests/`.
- No `pyproject.toml` yet; packaging still uses `distutils.core.setup` in `setup.py`.
- Runtime dependencies are legacy-pinned (`requests<=2.26.0`, `future`, `urllib3`).
- CI is Travis-based, targets Python 3.6-3.9 plus nightly, installs with `python setup.py -q install`, and runs `nose2 -v --with-coverage`.
- Tests are fixture-driven under `tests/resources/` and cover API v4/v5 behavior.
- Resolved: the request layer now verifies TLS certificates by default (`verify=True`), configurable per client via the `verify` keyword.

## Risks / gaps
- ~~Packaging path is outdated for current Python tooling.~~ Resolved: migrated to `pyproject.toml`.
- ~~CI/runtime support matrix is stale and likely misses current supported versions.~~ Resolved: matrix now targets Python 3.10-3.14 (all non-EOL versions).
- ~~TLS verification default is unsafe for production use.~~ Resolved: `verify` defaults to `True` and is configurable.

## Follow-up
- ~~Modernize packaging to `pyproject.toml`.~~ Done.
- ~~Refresh the test/CI matrix.~~ Done.
- ~~Revisit transport security defaults in a separate hardening card.~~ Done: TLS verification is on by default and configurable via the `verify` keyword.
