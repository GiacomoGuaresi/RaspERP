#!/bin/bash

echo "Updating system and installing required packages..."
sudo apt update && sudo apt install -y python3 python3-pip chromium-browser unclutter

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo "Creating Flask systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/flask_app.service
[Unit]
Description=Flask App
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/myflaskapp
ExecStart=/usr/bin/python3 /home/pi/myflaskapp/run.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling Flask service..."
sudo systemctl daemon-reload
sudo systemctl enable flask_app
sudo systemctl start flask_app

echo "Configuring Chromium kiosk mode..."
mkdir -p ~/.config/lxsession/LXDE-pi/
cat <<EOF >> ~/.config/lxsession/LXDE-pi/autostart
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --noerrdialogs --disable-infobars --kiosk http://127.0.0.1:5000/Inventory/codereader
EOF

echo "Setup complete! Rebooting now..."
sudo reboot
