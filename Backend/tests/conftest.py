"""
Add Backend/src to sys.path so test modules can import project packages
(agents, services, utils …) with the same unqualified import style used
in production code.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
