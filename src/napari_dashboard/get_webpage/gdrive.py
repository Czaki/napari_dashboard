import logging
import os.path

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from napari_dashboard.db_update.__main__ import main as db_update_main
from napari_dashboard.get_webpage.__main__ import main as get_webpage_main


def login_with_local_webserver():
    logging.info("Using local webserver")

    gauth = GoogleAuth()
    # Try to load saved client credentials
    gauth.LoadCredentialsFile("credentials.json")
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    gauth.SaveCredentialsFile("credentials.json")

    return gauth


def login_with_service_account():
    """
    Google Drive service with a service account.
    note: for the service account to work, you need to share the folder or
    files with the service account email.

    :return: google auth
    """
    # Define the settings dict to use a service account
    # We also can use all options available for the settings dict like
    # oauth_scope,save_credentials,etc.
    logging.info("Using service account")
    settings = {
        "client_config_backend": "service",
        "service_config": {"client_json_file_path": "service-secrets.json"},
    }
    # Create instance of GoogleAuth
    gauth = GoogleAuth(settings=settings)
    # Authenticate
    gauth.ServiceAuth()
    return gauth


def get_db_file():
    if os.path.exists("service-secrets.json"):
        gauth = login_with_service_account()
    else:
        gauth = login_with_local_webserver()
    drive = GoogleDrive(gauth)
    file_list = drive.ListFile(
        {"q": "title='dashboard.db' and trashed=false"}
    ).GetList()
    if file_list:
        return file_list[0]
    return None


def main():
    print("Downloading database")
    db_file = get_db_file()
    if db_file is not None:
        db_file.GetContentFile("dashboard.db")
    else:
        print("Database not found")

    print("Updating database")
    db_update_main(["dashboard.db"])
    print("generating webpage")
    get_webpage_main(["webpage", "dashboard.db"])
    print("Uploading database")
    file = get_db_file()
    file.SetContentFile("dashboard.db")
    file.Upload()


if __name__ == "__main__":
    main()
