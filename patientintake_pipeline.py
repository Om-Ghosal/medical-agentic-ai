import threading
import boto3
import time
import random
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError

# Lock to ensure only one execution at a time
lock = threading.Lock()

class PatientAdmissionForm(BaseModel):
    image_path: str = Field(description="The path containing the image of the form the patient submitted")


def analyze_document_with_retry(file_path, max_retries=5):
    """Attempts to analyze the document with retries in case of throttling"""
    retries = 0
    while retries < max_retries:
        try:
            with lock:  # Lock ensures that only one function call runs at a time
                with open(file_path, 'rb') as document:
                    image_bytes = document.read()

                textract = boto3.client('textract')

                response = textract.analyze_document(
                    Document={'Bytes': image_bytes},
                    FeatureTypes=['FORMS']
                )

                return response

        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                retries += 1
                delay = min(2 ** retries + random.uniform(0, 1), 16)  # Exponential backoff
                print(f"Throttling detected, retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                print(f"Error analyzing document: {e}")
                raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    raise Exception("Max retries reached, could not process the document due to throttling.")


def get_kv_pairs(response):
    blocks = response['Blocks']
    key_map = {}
    value_map = {}
    block_map = {}

    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block.get('EntityTypes', []):
                key_map[block_id] = block
            elif 'VALUE' in block.get('EntityTypes', []):
                value_map[block_id] = block

    kvs = {}
    for key_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        value = get_text(value_block, block_map)
        kvs[key] = value

    return kvs


def find_value_block(key_block, value_map):
    for relationship in key_block.get('Relationships', []):
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                return value_map.get(value_id)
    return None


def get_text(block, block_map):
    text = ''
    if not block:
        return text
    for relationship in block.get('Relationships', []):
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                word = block_map[child_id]
                if word['BlockType'] == 'WORD':
                    text += word['Text'] + ' '
                elif word['BlockType'] == 'SELECTION_ELEMENT':
                    if word['SelectionStatus'] == 'SELECTED':
                        text += 'X '
    return text.strip()


@tool("extract_patient_data", args_schema=PatientAdmissionForm)
def patientintake_pipeline(image_path):
    """Pass the Form's image path to this function to get a dictionary of the form data"""
    response = analyze_document_with_retry(image_path)  # Using retry function
    key_value_pairs = get_kv_pairs(response)

    return key_value_pairs


