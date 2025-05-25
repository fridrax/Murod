# config.py

import os

DB_URI = os.environ.get("DB_URI", "postgresql://sg_hotline_db_user:EdqwmK2EvU2gN6IOXTAG2jEw6oNoTR6b@dpg-d0n14515pdvs7386kdi0-a/sg_hotline_db")
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "123456")
