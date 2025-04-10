#!/bin/bash

echo "Updating system and installing required packages..."
sudo apt update && sudo apt install -y python3 python3-pip chromium-browser unclutter sqlite3

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Get current directory (script execution folder)
SCRIPT_DIR=$(pwd)

echo "Creating Flask systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/RaspERP.service
[Unit]
Description=RaspERP
After=network.target

[Service]
User=root
WorkingDirectory=${SCRIPT_DIR}
ExecStart=/usr/bin/python3 ${SCRIPT_DIR}/run.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling RaspERP service..."
sudo systemctl daemon-reload
sudo systemctl enable RaspERP
sudo systemctl start RaspERP

echo "Setting up SQLite database..."

DB_PATH="${SCRIPT_DIR}/database.db"
SQL_TEMPLATE="${SCRIPT_DIR}/db_template.sql"

if [ ! -f "$DB_PATH" ]; then
    echo "Creating database from template..."
    sudo sqlite3 "$DB_PATH" < "$SQL_TEMPLATE"
    echo "Database created successfully!"
else
    echo "Database already exists, skipping creation."
fi

echo "ALL DONE!"