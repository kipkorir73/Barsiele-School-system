import logging
import os
from auth import create_user, validate_login
# Other imports as needed

if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(filename='logs/app.log', level=logging.INFO)

def main():
    print("School Management CLI")
    while True:
        choice = input("1. Create User\n2. Login\n3. Exit\n")
        if choice == '1':
            username = input("Username: ")
            pw = input("Password: ")
            role = input("Role (admin/clerk): ")
            create_user(username, pw, role)
            print("User created.")
        elif choice == '2':
            username = input("Username: ")
            pw = input("Password: ")
            user = validate_login(username, pw)
            if user:
                print(f"Logged in as {user['role']}")
                # Add more CLI options for testing
            else:
                print("Invalid credentials")
        elif choice == '3':
            break

if __name__ == "__main__":
    main()