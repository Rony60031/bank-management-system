import sqlite3

DB_NAME = "bank.db"


def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0 CHECK (balance >= 0)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
            """
        )


def read_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a whole number.")


def read_amount(prompt):
    while True:
        try:
            value = round(float(input(prompt)), 2)
        except ValueError:
            print("Please enter a number.")
            continue
        if value <= 0:
            print("Amount must be greater than zero.")
            continue
        return value


def get_account(conn, acc_id):
    return conn.execute(
        "SELECT id, name, balance FROM accounts WHERE id = ?", (acc_id,)
    ).fetchone()


def log_transaction(conn, acc_id, kind, amount, note=""):
    conn.execute(
        "INSERT INTO transactions (account_id, type, amount, note) "
        "VALUES (?, ?, ?, ?)",
        (acc_id, kind, amount, note),
    )


def create_account():
    name = input("Account holder name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    while True:
        try:
            initial = round(float(input("Initial deposit (0 or more): ")), 2)
        except ValueError:
            print("Please enter a number.")
            continue
        if initial < 0:
            print("Initial deposit cannot be negative.")
            continue
        break
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (name, balance) VALUES (?, ?)", (name, initial)
        )
        acc_id = cur.lastrowid
        if initial > 0:
            log_transaction(conn, acc_id, "DEPOSIT", initial, "Initial deposit")
    print(f"Account created. Your account number is {acc_id}.")


def list_accounts():
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, balance FROM accounts ORDER BY id"
        ).fetchall()
    if not rows:
        print("No accounts found.")
        return
    print(f"\n{'Acc No':<10}{'Name':<22}{'Balance':<12}")
    print("-" * 44)
    for acc_id, name, balance in rows:
        print(f"{acc_id:<10}{name:<22}{balance:<12.2f}")


def deposit():
    acc_id = read_int("Account number: ")
    amount = read_amount("Deposit amount: ")
    with connect() as conn:
        if not get_account(conn, acc_id):
            print("Account not found.")
            return
        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount, acc_id),
        )
        log_transaction(conn, acc_id, "DEPOSIT", amount)
        balance = get_account(conn, acc_id)[2]
    print(f"Deposited {amount:.2f}. New balance: {balance:.2f}")


def withdraw():
    acc_id = read_int("Account number: ")
    amount = read_amount("Withdraw amount: ")
    with connect() as conn:
        account = get_account(conn, acc_id)
        if not account:
            print("Account not found.")
            return
        if account[2] < amount:
            print(f"Insufficient balance. Current balance: {account[2]:.2f}")
            return
        conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?",
            (amount, acc_id),
        )
        log_transaction(conn, acc_id, "WITHDRAW", amount)
        balance = get_account(conn, acc_id)[2]
    print(f"Withdrew {amount:.2f}. New balance: {balance:.2f}")


def transfer():
    from_id = read_int("From account number: ")
    to_id = read_int("To account number: ")
    if from_id == to_id:
        print("Cannot transfer to the same account.")
        return
    amount = read_amount("Transfer amount: ")
    # One connection, one transaction: both updates succeed or neither does.
    with connect() as conn:
        sender = get_account(conn, from_id)
        receiver = get_account(conn, to_id)
        if not sender or not receiver:
            print("One or both accounts were not found.")
            return
        if sender[2] < amount:
            print(f"Insufficient balance. Current balance: {sender[2]:.2f}")
            return
        conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?",
            (amount, from_id),
        )
        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount, to_id),
        )
        log_transaction(conn, from_id, "TRANSFER_OUT", amount, f"To account {to_id}")
        log_transaction(conn, to_id, "TRANSFER_IN", amount, f"From account {from_id}")
    print(f"Transferred {amount:.2f} from {from_id} to {to_id}.")


def check_balance():
    acc_id = read_int("Account number: ")
    with connect() as conn:
        account = get_account(conn, acc_id)
    if not account:
        print("Account not found.")
        return
    print(f"Account {account[0]} ({account[1]}) balance: {account[2]:.2f}")


def history():
    acc_id = read_int("Account number: ")
    with connect() as conn:
        if not get_account(conn, acc_id):
            print("Account not found.")
            return
        rows = conn.execute(
            "SELECT created_at, type, amount, note FROM transactions "
            "WHERE account_id = ? ORDER BY id",
            (acc_id,),
        ).fetchall()
    if not rows:
        print("No transactions yet.")
        return
    print(f"\n{'Date':<22}{'Type':<14}{'Amount':<12}{'Note':<20}")
    print("-" * 68)
    for created_at, kind, amount, note in rows:
        print(f"{created_at:<22}{kind:<14}{amount:<12.2f}{note or '':<20}")


def main():
    create_tables()
    actions = {
        "1": create_account,
        "2": list_accounts,
        "3": deposit,
        "4": withdraw,
        "5": transfer,
        "6": check_balance,
        "7": history,
    }
    while True:
        print("\n=== Bank Management System ===")
        print("1. Create Account")
        print("2. List Accounts")
        print("3. Deposit")
        print("4. Withdraw")
        print("5. Transfer")
        print("6. Check Balance")
        print("7. Transaction History")
        print("0. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()