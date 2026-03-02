import sys
import os

# add the web/ directory to Python's module search path
# this allows all test files to do "from run import create_app"
# regardless of which subdirectory they are in
sys.path.insert(0, os.path.dirname(__file__))