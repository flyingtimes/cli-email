#!/usr/bin/env python3
"""
Email Priority Manager Setup Script

Sets up the development environment, installs dependencies,
and configures the application for first use.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"Setting up: {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print(f"{'='*50}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True
        )
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print(f"\n{'='*50}")
    print("Checking Python version")
    print(f"{'='*50}")

    version = sys.version_info
    if version < (3, 8):
        print(f"✗ Python 3.8+ required, found {version.major}.{version.minor}")
        return False

    print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_virtual_environment():
    """Create virtual environment."""
    venv_path = Path("venv")

    if venv_path.exists():
        print(f"\n{'='*50}")
        print("Virtual environment already exists")
        print(f"{'='*50}")
        return True

    return run_command([sys.executable, "-m", "venv", "venv"], "virtual environment")

def install_dependencies():
    """Install project dependencies."""
    # Determine the Python executable in the virtual environment
    if os.name == 'nt':  # Windows
        python_exe = Path("venv/Scripts/python.exe")
    else:  # Unix-like
        python_exe = Path("venv/bin/python")

    if not python_exe.exists():
        print(f"✗ Python executable not found: {python_exe}")
        return False

    # Install base dependencies
    if not run_command([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"], "base dependencies"):
        return False

    # Install development dependencies
    if not run_command([str(python_exe), "-m", "pip", "install", "-r", "requirements/dev.txt"], "development dependencies"):
        return False

    # Install the package in development mode
    if not run_command([str(python_exe), "-m", "pip", "install", "-e", "."], "package in development mode"):
        return False

    return True

def setup_pre_commit():
    """Set up pre-commit hooks."""
    return run_command(["pre-commit", "install"], "pre-commit hooks")

def create_directories():
    """Create necessary directories."""
    print(f"\n{'='*50}")
    print("Creating directories")
    print(f"{'='*50}")

    directories = [
        "data",
        "logs",
        "temp",
        "secrets",
        "config"
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")

    return True

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        print(f"\n{'='*50}")
        print("Creating .env file from template")
        print(f"{'='*50}")

        # Copy the example file
        env_content = env_example.read_text()

        # Replace placeholder values with user input or defaults
        import getpass
        import socket

        hostname = socket.gethostname()
        username = getpass.getuser()

        # Simple replacements for common placeholders
        replacements = {
            "your-email@gmail.com": f"{username}@example.com",
            "your-app-password": "your-app-password-here",
            "your-bigmodel-api-key": "your-bigmodel-api-key-here",
            "your-secure-passphrase": f"{hostname}-{username}-secure-passphrase"
        }

        for placeholder, replacement in replacements.items():
            env_content = env_content.replace(placeholder, replacement)

        env_file.write_text(env_content)
        print(f"✓ Created .env file")
        print("⚠️  Please update .env file with your actual credentials")
        return True

    return True

def run_initial_validation():
    """Run initial configuration validation."""
    print(f"\n{'='*50}")
    print("Running initial validation")
    print(f"{'='*50}")

    try:
        # Import and run validation
        from email_priority_manager.config.settings import validate_configuration
        from email_priority_manager.config.secrets import SecretsManager

        # Try to validate configuration
        if validate_configuration():
            print("✓ Configuration validation passed")
        else:
            print("⚠️  Configuration validation failed (expected for first-time setup)")

        # Test secrets manager
        secrets_dir = Path("secrets")
        secrets_dir.mkdir(exist_ok=True)
        SecretsManager(str(secrets_dir))
        print("✓ Secrets manager initialized")

        return True

    except Exception as e:
        print(f"⚠️  Validation failed (expected for first-time setup): {e}")
        return True  # Don't fail setup for validation issues

def main():
    """Main setup function."""
    print("Email Priority Manager Setup")
    print("=" * 50)
    print("This script will set up the development environment for Email Priority Manager.")
    print("=" * 50)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Setup steps
    steps = [
        ("Check Python version", check_python_version),
        ("Create virtual environment", create_virtual_environment),
        ("Install dependencies", install_dependencies),
        ("Setup pre-commit hooks", setup_pre_commit),
        ("Create directories", create_directories),
        ("Create .env file", create_env_file),
        ("Run initial validation", run_initial_validation),
    ]

    failed_steps = []

    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"✗ {step_name} failed with exception: {e}")
            failed_steps.append(step_name)

    # Final summary
    print(f"\n{'='*50}")
    print("Setup Summary")
    print(f"{'='*50}")

    if failed_steps:
        print("✗ Setup completed with errors:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease fix the errors above and re-run the setup script.")
        return 1
    else:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update .env file with your actual credentials")
        print("2. Run 'python -m email_priority_manager.cli.main setup' to configure email and AI services")
        print("3. Run 'pytest' to run tests")
        print("4. Run 'email-priority-manager --help' to see available commands")
        return 0

if __name__ == "__main__":
    sys.exit(main())