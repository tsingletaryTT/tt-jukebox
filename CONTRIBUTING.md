# Contributing to tt-jukebox

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to tt-jukebox.

## Code of Conduct

This project follows the Tenstorrent Community Code of Conduct. Be respectful, inclusive, and constructive in all interactions.

## Ways to Contribute

### 1. Report Bugs
- **Search existing issues** first to avoid duplicates
- **Use the bug report template** when creating new issues
- **Include:**
  - Hardware type (N150, N300, T3K, etc.)
  - Python version
  - Full error message and stack trace
  - Steps to reproduce

### 2. Suggest Features
- **Check roadmap** in README first
- **Open a feature request** with clear use case
- **Discuss before implementing** large changes

### 3. Improve Documentation
- Fix typos, clarify instructions
- Add usage examples
- Update installation guides
- Improve code comments

### 4. Submit Code
- Bug fixes
- New features
- Performance improvements
- Test coverage

## Development Setup

### Prerequisites
- Python 3.9+
- Tenstorrent hardware (for full testing)
- Git

### Clone and Setup

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/tt-jukebox.git
cd tt-jukebox

# 3. Add upstream remote
git remote add upstream https://github.com/tenstorrent/tt-jukebox.git

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 5. Install dev dependencies
pip install -r requirements-tui.txt  # For TUI development
```

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes
# Edit files...

# 3. Test your changes
python3 tt-jukebox.py --list
python3 tt-jukebox.py --model llama

# 4. Check code style
# (Currently no linter enforced, but follow existing style)

# 5. Commit with clear messages
git add .
git commit -m "Add feature: brief description

Detailed explanation of what changed and why.
Fixes #123"

# 6. Push to your fork
git push origin feature/your-feature-name

# 7. Open Pull Request on GitHub
```

## Code Style

### Python Style
- Follow **PEP 8** conventions
- Use **type hints** where appropriate
- Add **docstrings** for functions and classes
- Keep functions **focused and small**

### Code Example

```python
def fetch_model_specs(force_refresh: bool = False) -> Optional[List[Dict]]:
    """
    Fetch model specifications from GitHub.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        List of model spec dictionaries, or None if fetch fails

    Example:
        specs = fetch_model_specs(force_refresh=True)
        if specs:
            print(f"Found {len(specs)} models")
    """
    # Implementation...
```

### Commit Messages

**Format:**
```
<type>: <short summary>

<detailed description>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**
```
feat: Add experimental model support

Adds --show-experimental flag to include models not validated
for user's hardware. Uses conservative parameters (33% reduction)
to minimize OOM risk.

Fixes #42
```

## Testing

### Manual Testing Checklist

Before submitting PR, test:

- [ ] `tt-jukebox.py --list` shows models
- [ ] `tt-jukebox.py --model llama` finds matches
- [ ] Hardware detection works: `tt-smi -s`
- [ ] Setup flow completes without errors
- [ ] vLLM command is correct and runs
- [ ] Works on both clean install and existing setup
- [ ] Error messages are clear and helpful

### Test on Multiple Scenarios

- **Fresh clone** (no tt-metal/vllm installed)
- **Existing installations** (correct commits)
- **Wrong commits** (needs checkout)
- **Network issues** (cached specs work)
- **Missing hardware** (graceful error)

## Adding New Features

### Task Mapping

To add a new task type (e.g., "reasoning"):

1. **Update `match_task()` function:**
```python
task_mappings = {
    'chat': ['llama', 'mistral', 'qwen', 'gemma'],
    'reasoning': ['qwq', 'deepseek', 'o1'],  # NEW
}
```

2. **Document in README.md** task table

3. **Add usage example** to USAGE_EXAMPLES.md

### Hardware Support

To add support for new hardware:

1. **Update `filter_by_hardware()` function:**
```python
arch_families = {
    'wormhole_b0': ['N150', 'N300', 'T3K'],
    'blackhole': ['P100', 'P150'],
    'grayskull': ['E75', 'E150'],  # NEW
}
```

2. **Test hardware detection** with `detect_hardware()`

3. **Verify `tt-smi` output parsing**

## Pull Request Process

### Before Submitting

1. ✅ **Rebase on latest main:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. ✅ **Test thoroughly** (see checklist above)

3. ✅ **Update documentation** if needed

4. ✅ **Add yourself to contributors** (if first PR)

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] Tested on hardware
- [ ] All commands work
- [ ] No breaking changes (or documented)

## Screenshots (if UI changes)
```

### Review Process

1. Maintainer reviews code
2. Automated checks run (if configured)
3. Discussion and feedback
4. Revisions if needed
5. Approval and merge

## Release Process

(For maintainers)

1. Update version in `tt-jukebox.py` and `setup.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag -a v1.0.1 -m "Release v1.0.1"`
4. Push tag: `git push origin v1.0.1`
5. Create GitHub release with notes

## Questions?

- **GitHub Issues:** General questions
- **Discord:** https://discord.gg/tenstorrent
- **Documentation:** README.md, INSTALL.md

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to tt-jukebox! 🎵**
