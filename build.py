"""
IPv7 Build Script
Consolidated PyInstaller configuration for all IPv7 components
Replaces multiple .spec files with a single dynamic build system
"""

import os
import sys
import subprocess
from pathlib import Path

# Scripts to build (relative to implementations directory)
SCRIPTS_TO_BUILD = [
    "ipv7_autonomo.py",
    "ipv7_experimental.py", 
    "ipv7_real.py",
    "tracker.py"
]

# Base directory
BASE_DIR = Path(__file__).parent
IMPLEMENTATIONS_DIR = BASE_DIR / "src" / "implementations"


def build_exe(script_name: str) -> bool:
    """
    Build a single executable using PyInstaller
    
    Args:
        script_name: Name of the Python script to build
        
    Returns:
        True if build succeeded, False otherwise
    """
    script_path = IMPLEMENTATIONS_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    exe_name = script_name.replace(".py", "")
    
    print(f"🔨 Building {script_name} -> {exe_name}.exe...")
    
    try:
        # Run PyInstaller with standard options
        cmd = [
            "pyinstaller",
            "--onefile",
            "--name", exe_name,
            "--console",
            "--noconfirm",
            "--workpath", str(BASE_DIR / "build"),
            "--distpath", str(BASE_DIR / "dist"),
            str(script_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully built {exe_name}.exe")
            return True
        else:
            print(f"❌ Failed to build {exe_name}.exe")
            print(f"Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ PyInstaller not found. Install with: pip install pyinstaller")
        return False
    except Exception as e:
        print(f"❌ Unexpected error building {script_name}: {e}")
        return False


def clean_build_artifacts():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous build artifacts...")
    
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
            print(f"  Removed {dir_name}/")
    
    # Clean spec files if they exist
    for script in SCRIPTS_TO_BUILD:
        spec_file = BASE_DIR / f"{script.replace('.py', '.spec')}"
        if spec_file.exists():
            spec_file.unlink()
            print(f"  Removed {spec_file.name}")


def build_all():
    """Build all executables"""
    print("=" * 50)
    print("IPv7 Build System")
    print("=" * 50)
    
    # Clean first
    clean_build_artifacts()
    print()
    
    # Build each script
    results = {}
    for script in SCRIPTS_TO_BUILD:
        results[script] = build_exe(script)
        print()
    
    # Summary
    print("=" * 50)
    print("BUILD SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    for script, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {script}")
    
    print()
    print(f"Built {successful}/{total} executables successfully")
    
    if successful == total:
        print("🎉 All builds completed successfully!")
        print(f"Executables are in: {BASE_DIR / 'dist'}")
        return 0
    else:
        print("⚠️ Some builds failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    # Change to script directory for consistent paths
    os.chdir(BASE_DIR)
    
    # Build all
    exit_code = build_all()
    sys.exit(exit_code)