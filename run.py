# run.py
import sys
from app import create_app

app = create_app()

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1].upper() == "--DEV":
        app.secret_key = 'DEBUG'
        app.run(debug=True)
    else: 
        app.secret_key = '09041cb63f198147e7f68ef9084dc7e16d5aa4f65b3d6e7701b0963b95beda09'
        app.run(host='0.0.0.0', port=80)