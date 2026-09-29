import os
import sys

from server import start_server


def main():
    print()
    print("========================================")
    print("          AniVora API Platform")
    print("========================================")
    print()

    print("Checking project files...")

    required_files = [
        "server.py",
        "routes.py",
        "database.py",
        "auth.py",
        "ai_engine.py",
    ]

    missing = [
        filename
        for filename in required_files
        if not os.path.isfile(filename)
    ]

    if missing:
        print()
        print("Missing required files:")

        for filename in missing:
            print(f"  - {filename}")

        print()
        print("AniVora API cannot start.")
        sys.exit(1)

    print("Project files: OK")
    print()

    print("Initializing AniVora API...")
    print()

    try:
        start_server()

    except KeyboardInterrupt:
        print()
        print("AniVora API stopped.")

    except OSError as error:
        print()
        print("Could not start AniVora API.")
        print()
        print(f"Error: {error}")
        print()
        print(
            "The port may already be in use."
        )
        sys.exit(1)

    except Exception as error:
        print()
        print("AniVora API failed to start.")
        print()
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
