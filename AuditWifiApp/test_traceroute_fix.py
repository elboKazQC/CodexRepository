#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify the traceroute fix works on Windows
"""

import os
import subprocess
import re
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_traceroute(ip: str) -> Optional[int]:
    """
    Test the fixed traceroute function
    """
    try:
        print(f"Testing traceroute to {ip}...")

        # Use appropriate command based on operating system
        if os.name == 'nt':  # Windows
            print("Using Windows tracert command...")
            # Windows uses tracert command
            result = subprocess.run([
                "tracert", "-d", ip
            ], capture_output=True, text=True, check=False, timeout=30)
        else:  # Unix-like systems (Linux, macOS)
            print("Using Unix traceroute command...")
            # Unix systems use traceroute command
            result = subprocess.run([
                "traceroute", "-n", ip
            ], capture_output=True, text=True, check=False, timeout=30)

        print(f"Command return code: {result.returncode}")

        if result.returncode != 0:
            print(f"Command failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
            return None

        # Parse output to count hops
        lines = result.stdout.splitlines()
        print(f"Total output lines: {len(lines)}")

        hop_lines = [
            line for line in lines
            if re.match(r"^\s*\d+\s", line)
        ]

        print(f"Found {len(hop_lines)} hop lines:")
        for i, line in enumerate(hop_lines[:5]):  # Show first 5 hops
            print(f"  Hop {i+1}: {line.strip()}")

        return len(hop_lines)

    except FileNotFoundError as e:
        print(f"Traceroute command not found: {e}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Traceroute timeout for {ip}")
        return None
    except Exception as e:
        print(f"Traceroute error: {e}")
        return None

def main():
    """
    Main test function
    """
    print("=" * 60)
    print("Testing Traceroute Fix for Windows")
    print("=" * 60)

    # Test with Google DNS (should be reachable)
    test_ip = "8.8.8.8"

    print(f"\nTesting with {test_ip} (Google DNS)...")
    hops = test_traceroute(test_ip)

    if hops is not None:
        print(f"\n✅ SUCCESS: Traceroute completed with {hops} hops")
    else:
        print(f"\n❌ FAILED: Traceroute failed")

    print("\n" + "=" * 60)
    print("Test completed")

if __name__ == "__main__":
    main()
