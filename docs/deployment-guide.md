# Deployment Guide

This guide covers deploying SMCP in production environments, including systemd services, Docker containers, and reverse proxy configurations.

## 🚀 Production Deployment Options

### Option 1: System Service (Recommended for Linux)
Deploy SMCP as a system service for automatic startup and management.

### Option 2: Docker Container
Deploy SMCP in a containerized environment for consistency and isolation.

### Option 3: Reverse Proxy
Deploy behind nginx or Apache for SSL termination and load balancing.

## 🔧 System Service Deployment (Linux)

### 1. Create System User
```bash
# Create dedicated user for SMCP
sudo useradd -r -s /bin/false smcp
sudo mkdir -p /opt/smcp
sudo chown smcp:smcp /opt/smcp
```

### 2. Install SMCP
```bash
# Clone to system location
sudo git clone https://github.com/animusos/smcp.git /opt/smcp
cd /opt/smcp

# Install dependencies
sudo -u smcp python -m pip install --user -r requirements.txt
```

### 3. Create Systemd Service
Create `/etc/systemd/system/smcp.service`:

```ini
[Unit]
Description=SMCP Model Context Protocol Server
After=network.target

[Service]
Type=simple
User=smcp
Group=smcp
WorkingDirectory=/opt/smcp
Environment=PATH=/opt/smcp/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=MCP_PORT=8000
Environment=MCP_HOST=0.0.0.0
Environment=MCP_PLUGINS_DIR=/opt/smcp/smcp/plugins
ExecStart=/usr/bin/python smcp.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 4. Enable and Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable smcp

# Start service
sudo systemctl start smcp

# Check status
sudo systemctl status smcp

# View logs
sudo journalctl -u smcp -f
```

### 5. Service Management
```bash
# Stop service
sudo systemctl stop smcp

# Restart service
sudo systemctl restart smcp

# Reload configuration
sudo systemctl reload smcp

# Check service status
sudo systemctl is-active smcp
```

## 🐳 Docker Deployment

### 1. Create Dockerfile
Create `Dockerfile` in the SMCP root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone SMCP
RUN git clone https://github.com/animusos/smcp.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create plugin directory
RUN mkdir -p smcp/plugins

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/messages/ || exit 1

# Run SMCP
CMD ["python", "smcp.py", "--host", "0.0.0.0"]
```

### 2. Build and Run
```bash
# Build image
docker build -t smcp:latest .

# Run container
docker run -d \
    --name smcp \
    -p 8000:8000 \
    -v /path/to/plugins:/app/smcp/plugins \
    --restart unless-stopped \
    smcp:latest

# Check logs
docker logs -f smcp

# Check status
docker ps
```

### 3. Docker Compose
Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  smcp:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./plugins:/app/smcp/plugins
      - ./logs:/app/logs
    environment:
      - MCP_PORT=8000
      - MCP_HOST=0.0.0.0
      - MCP_PLUGINS_DIR=/app/smcp/plugins
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/messages/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - smcp
    restart: unless-stopped
```

## 🌐 Reverse Proxy Configuration

### Nginx Configuration
Create `/etc/nginx/sites-available/smcp`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration
    ssl_certificate /etc/nginx/ssl/smcp.crt;
    ssl_certificate_key /etc/nginx/ssl/smcp.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # Proxy to SMCP
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for SSE
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### Enable Nginx Site
```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/smcp /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## 🔒 Security Configuration

### Firewall Setup
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access to SMCP
sudo ufw enable

# iptables (CentOS/RHEL)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j DROP
sudo service iptables save
```

### SSL Certificate Generation
```bash
# Generate self-signed certificate (development)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/smcp.key \
    -out /etc/nginx/ssl/smcp.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# Let's Encrypt (production)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📊 Monitoring and Logging

### Log Rotation
Create `/etc/logrotate.d/smcp`:

```
/var/log/smcp/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 smcp smcp
    postrotate
        systemctl reload smcp
    endscript
}
```

### System Monitoring
```bash
# Monitor service status
watch -n 5 'systemctl status smcp'

# Monitor logs
tail -f /var/log/smcp/logs/mcp_server.log

# Monitor system resources
htop
iotop
```

### Health Checks
```bash
# Create health check script
cat > /usr/local/bin/smcp-health << 'EOF'
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/messages/)
if [ $response -eq 200 ]; then
    echo "SMCP is healthy"
    exit 0
else
    echo "SMCP is unhealthy (HTTP $response)"
    exit 1
fi
EOF

chmod +x /usr/local/bin/smcp-health

# Add to crontab for regular checks
echo "*/5 * * * * /usr/local/bin/smcp-health" | crontab -
```

## 🔄 Updates and Maintenance

### Service Updates
```bash
# Stop service
sudo systemctl stop smcp

# Backup configuration
sudo cp -r /opt/smcp /opt/smcp.backup.$(date +%Y%m%d)

# Update code
cd /opt/smcp
sudo -u smcp git pull origin main

# Install new dependencies
sudo -u smcp python -m pip install --user -r requirements.txt

# Start service
sudo systemctl start smcp

# Check status
sudo systemctl status smcp
```

### Docker Updates
```bash
# Pull latest image
docker pull smcp:latest

# Stop and remove old container
docker stop smcp
docker rm smcp

# Run new container
docker run -d \
    --name smcp \
    -p 8000:8000 \
    -v /path/to/plugins:/app/smcp/plugins \
    --restart unless-stopped \
    smcp:latest
```

## 🚨 Troubleshooting Production Issues

### Service Won't Start
```bash
# Check service status
sudo systemctl status smcp

# Check logs
sudo journalctl -u smcp -n 50

# Check permissions
ls -la /opt/smcp/
sudo chown -R smcp:smcp /opt/smcp/
```

### Performance Issues
```bash
# Check resource usage
top -p $(pgrep -f mcp_server)

# Check network connections
netstat -an | grep :8000

# Check disk space
df -h
```

### SSL Issues
```bash
# Test SSL configuration
openssl s_client -connect your-domain.com:443

# Check nginx configuration
sudo nginx -t

# Check certificate expiration
openssl x509 -in /etc/nginx/ssl/smcp.crt -text -noout | grep "Not After"
```

## 📋 Deployment Checklist

- [ ] System user created with appropriate permissions
- [ ] SMCP installed in system directory
- [ ] Systemd service configured and enabled
- [ ] Firewall rules configured
- [ ] Reverse proxy configured (if using)
- [ ] SSL certificates installed
- [ ] Log rotation configured
- [ ] Monitoring and health checks set up
- [ ] Backup procedures established
- [ ] Update procedures documented

---

**Need help with deployment?** Check the [Troubleshooting Guide](troubleshooting.md) or visit [animus.uno](https://animus.uno) for support.
