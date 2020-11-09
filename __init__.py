# Fall 2020
# Vinetech generators imports

"""
Gives external access to appropriate internals.

Classes needing access to externals should be in the /ingest level.
"""

import os.path as p
import sys

# Add the package directory to the path variables
ingest = p.dirname(p.abspath(__file__))
sys.path.append(ingest)

root = p.dirname(ingest)
sys.path.append(root)
