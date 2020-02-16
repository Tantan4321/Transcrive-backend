import os
import pathlib
import tempfile
from pdf2image import convert_from_path
def main():
    filename = 'test.pdf'

    with tempfile.TemporaryDirectory() as path:
        images_from_path = convert_from_path(filename, output_folder=path)

    base_filename = os.path.splitext(os.path.basename(filename))[0] + '.png'

    parent_dir = str(pathlib.Path(__file__).parent.absolute())
    save_dir = 'output'

    for page in images_from_path:
        page.save(os.path.join(parent_dir, save_dir, base_filename), 'PNG')

if __name__ == "__main__":
    main()
