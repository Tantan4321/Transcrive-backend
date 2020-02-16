import os
import pathlib

import convertapi as convertapi


def convert(filename):

    parent_dir = str(pathlib.Path(__file__).parent.absolute())

    convertapi.api_secret = 'HRfgvNWaFLiw4U2w'
    convertapi.convert('jpg', {
        'File': os.path.join(parent_dir, filename)
    }, from_format='pdf').save_files(os.path.join(parent_dir, "output"))


