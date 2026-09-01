# Pampa release process

This document describes how to release Pampa as both a Python package and an
executable Shiv archive.

The release artifacts are:

- a source distribution (`.tar.gz`),
- a wheel (`.whl`), and
- an extensionless executable Shiv archive (`dist/pampa`).

The Shiv archive is convenient to distribute, but it still requires Python
3.12 or newer on the target machine. It is not a native standalone binary.

## Release prerequisites

Install or make available:

- Python 3.12 or newer,
- [`uv`](https://docs.astral.sh/uv/),
- Git,
- a clean checkout of the repository, and
- an account or publishing mechanism for the package/release destination, if
  the artifacts will be uploaded.

The project uses `pyproject.toml` as the canonical source of the package
version. Do not manually maintain a second hard-coded version in
`pampa/__about__.py`.

`pampa/__about__.py` should derive the installed version from package metadata:

```python
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

try:
    __version__ = package_version("pampa")
except PackageNotFoundError:
    __version__ = "0+unknown"
```

This works for installed packages, editable development installs, wheels, and
Shiv archives. When running code from an entirely uninstalled source checkout,
`0+unknown` is expected.

## First-time build setup

The project should provide the following Make targets:

```console
make bump LEVEL=patch
make build
make tag
```

A recommended implementation is:

```make
.PHONY: bump build tag

bump:
	@test -n "$(LEVEL)" || (echo "Usage: make bump LEVEL=patch|minor|major"; exit 1)
	uv version --bump "$(LEVEL)"
	uv lock
	@echo "Version is now $$(uv version --short)"

build:
	rm -rf dist build
	uv build
	uvx shiv \
		--console-script pampa \
		--compressed \
		--reproducible \
		--output-file dist/pampa \
		dist/pampa-*.whl
	chmod +x dist/pampa
	sha256sum dist/pampa > dist/SHA256SUMS
	@echo "Built dist/pampa"

tag:
	@test -z "$$(git status --porcelain)" || \
		(echo "Working tree must be clean before tagging"; exit 1)
	@version=$$(uv version --short); \
	tag="v$$version"; \
	test -z "$$(git tag -l "$$tag")" || \
		(echo "Tag $$tag already exists"; exit 1); \
	git tag -a "$$tag" -m "Release $$tag"; \
	echo "Created $$tag"
```

`uvx shiv` runs Shiv without adding Shiv to Pampa's runtime dependencies.
The wheel is passed to Shiv rather than the source tree so that the build
checks that all package files and package data were included in the wheel.

## Standard release procedure

### 1. Start from an up-to-date checkout

Switch to the release branch and make sure it is current:

```bash
git switch main
git pull --ff-only
```

Check the working tree:

```bash
git status --short
```

Do not begin a release with unrelated modified or untracked files.

### 2. Run the test and lint checks

```bash
make test
make lint
```

Fix all failures before changing the version.

### 3. Bump the version

Choose the appropriate semantic-version increment:

```bash
make bump LEVEL=patch   # 0.1.1 -> 0.1.2
make bump LEVEL=minor   # 0.1.1 -> 0.2.0
make bump LEVEL=major   # 0.1.1 -> 1.0.0
```

Only run one of these commands. Confirm the result:

```bash
uv version
uv run python -c 'import importlib.metadata as m; print(m.version("pampa"))'
git diff -- pyproject.toml uv.lock pampa/__about__.py
```

The metadata lookup can show the previous version if the environment has not
been refreshed. Run `uv sync --locked` if necessary.

### 4. Review and commit the version change

Inspect the complete diff:

```bash
git diff
```

Then commit the release metadata:

```bash
git add pyproject.toml uv.lock pampa/__about__.py
git commit -m "Release v$(uv version --short)"
```

If `pampa/__about__.py` only derives the version from metadata, it normally
will not have a diff and does not need to be staged.

### 5. Build the distributions

```bash
make build
```

The build should create files similar to:

```text
dist/pampa-0.1.2.tar.gz
dist/pampa-0.1.2-py3-none-any.whl
dist/pampa
dist/SHA256SUMS
```

The leading space in the last example is not part of the filename.

Confirm that the wheel includes all runtime files:

```bash
unzip -l dist/*.whl
```

In particular, verify that it contains:

```text
pampa/__init__.py
pampa/__about__.py
pampa/cli.py
pampa/core.py
pampa/chat.py
pampa/tools/__init__.py
pampa/tools/bash.py
pampa/models.toml
```

If `models.toml` is absent, fix the Hatchling package-data configuration
before releasing. Pampa loads that file at runtime.

### 6. Smoke-test the Shiv archive

Test the command entry point:

```bash
dist/pampa --help
```

The archive should be executable directly:

```bash
./dist/pampa
```

Test the installed version metadata:

```bash
uv run python -c 'import pampa; print(pampa.__version__)'
```

For an application smoke test, set the API key and start Pampa:

```bash
OPENAI_API_KEY="$OPENAI_API_KEY" dist/pampa
```

Do not put the API key in the archive, a source file, or a release command
that will be recorded in shell history. The key must be supplied by the user
through the environment at runtime.

The Shiv archive normally caches its extracted dependencies under the user's
Shiv cache directory. This is expected. The first invocation may take longer
than subsequent invocations.

### 7. Create the Git tag

After the build and smoke test pass, ensure that the source tree is clean:

```bash
git status --short
```

Then create the annotated tag:

```bash
make tag
```

Verify it:

```bash
git show --summary "v$(uv version --short)"
```

### 8. Push the commit and tag

Push the release commit and tag separately:

```bash
git push origin main
git push origin "v$(uv version --short)"
```

If CI publishes releases from tags, pushing the tag should start the release
workflow.

### 9. Publish or attach artifacts

Attach these files to the release corresponding to the tag:

```text
dist/pampa
dist/pampa-<version>-py3-none-any.whl
dist/pampa-<version>.tar.gz
dist/SHA256SUMS
```

Again, the leading space shown before the wheel in this documentation is only
formatting; the actual filename starts with `dist/`.

If publishing to PyPI, publish the wheel and source distribution using the
project's configured publishing credentials. The Shiv archive is normally
attached to the GitHub/GitLab release or hosted as a separate downloadable
release asset rather than uploaded to PyPI.

## Installing the executable for users

On Linux and macOS, users can install the extensionless Shiv archive as
`pampa`:

```bash
mkdir -p ~/.local/bin
curl -fL -o ~/.local/bin/pampa \
  https://example.invalid/pampa/releases/latest/download/pampa
chmod +x ~/.local/bin/pampa
```

They must ensure `~/.local/bin` is on `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

They can then run:

```bash
pampa
```

They also need Python 3.12 or newer and an API key:

```bash
export OPENAI_API_KEY="your-api-key"
pampa
```

On Windows, distribute `pampa.pyz` or provide a platform-specific launcher;
the extensionless executable convention documented above is intended for
Unix-like systems.

## Reproducibility and compatibility notes

- Build from the wheel, not directly from the source directory.
- Keep `uv.lock` committed whenever dependencies change.
- The `.pyz` archive requires Python 3.12 or newer.
- Dependencies containing native extensions can make the Shiv archive
  platform-specific. Build and test separate artifacts when necessary.
- Publish the SHA-256 checksum with every release.
- Do not treat Pampa or its shell-command confirmation prompts as a security
  boundary. Users should run it in an appropriately isolated environment when
  handling untrusted prompts or projects.

## Release checklist

- [ ] Working tree was clean before the release.
- [ ] Tests pass.
- [ ] Lint checks pass.
- [ ] Version was bumped with `uv version`.
- [ ] `uv.lock` is up to date.
- [ ] Version change was committed.
- [ ] Wheel and source distribution were built.
- [ ] Wheel contains `pampa/models.toml`.
- [ ] `dist/pampa --help` succeeds.
- [ ] Shiv archive was smoke-tested.
- [ ] Annotated `v<version>` tag was created.
- [ ] Commit and tag were pushed.
- [ ] Release artifacts and checksums were published.
