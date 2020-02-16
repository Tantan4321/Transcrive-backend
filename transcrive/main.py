#!/usr/bin/env python3
import os
import pathlib
import threading

import mysql.connector

from transcrive.transcribe_script import Transcrive

from pynput.keyboard import Key, Listener

def on_press(key):
    print('{0} pressed'.format(
        key))
    if key == Key.esc:
        # Stop listener
        return False

def key_logger():
    # Collect events until released
    with Listener(
            on_press=on_press) as listener:
        listener.join()

def main():
    path_to_auth = str(pathlib.Path(__file__).parent.absolute() / "auth.json")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path_to_auth



    transcriber = Transcrive()
    threading.Thread(name='keypress', target=key_logger).start()
    threading.Thread(name='transcriber', target=transcriber.run_transcribe()).start()









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
