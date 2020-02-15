from pdf2image import convert_from_path

def main():
    pdf_path = "C:\Git Stuff\Transcrive-backend\Input\Is this Reality.pdf"


    convert_from_path(pdf_path, output_folder="C:\Git Stuff\Transcrive-backend\Output")


if __name__ == "__main__":
    main()
