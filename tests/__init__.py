# Fall 2020
# Vinetech ingest imports

import os.path as p
import sys

# Add the root directory to the path variables
ingest = p.dirname(p.dirname(p.abspath(__file__)))
sys.path.append(ingest)
