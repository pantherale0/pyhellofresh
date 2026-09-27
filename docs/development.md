# Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,docs]'
```

## Tests

```bash
pytest --cov=pyhellofresh
```

CI on `main` and `develop` runs Ruff and pytest on Python 3.14.

`example_test.py` calls the live API:

```bash
python3 example_test.py --token "YOUR_ACCESS_TOKEN"
python3 example_test.py --email "user@example.com"
python3 example_test.py --refresh-token "YOUR_REFRESH_TOKEN"
python3 example_test.py --week 2026-W40 --country GB --locale en-GB
```

`--refresh-token` falls back to the `REFRESH_TOKEN` environment variable. `--email` falls back to `EMAIL`.

## Docs site

```bash
mkdocs serve
```

The published site is <https://pantherale0.github.io/pyhellofresh/>.

Pushes and pull requests to `main` build the site with `mkdocs build --strict`. A push to `main` also deploys that build to GitHub Pages.

One repository setting is required the first time: **Settings → Pages → Build and deployment → Source: GitHub Actions**. The workflow uploads the `site/` directory as a Pages artifact and deploys it with `actions/deploy-pages`. `site/` is gitignored.

API pages are generated from the docstrings in `src/pyhellofresh` by mkdocstrings. Guide pages live in `docs/`.
