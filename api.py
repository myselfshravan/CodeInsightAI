import sys
import time

import requests

try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import firebase_admin
import pandas as pd
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter  # noqa
# import chromadb


class API:
    def __init__(self, secrets):
        self.firestore = self.get_firestore(secrets)
        # self.chromadb = self.get_chromadb()
        self.users = self.firestore.collection("users")
        self.user = None

    @staticmethod
    def get_firestore(secrets):
        try:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": secrets["FIREBASE_PROJECT_ID"],
                "private_key_id": secrets["FIREBASE_PRIVATE_KEY_ID"],
                "private_key": secrets["FIREBASE_PRIVATE_KEY"],
                "client_email": secrets["FIREBASE_CLIENT_EMAIL"],
                "client_id": secrets["FIREBASE_CLIENT_ID"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": secrets["FIREBASE_CLIENT_X509_CERT_URL"],
                "universe_domain": "googleapis.com",
            })
            firebase_admin.initialize_app(cred)
        except ValueError:
            pass
        return firestore.client()

    # @staticmethod
    # def get_chromadb():
    #     return chromadb.HttpClient(host='13.201.63.243', port=8000).get_collection("collection")

    def auth(self, username, password):
        user = self.users.where(filter=FieldFilter(u'username', u'==', username)).where(
            filter=FieldFilter(u'password', u'==', password)).get()
        if user and user[0].exists: self.user = user[0]
        return self.user


class RespondAPI(API):
    def __init__(self, secrets, respond_col: str = "respond"):
        super().__init__(secrets)
        self.responds = self.firestore.collection(respond_col)

    def log(
            self,
            code_input: str,
            respond_text: str,
            title: str,
    ) -> str:
        log = self.responds.document()
        log.set({
            "code_input": code_input,
            "respond_text": respond_text,
            "title": title,
            "timestamp": int(time.time()),
        })
        return log.id

    def get_responds(self):
        return self.responds.stream()

    def get_respond(self, grv_id):
        return self.responds.document(grv_id).get()


__all__ = [
    "RespondAPI",
]
