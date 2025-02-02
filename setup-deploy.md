# Deploying Django with Gunicorn, Nginx,Celery,Redis and MSSQL on Ubuntu 24.04

## Setting up Gunicorn

1.Test gunicorn with django by running the following command inside the django project folder

```bash
gunicorn --bind 0.0.0.0:8800 alpha.wsgi:application
```

2.Lets daemonise the gunicorn
i.Open a new gunicorn.service file

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

ii.Copy the following lines with appropriate modifications

```bash
[Unit]
Description=gunicorn service
After=network.target

[Service]
User=bria
Group=www-data
WorkingDirectory=/home/bria/mine-apps/
ExecStart=/home/bria/mine-apps/env/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/bria/mine-apps/mine-apps.sock alpha.wsgi:application

[Install]
WantedBy=multi-user.target
```

iii.Enable the daemon

```bash
  sudo systemctl start gunicorn.service
  sudo systemctl enable gunicorn.service
  sudo systemctl status gunicorn.service
```

iv.If something went wrong, do

```bash
journalctl -u gunicorn
```

If journalctl isnt found, sudo apt install journalctl

v.If you do any changes to your django application, reload the gunicorn server by

```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

## Setting up Nginx

1.Create a new configuration file for nginx

```bash
sudo nano /etc/nginx/sites-available/mine-apps
```

2.Copy following lines with appropriate modifications

```bash
server {
listen 80;
 server_name 10.50.2.145;
location = /favicon.ico {access_log off;log_not_found off;}

        location /static/ {
            alias /home/bria/mine-apps/static/;
        }

        location /media/ {
            alias /home/bria/mine-apps/media/;
        }

        location / {
            include proxy_params;
            proxy_pass http://unix:/home/bria/mine-apps/mine-apps.sock;
        }
     }
```

3.Link the configuration so that nginx can recognise

```bash
sudo ln -s /etc/nginx/sites-available/mine-apps /etc/nginx/sites-enabled/
```

4.Check whether everything is fine

```bash
sudo nginx -t
```

5.Once everything is done, restart nginx

```bash
sudo systemctl restart nginx
```

## Setting up Celery

1.Create a new configuration file for celery

```bash
sudo nano /etc/systemd/system/celery.service
```

2.Copy following lines with appropriate modifications

```bash
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=bria
Group=www-data
WorkingDirectory=/home/bria/mine-apps
ExecStart=/home/bria/mine-apps/env/bin/celery -A alpha worker --loglevel=info
ExecStop=/home/bria/mine-apps/env/bin/celery -A alpha control shutdown
Restart=always
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target

```

## Setting up Beat (Opsional)

1.Create a new configuration file for celery

```bash
sudo nano /etc/systemd/system/celery-beat.service
```

2.Copy following lines with appropriate modifications

```bash
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=bria
WorkingDirectory=/home/bria/mine-apps
ExecStart=/home/bria/mine-apps/env/bin/celery -A alpha worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

## After Setting up

```bash
sudo systemctl daemon-reload
```

1. Run Redis server

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

redis status :

```bash
sudo systemctl status redis-server
```

Untuk memverifikasi Redis berjalan:

```bash
sudo systemctl status redis
```

2. Jalankan Nginx

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

Untuk memeriksa status Nginx:

```bash
sudo systemctl status nginx
```

Jika ada perubahan pada konfigurasi Nginx, lakukan pengecekan dan reload:

```bash
sudo nginx -t # Mengecek validitas konfigurasi Nginx
sudo systemctl reload nginx # Memuat ulang konfigurasi Nginx tanpa menghentikan layanan
```

3. Jalankan Gunicorn

```bash
sudo systemctl start gunicorn.service
sudo systemctl enable gunicorn.service
```

Periksa statusnya:

```bash
sudo systemctl status gunicorn.service
```

4. Jalankan Celery

```bash
sudo systemctl start celery
sudo systemctl enable celery
```

Jika Anda menggunakan Celery Beat (scheduler untuk tugas berkala), jalankan juga:

```bash
sudo systemctl start celery-beat
sudo systemctl enable celery-beat
```

Cek Status Service:

```bash
sudo systemctl status celery
sudo systemctl status celery-beat
```

Cek Log Celery / Jalankan Celery Secara Manual (tetsing)
/home/bria/mine-apps/env/bin/celery -A your_project_name worker --loglevel=info

```bash
/home/bria/mine-apps/env/bin/celery -A alpha worker --loglevel=info
```

Cek Log Layanan / Cek Log Celery

```bash
sudo journalctl -u celery.service -n 50
sudo journalctl -u celery.service -f
```

Pastikan Anda sudah memberikan izin yang benar pada direktori tersebut:

```bash
sudo chown -R bria:www-data /home/bria/mine-apps
```

Cek Timeout dan Pengaturan Sistem

```
TimeoutSec=600
```

## Reload daemon dan restart layanan:

```
sudo systemctl daemon-reload
sudo systemctl restart celery.service
```

## Note :

Jika mengedit pengaturan yang berkaitan dengan NGINX atau Gunicorn, seperti konfigurasi port, worker, atau pengaturan lainnya,
maka perlu merestart keduanya agar perubahan yang lakukan dapat diterapkan.

Berikut adalah cara merestart NGINX dan Gunicorn setelah mengedit pengaturan:

```bash
sudo systemctl restart nginx
sudo systemctl restart gunicorn
``
```

Periksa Status NGINX dan Gunicorn

```bash
sudo systemctl status nginx
sudo systemctl status gunicorn
```

Jika statusnya active (running), berarti layanan berjalan dengan baik.
