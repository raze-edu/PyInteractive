"""Entry point for the EduMath Pygame interactive learning application."""
import os
import sys

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from edu.app import EduApp

def main():
    print("Launching EduMath application...")
    app = EduApp()
    app.run()

if __name__ == "__main__":
    main()
