import os
from io import BytesIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


class GoogleDriveStorage:
    """Utility class for Google Drive storage operations"""

    # Google Drive folder ID for storing files
    DRIVE_FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]

    def __init__(self):
        """Initialize Google Drive API client"""
        self.service = self._get_drive_service()

    def _get_drive_service(self):
        """Create and return Google Drive API service"""
        # Path to service account JSON file
        service_account_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "service_account.json")

        # Create credentials from service account file
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=["https://www.googleapis.com/auth/drive"]
        )

        # Build and return the Drive service
        service = build("drive", "v3", credentials=credentials)
        return service

    def upload_file(self, file_path, file_name, mime_type=None, file_id=None):
        """
        Upload a file to Google Drive

        Args:
            file_path (str): Path to the file to upload
            file_name (str): Name for the file in Google Drive
            mime_type (str, optional): MIME type of the file
            file_id (str, optional): UUID to use as folder name

        Returns:
            dict: File metadata including id
        """
        # Create a folder with the file's UUID if it doesn't exist
        if file_id:
            folder_id = self._get_or_create_folder(file_id, parent_id=self.DRIVE_FOLDER_ID)
        else:
            folder_id = self.DRIVE_FOLDER_ID

        # File metadata
        file_metadata = {"name": file_name, "parents": [folder_id]}

        # Upload the file
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file = self.service.files().create(body=file_metadata, media_body=media, fields="id,name,mimeType,size").execute()

        return file

    def _get_or_create_folder(self, folder_name, parent_id=None):
        """
        Get or create a folder in Google Drive

        Args:
            folder_name (str): Name of the folder
            parent_id (str, optional): Parent folder ID

        Returns:
            str: Folder ID
        """
        # Try to find the folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = self.service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()

        # If folder exists, return its ID
        items = results.get("files", [])
        if items:
            return items[0]["id"]

        # Create new folder
        folder_metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}

        if parent_id:
            folder_metadata["parents"] = [parent_id]

        folder = self.service.files().create(body=folder_metadata, fields="id").execute()

        return folder.get("id")

    def download_file(self, file_id):
        """
        Download a file from Google Drive

        Args:
            file_id (str): Google Drive file ID

        Returns:
            BytesIO: File content as BytesIO object
        """
        request = self.service.files().get_media(fileId=file_id)
        file_content = BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        file_content.seek(0)
        return file_content

    def delete_file(self, file_id):
        """
        Delete a file from Google Drive

        Args:
            file_id (str): Google Drive file ID
        """
        self.service.files().delete(fileId=file_id).execute()
