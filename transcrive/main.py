#!/usr/bin/env python3
import argparse
import os
import pathlib

import cloudinary as cloudinary
import cloudinary.uploader

from transcrive import json_helper
from transcrive.PDFtoPNG import convert
from transcrive.transcribe_script import Transcrive


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backend for Transcrive."
    )

    parser.add_argument(
        "-p",
        "--path",
        type=str,
        metavar="FILE",
        help="Path to the presentation PDF file you wish to present."
    )
    return parser.parse_args()


def upload_image(path) -> str:
    result = cloudinary.uploader.upload(path)
    return result["secure_url"]


def main():
    args = parse_args()

    path_to_auth = str(pathlib.Path(__file__).parent.absolute() / "auth.json")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path_to_auth

    path_to_presentation = ""
    if args.path:
        path_to_presentation = args.path

    # convert pdf to images
    convert(path_to_presentation)

    pres_name = os.path.splitext(os.path.basename(path_to_presentation))[0]
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
            url = upload_image(os.path.join(output_dir, file))
            this_slide = {"url": url, "lines": []}
            slides[slide_index] = this_slide
            slide_index += 1
            os.remove(os.path.join(output_dir, file))

    # print(json_helper.dict_to_json(presentation_json))

    transcriber = Transcrive(pres_name, presentation_json)
    transcriber.run_transcribe()
