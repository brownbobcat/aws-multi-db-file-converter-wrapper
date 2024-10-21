import csv
import json
import xml.etree.ElementTree as ET
import argparse
import os
from typing import List, Dict, Callable

def txt_to_csv(input_file: str, output_file: str):
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        for line in infile:
            writer.writerow(line.strip().split())

def json_to_csv(input_file: str, output_file: str):
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        data = json.load(infile)
        writer = csv.writer(outfile)
        
        if isinstance(data, list) and data and isinstance(data[0], dict):
            headers = list(data[0].keys())
            writer.writerow(headers)
            for row in data:
                writer.writerow([row.get(header, '') for header in headers])
        elif isinstance(data, dict):
            for key, value in data.items():
                writer.writerow([key, value])
        else:
            raise ValueError("Unsupported JSON structure")

def xml_to_csv(input_file: str, output_file: str):
    tree = ET.parse(input_file)
    root = tree.getroot()

    with open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        headers = set()
        rows = []

        for child in root:
            row = {}
            for elem in child:
                headers.add(elem.tag)
                row[elem.tag] = elem.text
            rows.append(row)

        headers = sorted(headers)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row.get(header, '') for header in headers])

def process_files(input_files: List[str], output_dir: str, convert_func: Callable):
    for input_file in input_files:
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{file_name}.csv")
        convert_func(input_file, output_file)
        print(f"Converted {input_file} to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Convert .txt, .json, or .xml files to .csv")
    parser.add_argument("input", nargs='+', help="Input file(s)")
    parser.add_argument("-o", "--output", default=".", help="Output directory")
    parser.add_argument("-t", "--type", choices=['txt', 'json', 'xml'], required=True, help="Input file type")
    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    convert_func = {
        'txt': txt_to_csv,
        'json': json_to_csv,
        'xml': xml_to_csv
    }[args.type]

    process_files(args.input, args.output, convert_func)

if __name__ == "__main__":
    main()