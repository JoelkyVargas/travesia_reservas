# Travesía Reservas v2

## Flujo recomendado en PowerShell
```powershell
& "C:\Users\jvz16\anaconda3\python.exe" -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data
python manage.py runserver
```

## Roles
- Dueño: superusuario
- Staff / salonero: usuario `is_staff=True`

## URLs
- `/`
- `/reservar/`
- `/dashboard/`
- `/dashboard/reservas/`
- `/dashboard/configuracion/`
- `/dashboard/bloqueos/`
- `/dashboard/usuarios/`
- `/admin/`
