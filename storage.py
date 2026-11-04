def load_passwords():
    secret_settings_passcode = []
    settings_passcode = []
    try:
        with open("secret.txt", "r") as f:
            file = f.readlines()
            for i in file[0].strip().split(","):
                secret_settings_passcode.append(int(i))
            for i in file[1].strip().split(","):
                settings_passcode.append(int(i))
    except (OSError, ValueError) as e:
        print("Error opening secret.txt:", e)
        # Created secret.txt, but passwords are default
        with open("secret.txt", "w") as f:
            f.write("1, 1, 1, 1, 1, 1\n2, 2, 2, 2, 2, 2")
        secret_settings_passcode = [1, 1, 1, 1, 1, 1]
        settings_passcode = [2, 2, 2, 2, 2, 2]
    return secret_settings_passcode, settings_passcode


def save_history(to_save):
    with open("history.txt", "w") as f:
        for line in to_save:
            f.write(line + "\n")


def load_history():
    records = []
    try:
        with open("history.txt", "r") as f:
            for line in f:
                records.append(line.strip())
    except OSError as e:
        print("Error reading history.txt:", e)
    return records
