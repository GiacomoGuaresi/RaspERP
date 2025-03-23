# run.py
import sys
from app import create_app

app = create_app()

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--DEBUG":
        app.run(debug=True)
    else: 
        app.run(host='0.0.0.0', port=80)