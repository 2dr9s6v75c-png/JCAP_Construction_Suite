from services.password_service import hash_password

print("Creating admin password hash...")
print()

password = "admin123"

hashed = hash_password(password)

print("Password :", password)
print("Hash :")
print(hashed)