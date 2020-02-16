#!/usr/bin/env python3
import os
import pathlib

import cloudinary as cloudinary
import cloudinary.uploader

from transcrive import json_helper
from transcrive.PDFtoPNG import convert
from transcrive.transcribe_script import Transcrive


def upload_image(path) -> str:
    result = cloudinary.uploader.upload(path)
    return result["secure_url"]


def main():
    path_to_auth = str(pathlib.Path(__file__).parent.absolute() / "auth.json")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path_to_auth

    # convert pdf to images
    convert('test.pdf')

    pres_name = "test"
    presentation_json = {"isActive": True, "slides": {}, "current_slide": 0}

    output_dir = os.path.join(str(pathlib.Path(__file__).parent.absolute()), "output")
    cloudinary.config(
        cloud_name="transcrive",
        api_key="212465483262898",
        api_secret="8hs2Ei7xBrbyx3SLJcdYpwz4Kmc"
    )

    slide_index = 0
    slides: dict = presentation_json["slides"]
    for file in os.listdir(output_dir):
        if file.endswith(".jpg"):
            url = "placeholder" # upload_image(os.path.join(output_dir, file))
            this_slide = {"url": url, "lines": []}
            slides[slide_index] = this_slide
            slide_index += 1

    print(json_helper.dict_to_json(presentation_json))

    transcriber = Transcrive(pres_name, presentation_json)
    transcriber.run_transcribe()
