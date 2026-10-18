from pathlib import Path

# The current folder is our AgentGuard project root.
ROOT = Path(__file__).resolve().parent

# Create directories.
directories = [
    "agentguard",
    "models",
]

for directory in directories:
    (ROOT / directory).mkdir(
        parents=True,
        exist_ok=True
    )

# Create Python module files.
python_files = [
    "agentguard/__init__.py",
    "agentguard/db.py",
    "agentguard/collector.py",
    "agentguard/features.py",
    "agentguard/train_model.py",
    "agentguard/monitor.py",
    "agentguard/diagnosis.py",
    "agentguard/actions.py",
    "dashboard.py",
]

for filename in python_files:
    file_path = ROOT / filename

    if not file_path.exists():
        file_path.touch()

# Create requirements.txt.
requirements_file = ROOT / "requirements.txt"

if not requirements_file.exists():
    requirements_file.write_text(
        "",
        encoding="utf-8"
    )

# Create a local environment file.
env_file = ROOT / ".env"

if not env_file.exists():
    env_file.write_text(
        'MONGODB_URI=""\n'
        'MONGODB_DB="agentguard"\n'
        'GEMINI_API_KEY=""\n',
        encoding="utf-8"
    )

# Create .gitignore.
gitignore_file = ROOT / ".gitignore"

if not gitignore_file.exists():
    gitignore_file.write_text(
        ".env\n"
        ".venv/\n"
        "__pycache__/\n"
        "*.py[cod]\n"
        ".pytest_cache/\n"
        ".streamlit/secrets.toml\n",
        encoding="utf-8"
    )

print("AgentGuard project structure created!")
print(f"Project location: {ROOT}")

print("\nProject files:")
for path in sorted(ROOT.rglob("*")):
    if ".venv" not in path.parts and path.is_file():
        print(path.relative_to(ROOT))