import os, sys

# Append root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Change directory to root
from organization import file_org as f_org

# Add local path back to paths variables
sys.path.append(os.path.join(f_org.root, "ingest"))
