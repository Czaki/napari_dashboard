import bz2
import hashlib
import logging
import os.path
from pathlib import Path

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


def get_auth():
    if os.path.exists("service-secrets.json"):
        gauth = login_with_service_account()
    else:
        gauth = login_with_local_webserver()
    return gauth


def get_or_create_gdrive_file(drive, file_name):
    file_list = drive.ListFile(
        {"q": f"title='{file_name}' and trashed=false"}
    ).GetList()
    if file_list:
        return file_list[0]
    folders = drive.ListFile(
        {
            "q": "title='napari_dashboard' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        }
    ).GetList()
    for folder in folders:
        if folder["title"] == "napari_dashboard":
            return drive.CreateFile(
                {"title": file_name, "parents": [{"id": folder["id"]}]}
            )
    raise ValueError("Folder not found")


def upload_upload_xlsx_dump():
    drive = GoogleDrive(get_auth())
    file = get_or_create_gdrive_file(drive, "napari_dashboard.xlsx")
    file.SetContentFile("webpage/napari_dashboard.xlsx")
    file.Upload()


def upload_upload_db_dump():
    drive = GoogleDrive(get_auth())
    file = get_or_create_gdrive_file(drive, "dashboard.db.bz2")
    file.SetContentFile("dashboard.db.bz2")
    file.Upload()


def get_db_file():
    drive = GoogleDrive(get_auth())
    file_list = drive.ListFile(
        {"q": "title='dashboard.db.bz2' and trashed=false"}
    ).GetList()
    if file_list:
        return file_list[0]
    return None


def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def compress_file(original_file_path, compressed_file_path):
    with (
        open(original_file_path, "rb") as original_file,
        bz2.open(compressed_file_path, "wb") as compressed_file,
    ):
        compressed_file.writelines(original_file)


def uncompressed_file(compressed_file_path, original_file_path):
    with (
        bz2.open(compressed_file_path, "rb") as compressed_file,
        open(original_file_path, "wb") as original_file,
    ):
        original_file.writelines(compressed_file)


def fetch_database(db_path="dashboard.db"):
    logging.info("fetching database")

    db_path = Path(db_path)
    archive_path = db_path.with_suffix(".db.bz2")
    db_file = get_db_file()
    if db_file is not None:
        db_file.FetchMetadata(fields="md5Checksum")
        if not (
            archive_path.exists()
            and calculate_md5(archive_path) == db_file["md5Checksum"]
        ):
            logging.info("download database")

            db_file.GetContentFile(archive_path)
            logging.info("uncompressing database")
            uncompressed_file(archive_path, db_path)
    else:
        logging.info("Database not found")


def main():
    fetch_database()
    print("Updating database")
    db_update_main(["dashboard.db"])
    print("generating webpage")
    get_webpage_main(["webpage", "dashboard.db", "--no-excel-dump"])
    print("Compressing database")
    compress_file("dashboard.db", "dashboard.db.bz2")
    print("Uploading database")
    upload_upload_db_dump()
    # print("Uploading xlsx dump")
    # upload_upload_xlsx_dump()


if __name__ == "__main__":
    main()
