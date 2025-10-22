import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from app import app

# Export the Flask app for Vercel
application = app

# For Vercel compatibility
if __name__ == "__main__":
    app.run()
