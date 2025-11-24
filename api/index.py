"""# api/index.py
# Vercel serverless function entry — imports and exposes the Flask app from app.py

from app import app  # import the Flask app object from app.py

# Export both names commonly recognized by WSGI runtimes
application = app
# 'app' is available by import above
"""