
from io import BufferedReader
from typing import override
from PyPDF2 import PdfReader
from html.parser import HTMLParser

from data import DataType

class CustomHTMLParser(HTMLParser):
    
    @override
    def handle_data(self, data: str):
        print(data)

def parse(stream: BufferedReader, data_type: DataType):

    if data_type == DataType.UNSUPPORTED:
        print("Data type is not supported")

    if data_type == DataType.PDF:
        reader = PdfReader(stream = stream)

        for page in reader.pages:
            print(page.extract_text())

    elif data_type == DataType.HTML:
        html_parser = CustomHTMLParser()

        for data in stream:
            html_parser.feed(data.decode())
