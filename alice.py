from flask import Flask, request
import logging
from translations import get_translation, langlist
from database import group_id, peer_id, token
import vk_api
import requests
import json
from texttospeech import synthesis
import os
from langdetect import detect

app = Flask(__name__)
flags = {}

logging.basicConfig(level=logging.INFO, filename='example.log')


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    vk_session = vk_api.VkApi(token=token())
    uid = req['session']['user_id']
    if req['session']['new']:
        flags[uid] = {
            'translate': False,
            'voices': False,
            'lang_translate': 'en'
        }
        res['response']['text'] = 'Привет! Отправь боту голосовое или введи одну из команд:\n\n' \
                  'автоперевод включить/выключить - присылать ответ голосовым сообщением\n' \
                  'перевод вкл/выкл - переводить ли на другой язык (по умолчанию - английский)\n' \
                  'перевод английский - переводить на английский\n\n' \
                  'Tips and tricks:\n\n' \
                  '+ Можно сокращать некоторые запросы (кроме названий языков): авто вкл (автоперевод)\n' \
                  '+ Хотя в примере показан лишь английский, бот позволяет распознавать, переводить и' \
                  ' озвучивать 103 языка.'
        return

    text = req['request']['original_utterance']
    message = text
    settings = False
    if 'нач' in text or 'start' in text:
        settings = True
    elif 'авто' in text and (' на ' in text or'вкл' in text or 'выкл' in text):
        if 'вкл' in text:
            flags[uid]['voices'] = True
            settings = True
        elif 'выкл' in text:
            flags[uid]['voices'] = False
            settings = True
    elif 'перевод' in text and (' на ' in text or 'вкл' in text or 'выкл' in text):
        if ' на ' in text:
            for i in text.split():
                d = get_translation(i, 'en')
                if d in langlist:
                    flags[uid]['lang_translate'] = langlist[d]
                    settings = True
        if 'вкл' in text:
            flags[uid]['translate'] = True
            settings = True
        elif 'выкл' in text:
            flags[uid]['translate'] = False
            settings = True
    else:
        message = req['request']['original_utterance']
        if flags[uid]['translate']:
            message = get_translation(message, flags[uid]['lang_translate'])
            logging.info(message)
        if flags[uid]['voices']:
            logging.info('voices!')
            audio_url = vk_session.method('docs.getMessagesUploadServer',
                                          {'type': 'audio_message',
                                           'peer_id': peer_id(),
                                           'group_id': group_id()})['upload_url']
            logging.info(audio_url)
            meow = synthesis(message, detect(message))
            if meow != 0:
                res['response']['text'] = 'Извините, но сейчас доступны следующие языки:\n' \
                                          'Английский, голландский, датский, испанский, итальянский, корейский, немецкий, ' \
                                          'польский, португальский, русский, словацкий, турецкий, украинский, французский, ' \
                                          'шведский, японский.'

            else:
                files = [('file', ('output.mp3', open('output.mp3', 'rb')))]
                url2 = requests.post(audio_url, files=files).text
                os.remove('output.mp3')
                logging.info('meow!')
                RESPONSE = json.loads(url2)['file']
                RESPONSE_2 = vk_session.method('docs.save', {'file': RESPONSE})
                logging.info('RESPONSE_2: %r', RESPONSE_2)
                _id = RESPONSE_2['audio_message']['id']
                owner_id = RESPONSE_2['audio_message']['owner_id']
                document = 'doc%s_%s' % (str(owner_id), str(_id))
            return
        else:
            res['response']['text'] = message
            logging.info('message: %s' % message)
            return

    if settings:
        if flags[uid]['translate']:
            one = 'включен'
        else:
            one = 'выключен'
        if flags[uid]['voices']:
            two = 'включен'
        else:
            two = 'выключен'
        message += '\n\nПеревод: %s\nАвтоперевод: %s\nЯзык перевода: %s' % (
            one, two, flags[uid]['lang_translate'])
    res['response']['text'] = message.strip()
    logging.info('message: %s' % res['response']['text'])
    return


if __name__ == '__main__':
    app.run()
    os.system('export GOOGLE_APPLICATION_CREDENTIALS="/home/alicebot/mysite/auth.json"')
    logging.info('Did i set creds? Yes, of course!')
    with open('prefs.jpg', 'r') as f:
        m = f.read()
        if len(m) > 1:
            k = json.loads(m)
            for i in k:
                flags[i] = k[i]
