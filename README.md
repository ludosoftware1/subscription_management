# Documentação Tema
https://themesbrand.com/velzon/docs/django/getting-started.html

# Comandos
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
pip freeze > requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py seed_data

# Melhorias

# Tags
git tag -a v1.0.0 -m "Lançamento da versão 1.0.0"
git push --tags

# Comandos Railway
chmod +x build.sh && ./build.sh
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn velzon.wsgi:application --bind 0.0.0.0:$PORT

npm install -g @railway/cli
curl -fsSL https://railway.com/install.sh | sh
railway link -p 0788ed9a-d7dd-4627-b4c0-489ae1d5ff7f
railway login
railway run "comando"