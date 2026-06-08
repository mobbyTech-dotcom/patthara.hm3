"""
คำสั่ง: python manage.py create_staff_user

สร้าง user ใหม่ที่เป็น staff หรืออัปเกรด user ที่มีอยู่แล้วให้เป็น staff
ใช้สำหรับให้ทีมงานหลายคนเข้า admin-panel ได้
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'สร้าง staff user ใหม่ หรืออัปเกรด user ที่มีอยู่ให้เป็น staff'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='ชื่อผู้ใช้')
        parser.add_argument('--password', type=str, help='รหัสผ่าน')
        parser.add_argument('--promote',  type=str, help='ชื่อ user ที่มีอยู่แล้ว (อัปเกรดเป็น staff)')

    def handle(self, *args, **options):
        # ── กรณีอัปเกรด user ที่มีอยู่แล้ว ──────────────────────────────
        if options['promote']:
            username = options['promote']
            try:
                user = User.objects.get(username=username)
                user.is_staff = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ อัปเกรด "{username}" เป็น staff เรียบร้อย')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ ไม่พบ user "{username}"')
                )
            return

        # ── กรณีสร้าง user ใหม่ ──────────────────────────────────────────
        username = options['username'] or os.environ.get('STAFF_USERNAME')
        password = options['password'] or os.environ.get('STAFF_PASSWORD')

        if not username or not password:
            self.stdout.write(
                self.style.ERROR(
                    '❌ ต้องระบุ --username และ --password\n'
                    '   หรือตั้ง ENV: STAFF_USERNAME และ STAFF_PASSWORD'
                )
            )
            return

        if User.objects.filter(username=username).exists():
            # ถ้ามีอยู่แล้ว แค่อัปเกรดเป็น staff
            user = User.objects.get(username=username)
            user.is_staff = True
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ อัปเดต "{username}" — is_staff=True, รหัสผ่านอัปเดตแล้ว')
            )
        else:
            User.objects.create_user(
                username=username,
                password=password,
                is_staff=True,
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ สร้าง staff user "{username}" เรียบร้อย')
            )
