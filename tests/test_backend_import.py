#!/usr/bin/env python3
"""Quick test to see if backend routes can be imported"""

try:
    from backend.routes import enhancement
    print("✓ Enhancement routes imported successfully")
    print(f"✓ Router has {len(enhancement.router.routes)} routes")
    for route in enhancement.router.routes:
        print(f"  - {route.methods} {route.path}")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
