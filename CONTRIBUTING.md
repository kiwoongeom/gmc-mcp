# Contributing to gmc-mcp

Thanks for your interest! Contributions of all sizes are welcome.

## Dev setup

```bash
git clone https://github.com/<you>/gmc-mcp.git
cd gmc-mcp
python -m venv .venv
. .venv/Scripts/activate     # Windows; use 'source .venv/bin/activate' on Unix
pip install -e ".[dev,test]"
pre-commit install
```

## Running tests

```bash
pytest                       # all tests
pytest -k products           # filter
pytest --cov=gmc_mcp         # with coverage
```

Tests run fully offline using `respx` to mock the Merchant API. They do **not**
hit Google's servers, so you don't need credentials to develop on this repo.

## Style

- `ruff format` + `ruff check --fix` (run automatically by pre-commit).
- `mypy src/gmc_mcp` should pass.
- Type-hint everything new.
- Public tool functions need a docstring; the first line becomes the MCP tool
  description shown to the model.

## Adding a tool

1. Pick (or create) a module under `src/gmc_mcp/tools/`.
2. Define the function inside the module's `register(mcp, client)` and decorate
   with `@mcp.tool()`.
3. Use `client.request(method, path, ...)` for everything — never call `httpx`
   directly so audit and retries stay consistent.
4. For write operations, pass `op="..."` so the audit log has a readable label.
5. For tools that read the existing state before mutating, pass `before=...`
   so the audit log can be used to roll back.
6. Add a unit test in `tests/test_tools_<module>.py`.

## Releasing

Maintainers only.

```bash
# 1. Bump the version in src/gmc_mcp/__init__.py and pyproject.toml
# 2. Update CHANGELOG.md (move Unreleased entries to a new dated section)
# 3. Commit + tag
git commit -am "release: 0.x.y"
git tag v0.x.y
git push origin main --tags
```

The `publish.yml` workflow then builds and uploads to PyPI via OIDC trusted
publishing (no API tokens stored in the repo).
