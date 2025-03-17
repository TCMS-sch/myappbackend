import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/myapp'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set the environment variable for Flask
os.environ['FLASK_APP'] = 'server.py'

# Import Flask app
from server import app as application
