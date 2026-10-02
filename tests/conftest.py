import os

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-only-for-pytest",
)
