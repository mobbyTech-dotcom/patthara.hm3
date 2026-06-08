#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# ── สร้าง/อัปเดต superuser หลัก (เจ้าของร้าน) ──────────────────────────
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
if not username or not password:
    print('DJANGO_SUPERUSER_USERNAME / PASSWORD not set — skipping')
else:
    u, created = User.objects.get_or_create(username=username)
    u.set_password(password)
    u.email = email
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print('Superuser ready:', username, '(created=' + str(created) + ')')
"

# ── สร้าง staff user เพิ่มเติม (ทีมงาน) สูงสุด 5 คน ─────────────────────
# วิธีตั้งค่าใน Render Environment Variables:
#   STAFF_USER_1=username:password
#   STAFF_USER_2=username:password
#   ...ถึง STAFF_USER_5
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
for i in range(1, 6):
    val = os.environ.get(f'STAFF_USER_{i}', '')
    if not val or ':' not in val:
        continue
    username, password = val.split(':', 1)
    username = username.strip()
    password = password.strip()
    if not username or not password:
        continue
    u, created = User.objects.get_or_create(username=username)
    u.set_password(password)
    u.is_staff = True
    u.save()
    print(f'Staff user ready: {username} (created={created})')
"

echo "Build completed: $(date)"
