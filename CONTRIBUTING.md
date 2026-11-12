# Contributing

Thank you for helping improve this academic and experimental MVP. Its scope and
operational value remain subject to field research; do not present assumptions as
facts about Olokuti or its internal systems.

## Development setup

Follow the local setup in [README.md](README.md). Use Python 3.12 and install
`requirements/development.txt` in a virtual environment. Copy `.env.example` to
`.env` and use only local credentials and synthetic records.

## Before opening a pull request

Run the checks from the project root:

```powershell
ruff check .
pytest
```

Include focused tests for behavior changes, permissions, and security-sensitive
paths. Keep migrations, gettext source catalogs, and their compiled catalogs in
sync when applicable. Never commit secrets, local databases, or real personal or
operational data.

## Content and demo data

Product origins, certifications, suppliers, sustainability claims, and internal
workflows must not be attributed to Olokuti without evidence and authorization.
The `seed_demo` command is restricted to `DEBUG=True` and uses synthetic
placeholders. Do not use it with production data.

## Scope and license

By submitting a contribution, you agree that your contribution is distributed
under the repository's MIT License. The license covers project code and
documentation created for this repository; third-party marks, names, assets, and
data remain subject to their respective rights.
