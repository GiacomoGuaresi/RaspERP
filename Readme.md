# RaspERP

RaspERP is a simple Flask-based ERP designed to run on a Raspberry Pi.
The system allows you to manage a warehouse using barcodes and manage production orders for assembled and sub-assembled products.

## Features
- **Warehouse Management**: Track items using barcodes.
- **Production Orders**: Create and manage orders for assembled and sub-assembled products.
- **Web Interface**: Based on Flask for a simple, browser-accessible interface.
- **Raspberry Pi Compatible**: Optimized to run on low-power hardware.

## Requirements
- Raspberry Pi with Raspberry Pi OS
- Python 3
- Flask
- SQLite or PostgreSQL database
- Barcode scanner (optional)

## Installation
```bash
# Clone the repository
git clone https://github.com/your-user/rasperp.git
cd rasperp

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

## Usage
1. Access the ERP via browser at `http://<RASPBERRY_IP>:5000`
2. Register products and subassemblies in the warehouse.
3. Generate and manage production orders.
4. Scan barcodes to update item status.

## Contribute
Pull requests and bug reports are welcome! Make sure to open an issue to discuss any changes.

## License
This project is released under the MIT license.