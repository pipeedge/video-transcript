#!/usr/bin/env python3
"""
Check and diagnose dependencies for the Podcast Analyzer
"""

import sys
import subprocess
import importlib
import shutil

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ required")
        return False

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - run: pip install {package_name}")
        return False

def check_system_dependency(command, package_name):
    """Check if a system dependency is available"""
    if shutil.which(command):
        print(f"✅ {package_name}")
        return True
    else:
        print(f"❌ {package_name} - see install_dependencies.sh")
        return False

def check_docker():
    """Check if Docker is available for MeiliSearch"""
    if shutil.which("docker"):
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Docker (for MeiliSearch)")
                return True
        except:
            pass
    
    print("⚠️  Docker not found - MeiliSearch will not work")
    print("   Install Docker or run MeiliSearch locally")
    return False

def main():
    print("🔍 Checking Podcast Analyzer Dependencies")
    print("=" * 50)
    
    all_good = True
    
    # Check Python version
    print("\n📋 Python Environment:")
    all_good &= check_python_version()
    
    # Check core Python packages
    print("\n📦 Core Python Packages:")
    packages = [
        ("requests", "requests"),
        ("python-dotenv", "dotenv"),
        ("pydantic", "pydantic"),
    ]
    
    for pkg, import_name in packages:
        all_good &= check_package(pkg, import_name)
    
    # Check audio processing packages
    print("\n🎵 Audio Processing:")
    audio_packages = [
        ("pydub", "pydub"),
        ("librosa", "librosa"),
    ]
    
    for pkg, import_name in audio_packages:
        all_good &= check_package(pkg, import_name)
    
    # Check ML packages
    print("\n🤖 Machine Learning:")
    ml_packages = [
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("openai-whisper", "whisper"),
    ]
    
    for pkg, import_name in ml_packages:
        check_package(pkg, import_name)  # Don't fail on ML packages
    
    # Check system dependencies
    print("\n🔧 System Dependencies:")
    check_system_dependency("ffmpeg", "FFmpeg")
    
    # Check optional services
    print("\n🌐 Optional Services:")
    check_docker()
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("🎉 All core dependencies are installed!")
        print("\n🚀 Ready to run:")
        print("   python example.py          # Demo mode")
        print("   python test_syntax.py      # Test fixes")
        print("   ./install_dependencies.sh  # Install missing items")
    else:
        print("⚠️  Some dependencies are missing")
        print("\n🔧 To fix:")
        print("   ./install_dependencies.sh  # Auto-install")
        print("   pip install -r requirements.txt")
        print("\n📖 See TROUBLESHOOTING.md for detailed help")
    
    print("\n💡 Note: Demo mode works even with missing ML packages!")

if __name__ == "__main__":
    main()