from functools import lru_cache

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from napari_dashboard.db_update.__main__ import main as db_update_main
from napari_dashboard.get_webpage.__main__ import main as get_webpage_main


@lru_cache
def authenticate_and_get_drive():
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

    return GoogleDrive(gauth)


def main():
    drive = authenticate_and_get_drive()
    file_list = drive.ListFile(
        {"q": "title='dashboard.db' and trashed=false"}
    ).GetList()
    file = file_list[0]
    print("Downloading database")
    file.GetContentFile("dashboard.db")
    print("Updating database")
    db_update_main(["dashboard.db"])
    print("generating webpage")
    get_webpage_main(["webpage", "dashboard.db"])
    print("Uploading database")
    file.SetContentFile("dashboard.db")
    file.Upload()


if __name__ == "__main__":
    main()
