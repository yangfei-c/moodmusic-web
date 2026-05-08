# EmoMMWeb Droplet / Cloud Server Migration Guide

This guide deploys EmoMMWeb on a persistent cloud server such as DigitalOcean Droplet, Tencent Cloud CVM/Lighthouse, or Baidu Cloud BCC.

The App Platform deployment can stay online while this server is configured.

## 1. Recommended server

Minimum recommended for the current 3GB checkpoint:

- Ubuntu 22.04 or 24.04
- 8 GB RAM preferred
- 4 vCPU preferred
- 80 GB disk or larger

A 4 GB RAM server may work only with swap and can still be unstable for `last.ckpt`.

## 2. Project layout on server

Use this layout:

```text
/home/emo/EmoMMWeb/
├── backend/
├── frontend/
└── data/
    ├── semantic_db.json
    └── last.ckpt
```

The audio files should remain in object storage such as DigitalOcean Spaces / Tencent COS / Baidu BOS. Do not copy the full MP3 library to the server.

## 3. Install system packages

```bash
sudo apt update
sudo apt install -y git curl nginx python3 python3-venv python3-pip nodejs npm
```

If the default Node.js is too old for Vite, install Node.js 20 with NodeSource.

## 4. Clone repository

```bash
cd /home
sudo mkdir -p /home/emo
sudo chown -R $USER:$USER /home/emo
cd /home/emo
git clone https://github.com/yangfei-c/EmoMMWeb.git
cd EmoMMWeb
```

## 5. Download runtime data

```bash
mkdir -p data
curl -L "https://emmrmusic.sfo3.cdn.digitaloceanspaces.com/data/semantic_db.json" -o data/semantic_db.json
curl -L "https://emmrmusic.sfo3.cdn.digitaloceanspaces.com/data/last.ckpt" -o data/last.ckpt
ls -lh data
```

Expected:

```text
semantic_db.json
last.ckpt
```

## 6. Install backend

```bash
cd /home/emo/EmoMMWeb/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Test backend manually:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

In another shell:

```bash
curl http://127.0.0.1:8080/health
```

Expected:

```json
{"status":"ok"}
```

## 7. Build frontend

```bash
cd /home/emo/EmoMMWeb/frontend
npm install
npm run build
```

Expected output directory:

```text
frontend/dist/
```

## 8. Create backend systemd service

```bash
sudo nano /etc/systemd/system/emommweb-backend.service
```

Paste:

```ini
[Unit]
Description=EmoMMWeb Backend
After=network.target

[Service]
WorkingDirectory=/home/emo/EmoMMWeb/backend
ExecStart=/home/emo/EmoMMWeb/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable emommweb-backend
sudo systemctl start emommweb-backend
sudo systemctl status emommweb-backend
```

View logs:

```bash
journalctl -u emommweb-backend -f
```

## 9. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/emommweb
```

Paste, replacing `SERVER_NAME_HERE` with the server IP or domain:

```nginx
server {
    listen 80;
    server_name SERVER_NAME_HERE;

    root /home/emo/EmoMMWeb/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

Enable Nginx site:

```bash
sudo ln -sf /etc/nginx/sites-available/emommweb /etc/nginx/sites-enabled/emommweb
sudo nginx -t
sudo systemctl restart nginx
```

Open:

```text
http://SERVER_IP/
```

Test backend through Nginx:

```text
http://SERVER_IP/api/health
```

## 10. Optional: enable swap for 4GB RAM servers

```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## 11. Optional: HTTPS with Certbot

After pointing a domain to the server IP:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d YOUR_DOMAIN
```

## 12. Cutover checklist

Before stopping App Platform:

- `http://SERVER_IP/api/health` returns ok
- frontend loads at `http://SERVER_IP/`
- `/api/recommend` returns recommendations
- audio playback works
- `journalctl -u emommweb-backend -f` has no crash loop
- App Platform remains online until the new server passes all tests
