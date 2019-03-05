from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from google.cloud import storage
from urllib.request import urlretrieve
from os import system
from pprint import pprint


def recognize(blob_name, filename, audio_url, lang='ru'):
    bucket_name = 'bucket-111493473'
    urlretrieve(filename=filename, url=audio_url)
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(filename)
    system('rm -f ' + filename)
    client = speech.SpeechClient()
    audio = types.RecognitionAudio(uri='gs://bucket-111493473/' + blob_name)
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.OGG_OPUS,
        sample_rate_hertz=16000,
        language_code=lang)
    operation = client.long_running_recognize(config, audio)
    print('Waiting for operation to complete...')
    response = operation.result()
    pprint(response)
    for result in response.results:
        return result.alternatives[0].transcript

