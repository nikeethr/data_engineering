import os
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    key_file_location = os.path.join(_DIR, 'credentials', 'cred.json')
    scopes = [ 'https://www.googleapis.com/auth/drive' ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        key_file_location, scopes=scopes)

    # https://developers.google.com/drive/api/v3/quickstart/python
    service = build('drive', 'v3', credentials=credentials)

    # Call the Drive v3 API

    # 1) get the right folder
    # 2) download the file
    results = service.files().list(
        q="mimeType = 'application/vnd.google-apps.folder'",
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    print(results)
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

if __name__ == '__main__':
    main()
