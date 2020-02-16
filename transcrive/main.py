#!/usr/bin/env python3
import os
import pathlib

import mysql.connector

from transcrive.PDFtoPNG import convert
from transcrive.transcribe_script import Transcrive



def main():
    path_to_auth = str(pathlib.Path(__file__).parent.absolute() / "auth.json")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path_to_auth

    # convert pdf to images
    convert('test.pdf')



    transcriber = Transcrive()
    transcriber.run_transcribe()


def sql():
    # Open database connection
    cnx = mysql.connector.connect(user='doadmin', password='g2o24tvb377oiu3z',
                                  host='transcrive-db-do-user-7124898-0.db.ondigitalocean.com',
                                  database='defaultdb')
    print("bruh")

    # prepare a cursor object using cursor() method
    cursor = cnx.cursor()

    # execute SQL query using execute() method.
    cursor.execute("SELECT VERSION()")

    # Fetch a single row using fetchone() method.
    data = cursor.fetchone()
    print("Database version : %s " % data)

    # disconnect from server
    cnx.close()
