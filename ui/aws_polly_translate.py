import boto3

import json
import os
import uuid

from transcribe_setup import *

# REGION = "us-east-1"
# LANGUAGE_CODE = "en-US"
# SAMPLE_RATE = 16000  # Adjust based on your audio file
# CHUNK_SIZE = 1024 * 2  
# transcribe_client = boto3.client("transcribe", region_name=REGION)

session = boto3.Session()
credentials = session.get_credentials()

def aws_polly_voice(text,language_id,voice_id):
    polly = boto3.client('polly', region_name='ap-south-1')
    response = polly.synthesize_speech(
        Text=text,
        OutputFormat="mp3",
        VoiceId=voice_id,
        Engine="neural" , # Specify the neural engine
        LanguageCode=language_id
    )
    audio_stream = response['AudioStream'].read()
    return audio_stream

def aws_translation(text,target_language='en',source_language='en'):
    translate = boto3.client('translate')
    response = translate.translate_text(
    Text=text,
    SourceLanguageCode=source_language,
    TargetLanguageCode=target_language
)
    return response['TranslatedText']


def polly_pipieline(text,to_language,lang_id,voice_id):

    translated_text = aws_translation(text,to_language)

    return aws_polly_voice(translated_text,'cmn-CN' if lang_id== 'zh-CN' else lang_id,voice_id)




def get_job(job_name, transcribe_client):
    """
    Gets details about a transcription job.

    :param job_name: The name of the job to retrieve.
    :param transcribe_client: The Boto3 Transcribe client.
    :return: The retrieved transcription job.
    """
    
    response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
    job = response["TranscriptionJob"]
       

    return job

def delete_file(file_path):
    """
    Deletes a local file if it exists.
    
    :param file_path: The full path of the file to delete.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        else:
            print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error deleting file: {e}")


def aws_transcribe_stream(language_code):
    mp3_to_pcm('temp.mp3','Recording.pcm')
    final_text = asyncio.run(basic_transcribe(language_code=language_code))
    delete_file('temp.mp3')
    delete_file('Recording.pcm')

    return final_text
