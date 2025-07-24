#!/usr/bin/env python3
"""
Quick fix for sentencepiece/tokenizer errors
"""

import subprocess
import sys

def install_package(package):
    """Install a Python package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    print("🔧 Fixing sentencepiece and tokenizer issues...")
    print("=" * 50)
    
    packages_to_install = [
        "sentencepiece",
        "protobuf",
        "transformers",
        "torch"
    ]
    
    success_count = 0
    for package in packages_to_install:
        print(f"\nInstalling {package}...")
        if install_package(package):
            success_count += 1
    
    print(f"\n{'=' * 50}")
    print(f"Installation complete: {success_count}/{len(packages_to_install)} packages installed")
    
    if success_count == len(packages_to_install):
        print("\n🎉 All dependencies installed successfully!")
        print("\n🚀 You can now try:")
        print("   python minimal_demo.py     # Works without AI models")
        print("   python example.py          # Full demo with sample data")
        print("   python test_syntax.py      # Test syntax fixes")
    else:
        print("\n⚠️  Some installations failed. Try:")
        print("   ./install_dependencies.sh  # Full auto-installer")
        print("   python minimal_demo.py     # Still works without ML models")
    
    print("\n📖 For more help, see TROUBLESHOOTING.md")

if __name__ == "__main__":
    main()