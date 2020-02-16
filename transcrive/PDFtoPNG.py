import os
import pathlib

import convertapi as convertapi


def main():
    filename = 'test.pdf'

    parent_dir = str(pathlib.Path(__file__).parent.absolute())

    convertapi.api_secret = 'HRfgvNWaFLiw4U2w'
    convertapi.convert('jpg', {
        'File': os.path.join(parent_dir, 'test.pdf')
    }, from_format='pdf').save_files(os.path.join(parent_dir, "output"))


if __name__ == "__main__":
    main()
