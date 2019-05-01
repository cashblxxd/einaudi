from google.cloud import texttospeech


def synthesis(text, lang='en', gender='m', filename='output.mp3'):
    gender = {
        'm': texttospeech.enums.SsmlVoiceGender.MALE,
        'f': texttospeech.enums.SsmlVoiceGender.FEMALE,
        'n': texttospeech.enums.SsmlVoiceGender.NEUTRAL,
    }[gender]
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.types.SynthesisInput(text=text)
        voice = texttospeech.types.VoiceSelectionParams(
            language_code=lang,
            ssml_gender=gender)
        audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.MP3)
        response = client.synthesize_speech(synthesis_input, voice, audio_config)
        with open(filename, 'wb') as out:
            out.write(response.audio_content)
        return 0
    except Exception as e:
        print(e)
        return text

