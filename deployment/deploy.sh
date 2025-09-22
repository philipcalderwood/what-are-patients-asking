#!/bin/bash

set -e  # Exit on any error

echo "MRPC Data Explorer - Direct Deployment"
echo "======================================"

# Interactive options at the beginning
echo ""
echo "Deployment Options:"
echo "1. Deploy and start application immediately"
echo "2. Deploy only (manual start)"
echo ""
read -p "Choose option (1 or 2): " DEPLOY_OPTION

# Configuration
SSH_HOST="data-explorer"
DEPLOY_DIR="mrpc-deploy"

# Step 1: Check required files
echo ""
echo "Step 1: Checking required files..."

if [[ ! -f "src/app.py" ]]; then
    echo "Error: src/app.py not found. Run from project root directory."
    exit 1
fi

if [[ ! -f "requirements-final.txt" ]]; then
    echo "Error: requirements-final.txt not found."
    exit 1
fi

if [[ ! -f "src/data/mrpc_new.db" ]]; then
    echo "Error: src/data/mrpc_new.db not found."
    exit 1
fi

echo "All required files found"

# Step 2: Setup remote directory structure
echo ""
echo "Step 2: Setting up remote directory structure..."

ssh "${SSH_HOST}" << 'EOF'
# Stop existing service and clean up old deployment
sudo systemctl stop mrpc.service || true

# IMPORTANT: Verify backup system is running and protected
echo "Verifying backup system protection..."
if sudo systemctl is-active --quiet mrpc-backup.timer; then
    echo "Backup timer is active and protected"
else
    echo "WARNING: Backup timer not active"
fi

# Ensure backup directories are protected (outside deployment path)
if [[ -d ~/mrpc-backups ]]; then
    echo "Backup directory protected at ~/mrpc-backups"
else
    echo "Creating backup directory for future use"
    mkdir -p ~/mrpc-backups
fi

# Remove old deployment
if [[ -d ~/mrpc/mrpc-deploy ]]; then
    rm -rf ~/mrpc/mrpc-deploy
fi

# Create clean deployment directory structure
mkdir -p ~/mrpc/mrpc-deploy/components
mkdir -p ~/mrpc/mrpc-deploy/pages  
mkdir -p ~/mrpc/mrpc-deploy/utilities
mkdir -p ~/mrpc/mrpc-deploy/services
mkdir -p ~/mrpc/mrpc-deploy/callbacks
mkdir -p ~/mrpc/mrpc-deploy/data

echo "Clean remote directory structure created"
EOF

# Step 3: Copy files directly via SCP
echo ""
echo "Step 3: Copying files to server..."

# Copy main application files
echo "Copying main application files..."
scp src/app.py "${SSH_HOST}:~/mrpc/${DEPLOY_DIR}/"
scp src/config.py "${SSH_HOST}:~/mrpc/${DEPLOY_DIR}/"
scp requirements-production.txt "${SSH_HOST}:~/mrpc/${DEPLOY_DIR}/requirements.txt"

# Copy directories
echo "Copying components..."
scp -r src/components/* "${SSH_HOST}:~/mrpc/${DEPLOY_DIR}/components/"

echo "Copying pages..."
scp -r src/pages/* "${SSH_HOST}:~/mrpc/${DEPLOY_DIR}/pages/"

echo "Copying utilities..."
scp -r src/utilities/* "${SSH_HOST}:~/mrpc/${DEPLOY_DIR}/utilities/"

echo "Copying services..."
scp -r src/services/* "${SSH_HOST}:~/mrpc/${DEPLOY_DIR}/services/"

echo "Copying callbacks..."
scp -r src/callbacks/* "${SSH_HOST}:~/mrpc/${DEPLOY_DIR}/callbacks/"

echo "Copying data..."
scp -r src/data/* "${SSH_HOST}:~/mrpc/${DEPLOY_DIR}/data/"

# Create startup script directly on server
echo "Creating startup script..."
ssh "${SSH_HOST}" << 'EOF'
cd ~/mrpc/mrpc-deploy

cat > start_mrpc.sh << 'STARTUP_EOF'
#!/bin/bash

# MRPC Data Explorer Startup Script
# Usage: ./start_mrpc.sh [port] [host] [workers]

PORT=${1:-3000}
HOST=${2:-0.0.0.0}
WORKERS=${3:-4}

echo "Starting MRPC Data Explorer"
echo "Port: $PORT | Host: $HOST | Workers: $WORKERS"

# Activate virtual environment
source .venv/bin/activate

# Start with gunicorn for production
echo "Starting with gunicorn..."
exec gunicorn -w $WORKERS -k gthread -b $HOST:$PORT app:server
STARTUP_EOF

chmod +x start_mrpc.sh
echo "Startup script created"
EOF

echo "All files copied successfully"

# Step 4: Setup Python environment and dependencies
echo ""
echo "Step 4: Setting up Python environment..."

ssh "${SSH_HOST}" << EOF
cd ~/mrpc/${DEPLOY_DIR}

# Setup Python environment
echo "Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-final.txt

echo "Dependencies installed"

# Check for systemd service and offer to create it
echo "Checking systemd service..."
if ! systemctl list-unit-files | grep -q "mrpc.service"; then
    echo "Creating systemd service for MRPC..."
    
    # Create systemd service file
    sudo tee /etc/systemd/system/mrpc.service > /dev/null << 'SYSTEMD_EOF'
[Unit]
Description=MRPC Data Explorer Dashboard
After=network.target

[Service]
Type=exec
User=ec2-user
WorkingDirectory=/home/ec2-user/mrpc/${DEPLOY_DIR}
Environment=PATH=/home/ec2-user/mrpc/${DEPLOY_DIR}/.venv/bin
ExecStart=/home/ec2-user/mrpc/${DEPLOY_DIR}/.venv/bin/gunicorn -w 4 -k gthread -b 0.0.0.0:3000 app:server
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable mrpc.service
    echo "Systemd service created and enabled"
else
    echo "Systemd service already exists"
    sudo systemctl daemon-reload
fi

# Clean up any processes running on port 3000
echo "Checking for processes on port 3000..."
PORT_PROCESSES=\$(sudo lsof -ti:3000 2>/dev/null || true)
if [[ -n "\$PORT_PROCESSES" ]]; then
    echo "Found processes on port 3000, cleaning up..."
    sudo kill -9 \$PORT_PROCESSES || true
    sleep 2
    echo "Port 3000 cleared"
else
    echo "Port 3000 is available"
fi

echo ""
echo "Ready to start:"
echo "cd ~/mrpc/${DEPLOY_DIR}"
echo "./start_mrpc.sh [port]"
echo "OR"
echo "sudo systemctl start mrpc.service"

EOF

# Step 5: Handle interactive start option
if [[ "$DEPLOY_OPTION" == "1" ]]; then
    echo ""
    echo "Starting application automatically..."
    
    ssh "${SSH_HOST}" << EOF
cd ~/mrpc/${DEPLOY_DIR}

echo "Starting MRPC via systemd service..."
sudo systemctl start mrpc.service
sleep 3

# Check service status
if systemctl is-active --quiet mrpc.service; then
    echo "MRPC service started successfully"
    echo "Service status: \$(systemctl is-active mrpc.service)"
    echo "Service logs: sudo journalctl -u mrpc.service -f"
else
    echo "Service failed to start. Check logs: sudo journalctl -u mrpc.service"
fi

echo "Access at: http://\$(curl -s ipinfo.io/ip):3000"
EOF
fi

# Step 6: Completion
echo ""
echo "Deployment Complete!"
echo "======================================"
echo "Server: ${SSH_HOST}"

if [[ "$DEPLOY_OPTION" == "1" ]]; then
    echo ""
    echo "Application is running:"
    echo "Access: http://your-server-ip:3000"
    echo "Stop: ssh ${SSH_HOST} 'sudo systemctl stop mrpc.service'"
    echo "Status: ssh ${SSH_HOST} 'sudo systemctl status mrpc.service'"
    echo "Logs: ssh ${SSH_HOST} 'sudo journalctl -u mrpc.service -f'"
else
    echo ""
    echo "To start the application:"
    echo "ssh ${SSH_HOST}"
    echo "cd ~/mrpc/${DEPLOY_DIR}"
    echo "sudo systemctl start mrpc.service"
fi

echo ""
echo "Management Commands:"
echo "sudo systemctl start mrpc.service    # Start service"
echo "sudo systemctl stop mrpc.service     # Stop service"
echo "sudo systemctl restart mrpc.service  # Restart service"
echo "sudo systemctl status mrpc.service   # Check status"
echo "sudo journalctl -u mrpc.service -f   # Follow logs"

echo ""
