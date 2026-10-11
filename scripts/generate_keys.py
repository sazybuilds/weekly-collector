import secrets
from cryptography.fernet import Fernet

def main():
    api_key = secrets.token_urlsafe(32)
    fernet_key = Fernet.generate_key().decode()

    print("=" * 60)
    print("[*] GENERATED APPLICATION SECRETS")
    print("=" * 60)
    print(f"API_KEY:         {api_key}")
    print(f"ENCRYPTION_KEY:  {fernet_key}")
    print("=" * 60)
    print("[!] IMPORTANT: Save the ENCRYPTION_KEY in a secure place!")
    print("    The same ENCRYPTION_KEY must be used across Streamlit/API and GitHub Actions.")
    print("=" * 60)

if __name__ == "__main__":
    main()
