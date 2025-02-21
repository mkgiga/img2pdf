# img2pdf.py - A program that converts images with text to PDFs with text content.

import tkinter
import argparse
import pathlib
import easyocr

parser: argparse.ArgumentParser = None

args = {
    # Default parameters
    "input": pathlib.Path("./input"),
    "output": pathlib.Path("./output"),
}

"""
# Arguments

    -o, --output: The output directory for the PDFs.
    -i, --image: The path to either an image or a directory containing images to convert to PDFs.
    -h, --help: Show the help message.
"""


def main():
    parse_args()
    test()


def parse_args():
    global parser
    
    parser = argparse.ArgumentParser(description="Convert images with text to PDFs with text content.")
    
    parser.add_argument("-o", "--output", type=pathlib.Path, help="The output directory for the PDFs.", default=args["output"])
    parser.add_argument("-i", "--image", type=pathlib.Path, help="The path to either an image or a directory containing images to convert to PDFs.", default=args["input"])
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit.")
    
    args = parser.parse_args()
    
    input_path = args.input
    
    if not input_path.exists():
        print(f"Error: The input path '{input_path}' does not exist.")
        exit(1)
    
    return args

def test():
    pass
if __name__ == "__main__":
    main()