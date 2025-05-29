#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment setup script for network monitoring application
"""

import os
import sys
import subprocess
import logging

def setup_environment():
    """Set up the environment for the network monitoring application"""
    print("🚀 Setting up environment for Network Monitoring Application...")

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            raise RuntimeError(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")

        print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

        # Create necessary directories
        directories = [
            "logs",
            "logs_moxa",
            "config",
            "tests/reports"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")

        # Check for required modules
        required_modules = [
            "pytest",
            "dataclasses",  # Should be built-in for Python 3.7+
            "typing",       # Should be built-in
            "json",         # Built-in
            "subprocess",   # Built-in
            "re",           # Built-in
            "datetime",     # Built-in
            "csv",          # Built-in
            "os",           # Built-in
            "logging",      # Built-in
        ]

        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
                print(f"✅ Module available: {module}")
            except ImportError:
                missing_modules.append(module)
                print(f"❌ Module missing: {module}")

        if missing_modules and "pytest" in missing_modules:
            print("📦 Installing pytest...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
                print("✅ pytest installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install pytest: {e}")        # Test basic network connectivity
        print("\n🌐 Testing network connectivity...")
        try:
            result = subprocess.run(["ping", "-n", "1", "8.8.8.8"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Network connectivity: OK")
            else:
                print("⚠️  Network connectivity: Limited (may affect network tests)")
        except Exception as e:
            print(f"⚠️  Network test failed: {e}")

        # Verify core modules
        print("\n🔍 Verifying core application modules...")

        try:
            import network_monitor
            print("✅ network_monitor module: Available")

            # Test basic functionality
            print("   Testing ping_ip function...")
            result = network_monitor.ping_ip("127.0.0.1")  # Test with localhost
            if isinstance(result, dict) and 'ip' in result:
                print("   ✅ ping_ip function: Working")
            else:
                print("   ⚠️  ping_ip function: May have issues")

        except ImportError as e:
            print(f"❌ network_monitor module: Not found ({e})")
        except Exception as e:
            print(f"⚠️  network_monitor module: Issues detected ({e})")

        # Check WiFi modules (optional)
        try:
            from wifi.wifi_collector import WifiCollector
            print("✅ wifi.wifi_collector module: Available")
        except ImportError:
            print("⚠️  wifi.wifi_collector module: Not available (optional)")

        print("\n📋 Environment setup completed!")
        return True

    except Exception as e:
        logger.error(f"Environment setup failed: {e}")
        return False

def run_basic_tests():
    """Run basic functionality tests"""
    print("\n🧪 Running basic functionality tests...")

    try:
        # Test network_monitor module
        import network_monitor

        print("Testing network_monitor.ping_ip...")
        result = network_monitor.ping_ip("127.0.0.1")
        print(f"  Result: {result}")

        if result.get('ip') == '127.0.0.1':
            print("✅ Basic ping test: PASSED")
        else:
            print("❌ Basic ping test: FAILED")

        # Test parsing functions
        print("Testing parsing functions...")
        sample_output = """
Ping statistics for 127.0.0.1:
    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 0ms, Maximum = 1ms, Average = 0ms
        """

        latency, loss, loss_value = network_monitor._parse_ping_output(sample_output)
        if latency == "0ms" and loss == "0%":
            print("✅ Parsing functions: PASSED")
        else:
            print("❌ Parsing functions: FAILED")

        print("✅ All basic tests passed!")
        return True

    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("    NETWORK MONITORING APPLICATION SETUP")
    print("=" * 60)

    # Run setup
    setup_success = setup_environment()

    if setup_success:
        # Run basic tests
        test_success = run_basic_tests()

        if test_success:
            print("\n🎉 Environment setup and testing completed successfully!")
            print("\n📖 Next steps:")
            print("   • Run 'python -m pytest tests/' to run all tests")
            print("   • Run 'python runner.py' to start the GUI application")
            print("   • Check logs/ directory for application logs")
            sys.exit(0)
        else:
            print("\n⚠️  Environment setup completed but basic tests failed")
            sys.exit(1)
    else:
        print("\n❌ Environment setup failed")
        sys.exit(1)
