# Traceroute Fix for Windows

## Problem
The application was experiencing the error:
```
ERROR:root:Traceroute error: [WinError 2] The system cannot find the file specified
```

## Root Cause
The application was trying to use the Unix `traceroute` command on Windows, which doesn't exist by default. Windows uses the `tracert` command instead.

## Solution
Modified the `_perform_traceroute` method in `runner.py` to:

1. **Detect Operating System**: Use `os.name == 'nt'` to detect Windows
2. **Use Correct Command**:
   - Windows: `tracert -d <ip>`
   - Unix/Linux/macOS: `traceroute -n <ip>`
3. **Improved Error Handling**: Added specific handling for:
   - `FileNotFoundError`: Command not found
   - `subprocess.TimeoutExpired`: Command timeout
   - Better logging with specific error messages

## Code Changes

### Before:
```python
def _perform_traceroute(self, ip: str) -> Optional[int]:
    try:
        result = subprocess.run([
            "traceroute", "-n", ip
        ], capture_output=True, text=True, check=False, timeout=30)
        # ... rest of function
```

### After:
```python
def _perform_traceroute(self, ip: str) -> Optional[int]:
    try:
        # Use appropriate command based on operating system
        if os.name == 'nt':  # Windows
            # Windows uses tracert command
            result = subprocess.run([
                "tracert", "-d", ip
            ], capture_output=True, text=True, check=False, timeout=30)
        else:  # Unix-like systems (Linux, macOS)
            # Unix systems use traceroute command
            result = subprocess.run([
                "traceroute", "-n", ip
            ], capture_output=True, text=True, check=False, timeout=30)
        # ... improved error handling
```

## Testing
- ✅ Windows `tracert -d 8.8.8.8` command works
- ✅ Application loads without traceroute errors
- ✅ Cross-platform compatibility maintained

## Benefits
1. **Cross-Platform**: Works on both Windows and Unix-like systems
2. **Better Error Messages**: More specific error reporting
3. **Robust**: Proper timeout and exception handling
4. **User-Friendly**: Improved UI feedback for traceroute operations

## Parameters Used
- **Windows**: `tracert -d` (suppress hostname resolution for faster execution)
- **Unix**: `traceroute -n` (suppress hostname resolution for faster execution)

Both commands provide similar functionality with numeric IP addresses only, making parsing consistent across platforms.
