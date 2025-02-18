import configparser
import os 
# chưa dùng đến 
parser = configparser.ConfigParser()
parser.read(os.path.join(os.path.dirname(__file__),'../config/config.conf'))

#AWS

INPUT_PATH = parser.get('file_paths', 'input_path')
OUTPUT_PATH = parser.get('file_paths', 'output_path')

