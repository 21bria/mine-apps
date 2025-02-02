# Deploying Django with Nginx,Redis,Gunicorn,Celery,and MsSQL on Ubuntu 24.04

## Setting up software

1. Update ubuntu software repository
2. Install
   1. nginx - Serve our website
   2. redis server
   3. mysql-server and libmysqlclient-dev - For database
   4. Python 3
   5. virtualenv - Virtual environment for our python application

Update Sistem

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

Install Nginx

```bash
sudo apt-get install nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

Install Redis server

```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

Instal Python 3.12

```bash
$ sudo add-apt-repository ppa:deadsnakes/ppa
$ sudo apt-get update
$ sudo apt-get install python3.12 python3.12-venv python3.12-dev
```

Install Dependensi MySQL/MariaDB

```bash
sudo apt install default-libmysqlclient-dev
```

```bash
$ sudo apt-get install -y python3-pip python3-dev libffi-dev
```

Tambahkan Repositori Microsoft

```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository "$(curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list)"
sudo apt-get update

```

Instal MSSQL Server dan Tools

```bash
sudo apt-get install -y mssql-tools unixodbc-dev
```

Tambahkan ke PATH

```bash
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
source ~/.bashrc
```

Instal ODBC Driver

```bash
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

## Installing python libraries

1. Create a directory to hold all django apps (Eg. django)
1. Clone project from github
1. Create a virtual environment
1. Install Library dari requirements.txt
1. Install Library gunicorn

```bash
$ mkdir mine_project
$ cd mine_project
$ git clone https://github.com/21bria/mine-apps.git
$ python3 -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ pip install gunicorn
```

Also install any other dependencies needed

## Setting up the firewall

We'll disable access to the server on all ports except 8800 for now. Later on we'll remove this give access to all ports that nginx needs

```bash
$ sudo ufw default deny
$ sudo ufw enable
$ sudo ufw allow 8800
```

1. Modify the `settings.py` file to use the newly created database.

```python
DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'domain.name', 'ip-address']

...

DATABASES = {

}

...

STATIC_URL = '/static/'
STATIC_ROOT=os.path.join(BASE_DIR, 'static/')

MEDIA_URL='/media/'
MEDIA_ROOT=os.path.join(BASE_DIR, 'media/')

```

Add appropriate ip address or domain name to allowed hosts.

2. Make database migrations

```bash
(venv) $ python manage.py makemigrations
(venv) $ python manage.py migrate
(venv) $ python manage.py collectstatic
```

These commands create all required tables in the new database created and also collects all static files to a static folder under django_project directory.

3. Run the development server to check whether everything is working fine.

```bash
python manage.py runserver
```

#### Final Folder structure

```
\home\<user>\django\
|
|--- venv
|
|--- django_project
    |
    |--- manage.py
    |--- django_project
    |    |
    |    |--- __init__.py
    |    |--- urls.py
    |    |--- settings.py
    |    |--- wsgi.py
    |
    |--- static
    |
    |--- media
    |
    |--- django_project.sock

```

---
