import os
import getpass
from secrets import compare_digest

from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.utils.separators import show_separators, show_center_text_with_separators


def prompt_for_access_coordinator():
    access_coordinator = None
    action = "decrypted"
    print(show_separators())
    print(show_center_text_with_separators("Loading data..."))
    while True:
        if os.path.exists("data/access_data.enc"):
            print("We found the configuration file. What do you want to do with it?")
            print("1. Decrypt the data.")
            print("2. Delete the data and create a new one.")
            print("3. Exit.")
            opt = input("Enter the number of the option you want to perform: ")
            if opt == '1':
                password = getpass.getpass(prompt="Enter your password: ")
                access_coordinator = AccessCoordinator(password.encode())
                break
            elif opt.lower() == '2':
                while True:
                    opt_select = input("Are you sure you want to delete the data and create a new one? (y/n): ")
                    if opt_select.lower() == 'y':
                        print("Please enter a password to encrypt the data.")
                        password = getpass.getpass(prompt="Enter your password: ")
                        password_confirm = getpass.getpass(prompt="Confirm your password: ")
                        os.remove("data/access_data.enc")
                        if compare_digest(password, password_confirm):
                            print("The data has been deleted and a new password has been set.")
                            access_coordinator = AccessCoordinator(password.encode())
                            break
                        else:
                            print("Passwords do not match.")
                    elif opt_select.lower() == 'n':
                        break
                    else:
                        print("Invalid option.")
                break
            elif opt == '3':
                print(show_separators())
                print(show_center_text_with_separators("Exiting..."))
                print(show_separators())
                exit(0)
            else:
                print("Invalid option.")
        else:
            print("No data found.")
            print("Please enter a password to encrypt the data.")
            password = getpass.getpass(prompt="Enter your password: ")
            password_confirm = getpass.getpass(prompt="Confirm your password: ")
            if compare_digest(password, password_confirm):
                access_coordinator = AccessCoordinator(password.encode())
                break
    print(show_separators())
    print(show_center_text_with_separators(f"The information has been {action} successfully."))
    print("A qr code for authentication has been generated in the path: data/qr_code.png")
    print(show_separators() + "\n")
    return access_coordinator
