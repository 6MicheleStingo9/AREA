import subprocess
import sys
from pathlib import Path


def main():
    """Start the Streamlit application."""
    streamlit_app = Path(__file__).parent / "app.py"

    if not streamlit_app.exists():
        print(f"❌ File not found: {streamlit_app}")
        sys.exit(1)

    print("🚀 Starting Streamlit application...")
    print("📝 Application will open in the default browser")
    print("⏹️  Press Ctrl+C to stop\n")

    # Propagate the --lang argument if present
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["it", "en"], default="en")
    args = parser.parse_args()
    lang_arg = f"--lang={args.lang}" if args.lang else ""

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(streamlit_app),
        "--theme.base=dark",
        "--theme.primaryColor=#00cc88",
        "--server.headless=true",
    ]
    # Custom arguments go after '--'
    if lang_arg:
        cmd += ["--", lang_arg]
    subprocess.run(cmd, cwd=Path(__file__).parent)


if __name__ == "__main__":
    main()
