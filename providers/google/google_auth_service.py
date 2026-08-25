import os.path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class GoogleAuthService:
    def __init__(self, scopes: list[str]):
        self.credentials_path = "credentials/credentials.json"
        self.token_path = "credentials/token.json"
        self.scopes = scopes

    def get_credentials(self):
        credentials = None

        if os.path.exists(self.token_path):
            credentials = Credentials.from_authorized_user_file(
                filename=self.token_path,
                scopes=self.scopes
            )

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except RefreshError as e:
                    credentials = self._authorize()
            else:
                credentials = self._authorize()

            with open(self.token_path, "w") as token_file:
                token_file.write(credentials.to_json())

        return credentials

    def _authorize(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file=self.credentials_path,
            scopes=self.scopes
        )
        return flow.run_local_server(port=0)