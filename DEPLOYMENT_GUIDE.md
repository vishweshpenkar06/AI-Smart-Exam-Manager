# AI Smart Exam Manager — Deployment Guide

## 1. Prerequisites

- Python 3.9+
- Linux/Ubuntu server recommended (Nginx + Gunicorn)
- Git

## 2. Server Setup

```bash
# Clone the repository
git clone <repository-url>
cd ai_smart_exam_manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Configuration

Copy the example environment file and customize it:

```bash
cp .env.example .env
nano .env
```

Ensure you update `SECRET_KEY` and set `FLASK_ENV=production`.

## 4. Gunicorn Server Setup

Do not use the Flask development server (`app.run()`) in production. Use Gunicorn.

```bash
# Test Gunicorn locally
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

Create a systemd service file `/etc/systemd/system/exam_manager.service`:

```ini
[Unit]
Description=Gunicorn daemon for AI Exam Manager
After=network.target

[Service]
User=your_username
Group=www-data
WorkingDirectory=/path/to/ai_smart_exam_manager
Environment="PATH=/path/to/ai_smart_exam_manager/venv/bin"
ExecStart=/path/to/ai_smart_exam_manager/venv/bin/gunicorn --workers 4 --bind unix:exam_manager.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start exam_manager
sudo systemctl enable exam_manager
```

## 5. Nginx Configuration

Create an Nginx server block `/etc/nginx/sites-available/exam_manager`:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/ai_smart_exam_manager/exam_manager.sock;
    }

    # Serve static files directly
    location /static/ {
        alias /path/to/ai_smart_exam_manager/static/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/exam_manager /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 6. SSL Configuration (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com
```

## 7. Backups

A cron job can be configured to call the backup API endpoint, or you can use the built-in admin dashboard UI to trigger backups before making any significant database changes.
