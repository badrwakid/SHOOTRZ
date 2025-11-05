"""
Setup verification script.

Checks that all required configuration and dependencies are in place.
"""

import os
import sys
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_file_exists(filepath: Path, description: str) -> bool:
	"""Check if a file exists."""
	if filepath.exists():
		print(f"{GREEN}✓{RESET} {description}: {filepath}")
		return True
	else:
		print(f"{RED}✗{RESET} {description}: {filepath} (NOT FOUND)")
		return False


def check_env_var(var_name: str, description: str) -> bool:
	"""Check if environment variable is set."""
	value = os.getenv(var_name)
	if value:
		# Don't print full value for security
		preview = value[:20] + "..." if len(value) > 20 else value
		print(f"{GREEN}✓{RESET} {description}: {var_name} = {preview}")
		return True
	else:
		print(f"{RED}✗{RESET} {description}: {var_name} (NOT SET)")
		return False


def check_python_package(package: str) -> bool:
	"""Check if Python package is installed."""
	try:
		__import__(package)
		print(f"{GREEN}✓{RESET} Python package: {package}")
		return True
	except ImportError:
		print(f"{RED}✗{RESET} Python package: {package} (NOT INSTALLED)")
		return False


def check_supabase_connection() -> bool:
	"""Check Supabase connection."""
	try:
		from backend.storage.supabase_client import get_service_client
		client = get_service_client()
		# Try a simple query
		result = client.table("users").select("count", count="exact").execute()
		print(f"{GREEN}✓{RESET} Supabase connection: SUCCESS")
		return True
	except Exception as e:
		print(f"{RED}✗{RESET} Supabase connection: FAILED - {str(e)}")
		return False


def main():
	"""Run all verification checks."""
	print("\n" + "=" * 60)
	print("SHOOTRZ Setup Verification")
	print("=" * 60 + "\n")

	all_checks_passed = True

	# Check backend directory structure
	print("\n📁 Directory Structure:")
	backend_dir = Path(__file__).parent.parent / "backend"
	checks = [
		(backend_dir / "main.py", "Backend main.py"),
		(backend_dir / "requirements.txt", "Requirements.txt"),
		(backend_dir / ".env", "Backend .env file"),
	]
	for filepath, desc in checks:
		if not check_file_exists(filepath, desc):
			all_checks_passed = False

	# Check frontend directory structure
	print("\n📱 Frontend Structure:")
	frontend_dir = Path(__file__).parent.parent
	checks = [
		(frontend_dir / "package.json", "package.json"),
		(frontend_dir / ".env", "Frontend .env file"),
		(frontend_dir / "src", "src directory"),
	]
	for filepath, desc in checks:
		if not check_file_exists(filepath, desc):
			all_checks_passed = False

	# Check environment variables
	print("\n🔐 Environment Variables:")
	env_vars = [
		("SUPABASE_URL", "Supabase URL"),
		("SUPABASE_SERVICE_ROLE_KEY", "Supabase Service Role Key"),
		("SUPABASE_ANON_KEY", "Supabase Anon Key"),
	]
	for var, desc in env_vars:
		if not check_env_var(var, desc):
			all_checks_passed = False

	# Check Python packages
	print("\n🐍 Python Dependencies:")
	packages = [
		"fastapi",
		"uvicorn",
		"supabase",
		"mediapipe",
		"cv2",  # opencv-python
		"numpy",
		"ultralytics",  # YOLOv8
	]
	for package in packages:
		if not check_python_package(package):
			all_checks_passed = False

	# Check Supabase connection
	print("\n🔌 Supabase Connection:")
	if not check_supabase_connection():
		all_checks_passed = False

	# Summary
	print("\n" + "=" * 60)
	if all_checks_passed:
		print(f"{GREEN}✓ All checks passed! Setup is complete.{RESET}")
		print("\n🚀 Next steps:")
		print("  1. Start backend: cd backend && python -m uvicorn main:create_app --factory --reload")
		print("  2. Start frontend: cd SHOOTRZ && npm start")
		print("  3. Visit API docs: http://127.0.0.1:8000/docs")
	else:
		print(f"{RED}✗ Some checks failed. Please review the errors above.{RESET}")
		print("\n📖 See SETUP.md for detailed setup instructions.")
	print("=" * 60 + "\n")

	return 0 if all_checks_passed else 1


if __name__ == "__main__":
	sys.exit(main())



