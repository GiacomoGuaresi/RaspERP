# run.py
import os
import sys
import secrets
from app import create_app

def load_or_create_secret_key(filename=".secret_key"):
    if not os.path.exists(filename):
        secret = secrets.token_hex(32)
        with open(filename, "w") as f:
            f.write(secret)
        print(f"Secret key generated and saved to {filename}")
    else:
        with open(filename, "r") as f:
            secret = f.read().strip()
    return secret

app = create_app()

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1].upper() == "--DEV":
        app.secret_key = 'DEBUG_SECRET_KEY'
        app.run(debug=True)
    else: 
        app.secret_key = load_or_create_secret_key()
        app.run(host='0.0.0.0', port=80)
