# Contributing to T-Zero Context Architect

Thank you for your interest in contributing to **T-Zero**! We welcome contributions from developers worldwide to help make context optimization, AST pruning, and autonomous agent orchestration faster, more private, and accessible to everyone.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (Python 3.11 or 3.12 recommended)
- `git`
- Optional: `uv` for ultra-fast environment bootstrapping

### 2. Fork & Clone
```bash
git clone https://github.com/<your-username>/TZeroAlgorithm.git
cd TZeroAlgorithm
```

### 3. Install Dependencies
```bash
# Using standard pip
pip install -e ".[dev]"

# Or using uv
uv sync
```

---

## 🧪 Testing Guidelines

Before opening a pull request, ensure all tests pass locally:

```bash
# Run full unit and integration test suite
python -m unittest discover -s tests -v

# Smoke-test CLI tools
python tzero_v3.py --version
python tzero_v3.py --savings
python tzero_v3.py --scan .
python tzero_v3.py --audit .
```

All pull requests automatically run across a matrix of:
- **Ubuntu Latest & Windows Latest**
- **Python 3.11, 3.12, and 3.13**

---

## 🌐 Adding New Language Support

To add signature reduction for a new programming language (e.g. Zig, Lua, Elixir):
1. Open `tzero_polyglot.py`.
2. Add language file extension mappings to `SUPPORTED_LANGUAGES`.
3. Implement `reduce_<language>(content: str, mode: str) -> str`.
4. Add unit tests in `tests/test_polyglot_engine.py`.
5. Run the test suite: `python -m unittest tests/test_polyglot_engine.py`.

---

## 🔒 100% Zero-Leak & Zero-Cost Policy

T-Zero enforces strict security standards:
- **Never hardcode secrets, API keys, or personal tokens.**
- All code transformations and AST reductions must execute **100% offline** without unexpected cloud API charges ($0.00 cost forever).
- Every PR is automatically scanned by our Zero-Leak security auditor.

---

## 📜 Pull Request Process

1. Create a feature branch: `git checkout -b feature/my-new-feature`
2. Commit with conventional commit messages: `feat: ...`, `fix: ...`, `docs: ...`
3. Push to your fork and submit a Pull Request to `toprakahmetaydogmus/TZeroAlgorithm` (`main` branch).
4. Ensure all CI/CD matrix checks are green.

Thank you for helping empower developers and AI coding agents everywhere!
