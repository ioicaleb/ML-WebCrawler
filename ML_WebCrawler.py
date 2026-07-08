import Login as login
import GSReadAndWrite as gs

# TODO: Set to automatically grab code from email
# TODO: Access round results
# TODO: Organize results
# TODO: Log results to a file
# TODO: Apply results directly to Google Sheets (?)
# TODO: Make headless once finished debugging

def main():
    while True:
        option = input("Do you want to test login, sheets, quit?: ")
        if option == "login":
            login.Login()
        elif option == "sheets":
            gs.read_sheet()
        elif option == "quit":
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()