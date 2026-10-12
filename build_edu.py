#!/usr/bin/env python3
"""build_edu.py - Build and package script for EduMath executable.

Compiles the EduMath interactive application into a standalone Windows .exe using PyInstaller.
Designed to be reusable for future releases and version updates.

Usage examples:
    # Build default standalone executable:
    python build_edu.py

    # Build with specific version and custom name:
    python build_edu.py --version 1.0.1 --name EduMath-v1.0.1

    # Build folder distribution (faster launch):
    python build_edu.py --mode onedir

    # Build with debug console enabled:
    python build_edu.py --console

    # Build and test run immediately:
    python build_edu.py --run
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def get_default_version() -> str:
    """Extracts application version from edu package if available."""
    try:
        import edu
        return getattr(edu, "__version__", "1.0.0")
    except Exception:
        return "1.0.0"


def version_str_to_tuple(version_str: str) -> tuple:
    """Converts a semver string like '1.2.3' into a 4-integer tuple for Windows version info."""
    clean = version_str.split("-")[0].split("+")[0]
    parts = []
    for token in clean.split("."):
        try:
            parts.append(int(token))
        except ValueError:
            parts.append(0)
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def generate_version_info(output_path: Path, app_name: str, version_str: str, description: str) -> None:
    """Generates a Windows version metadata resource file for PyInstaller."""
    v_tuple = version_str_to_tuple(version_str)
    content = f"""# UTF-8
# Generated automatically by build_edu.py
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={v_tuple},
    prodvers={v_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'EduMath Open Learning'),
        StringStruct('FileDescription', '{description}'),
        StringStruct('FileVersion', '{version_str}'),
        StringStruct('InternalName', '{app_name}'),
        StringStruct('LegalCopyright', 'Copyright (C) 2026 EduMath. All rights reserved.'),
        StringStruct('OriginalFilename', '{app_name}.exe'),
        StringStruct('ProductName', '{app_name}'),
        StringStruct('ProductVersion', '{version_str}')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def clean_directory(path: Path) -> None:
    """Safely removes an existing directory and its contents."""
    if path.exists():
        try:
            shutil.rmtree(path)
            print(f"  [Cleaned] {path}")
        except Exception as e:
            print(f"  [Warning] Could not clean {path}: {e}")


def build_executable(
    entry_point: str = "run_edu.py",
    app_name: str = "EduMath",
    version: str = "1.0.0",
    mode: str = "onefile",
    console: bool = False,
    clean: bool = True,
    dist_dir: str = "dist",
    build_dir: str = "build",
    icon_path: str = "edu/assets/icon.ico",
    run_after: bool = False,
    open_folder: bool = False,
) -> bool:
    """Runs PyInstaller with configured arguments to build the executable."""
    root_dir = Path(__file__).resolve().parent
    entry_file = root_dir / entry_point
    dist_path = root_dir / dist_dir
    build_path = root_dir / build_dir
    icon_file = root_dir / icon_path

    if not entry_file.exists():
        print(f"Error: Entry point script '{entry_file}' not found.")
        return False

    print("=" * 70)
    print(f"  BUILDING: {app_name} (v{version})")
    print(f"  Mode: {'Single File (.exe)' if mode == 'onefile' else 'Directory Bundle'}")
    print(f"  Console Window: {'Enabled (Debug)' if console else 'Disabled (Windowed GUI)'}")
    print(f"  Entry Point: {entry_file.name}")
    print(f"  Output Directory: {dist_path}")
    print("=" * 70)

    # 1. Clean previous build artifacts if requested
    if clean:
        print("\n[1/4] Cleaning build artifacts...")
        clean_directory(build_path)
        # Note: only remove the target exe or dir inside dist to avoid wiping other dist items
        target_in_dist = dist_path / (f"{app_name}.exe" if mode == "onefile" else app_name)
        if target_in_dist.exists():
            if target_in_dist.is_dir():
                shutil.rmtree(target_in_dist)
            else:
                target_in_dist.unlink()
            print(f"  [Cleaned] Previous build at {target_in_dist}")

    build_path.mkdir(parents=True, exist_ok=True)
    dist_path.mkdir(parents=True, exist_ok=True)

    # 2. Generate Windows version metadata resource
    print("\n[2/4] Generating Windows version metadata...")
    version_file = build_path / "version_info.txt"
    generate_version_info(
        version_file,
        app_name=app_name,
        version_str=version,
        description="EduMath Interactive Learning Application"
    )
    print(f"  [Created] {version_file}")

    # 3. Assemble PyInstaller command-line arguments
    print("\n[3/4] Compiling application with PyInstaller...")
    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name", app_name,
        f"--{mode}",
        "--windowed" if not console else "--console",
        "--distpath", str(dist_path),
        "--workpath", str(build_path),
        "--specpath", str(root_dir),
        "--version-file", str(version_file),
    ]

    # Include assets directory: source;dest (Windows format with semicolon)
    assets_dir = root_dir / "edu" / "assets"
    if assets_dir.exists():
        pyinstaller_args.extend(["--add-data", f"{assets_dir};edu/assets"])
        print(f"  [Asset Included] {assets_dir} -> edu/assets")

    # Add application icon if available
    if icon_file.exists():
        pyinstaller_args.extend(["--icon", str(icon_file)])
        print(f"  [Icon Attached] {icon_file}")

    # Explicit hidden imports to prevent missing dynamic dependencies
    hidden_imports = [
        "pygame",
        "pygame.font",
        "pygame.mixer",
        "pygame.sndarray",
        "numpy",
        "edu",
        "edu.app",
        "edu.main",
        "edu.sound",
        "edu.theme",
        "edu.lessons",
        "edu.generator",
        "edu.math_renderer",
        "edu.exercises",
        "edu.components",
    ]
    for hi in hidden_imports:
        pyinstaller_args.extend(["--hidden-import", hi])

    # Target entry point
    pyinstaller_args.append(str(entry_file))

    start_time = time.time()
    try:
        proc = subprocess.run(pyinstaller_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] PyInstaller build failed with exit code {e.returncode}.")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during compilation: {e}")
        return False

    elapsed = time.time() - start_time

    # 4. Verification and summary
    print(f"\n[4/4] Compilation completed in {elapsed:.1f} seconds!")
    exe_path = dist_path / f"{app_name}.exe" if mode == "onefile" else dist_path / app_name / f"{app_name}.exe"

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("=" * 70)
        print("  BUILD SUCCESSFUL!")
        print(f"  Executable: {exe_path}")
        print(f"  Size: {size_mb:.2f} MB")
        print("=" * 70)

        if open_folder:
            print(f"Opening folder {dist_path} in Explorer...")
            subprocess.run(["explorer", str(dist_path)], check=False)

        if run_after:
            print(f"Launching {exe_path.name}...")
            subprocess.Popen([str(exe_path)])

        return True
    else:
        print(f"[Warning] Expected output file not found at {exe_path}.")
        return False


def main():
    default_version = get_default_version()

    parser = argparse.ArgumentParser(
        description="EduMath Executable Compiler & Packager",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v", "--version",
        default=default_version,
        help="Application version string (e.g. 1.0.0, 1.1.0)",
    )
    parser.add_argument(
        "-n", "--name",
        default="EduMath",
        help="Name of the generated executable",
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["onefile", "onedir"],
        default="onefile",
        help="Build mode: 'onefile' for single .exe, 'onedir' for directory bundle",
    )
    parser.add_argument(
        "-c", "--console",
        action="store_true",
        help="Keep console window open for debugging stdout/stderr logs",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleaning build and dist cache before building",
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Destination directory for built binaries",
    )
    parser.add_argument(
        "--icon",
        default="edu/assets/icon.ico",
        help="Path to Windows .ico file for executable icon",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Automatically launch the compiled executable after building",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the destination folder in Windows Explorer after building",
    )

    args = parser.parse_args()

    success = build_executable(
        entry_point="run_edu.py",
        app_name=args.name,
        version=args.version,
        mode=args.mode,
        console=args.console,
        clean=not args.no_clean,
        dist_dir=args.dist_dir,
        build_dir="build",
        icon_path=args.icon,
        run_after=args.run,
        open_folder=args.open,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
