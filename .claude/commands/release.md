# Release a new version of exif-sorter

Help me release a new version of exif-sorter. This is a fully automated release pipeline.

## Pre-release Checklist

Before starting, verify:
1. All changes are committed and pushed to main
2. All tests pass locally: `pytest tests/ -v`
3. Linting passes: `ruff check src/`

## Release Steps

### 1. Determine Version Number

Follow semantic versioning (MAJOR.MINOR.PATCH):
- **PATCH** (1.0.x): Bug fixes, no new features
- **MINOR** (1.x.0): New features, backward compatible
- **MAJOR** (x.0.0): Breaking changes

### 2. Update Version Numbers

Update version in TWO files (they must match):
- `pyproject.toml`: `version = "X.Y.Z"`
- `src/exif_sorter/__init__.py`: `__version__ = "X.Y.Z"`

### 3. Update CHANGELOG.md

Add a new section at the top following Keep a Changelog format:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing features

### Fixed
- Bug fixes
```

Don't forget to add the version link at the bottom:
```markdown
[X.Y.Z]: https://github.com/davidamacey/exif-sorter/releases/tag/vX.Y.Z
```

### 4. Commit the Release

```bash
git add -A
git commit -m "Release vX.Y.Z - Brief description"
git push
```

### 5. Create and Push Tag

This triggers the automated release pipeline:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z - Brief description"
git push origin vX.Y.Z
```

### 6. Create GitHub Release

```bash
gh release create vX.Y.Z --title "vX.Y.Z - Brief Title" --notes "$(cat <<'EOF'
## What's New

### Added
- Feature 1
- Feature 2

### Fixed
- Bug fix 1

**Full Changelog**: https://github.com/davidamacey/exif-sorter/compare/vPREVIOUS...vX.Y.Z
EOF
)"
```

## Automated Pipeline

When you push a tag (v*), GitHub Actions automatically:

1. **lint**: Runs ruff on source code
2. **test**: Runs pytest on Python 3.11, 3.12, 3.13
3. **publish**:
   - Verifies tag version matches pyproject.toml
   - Builds package with `python -m build`
   - Uploads to PyPI via twine
4. **docker**:
   - Waits 30s for PyPI propagation
   - Builds multi-arch image (amd64, arm64)
   - Pushes to Docker Hub as `davidamacey/exif-sorter:latest` and `:X.Y.Z`

## Required Secrets

These must be configured in GitHub repo settings:
- `PYPI_API_TOKEN`: PyPI API token (scope: project exif-sorter)
- `DOCKERHUB_USERNAME`: DockerHub username
- `DOCKERHUB_TOKEN`: DockerHub access token

## Verification

After release completes, verify:

```bash
# Check PyPI
pip index versions exif-sorter

# Check Docker Hub
docker pull davidamacey/exif-sorter:latest
docker run --rm davidamacey/exif-sorter:latest --version

# Check GitHub
gh release view vX.Y.Z
```

## Rollback (if needed)

If something goes wrong:

```bash
# Delete the tag locally and remotely
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z

# Delete GitHub release
gh release delete vX.Y.Z --yes
```

Note: PyPI releases cannot be deleted, only yanked. Docker images can be deleted from Docker Hub UI.
