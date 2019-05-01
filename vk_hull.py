def starter():
    from database import token
    import json
    from multiprocessing import Process, Queue, Manager
    token = token()
    manager = Manager()
    flags = manager.dict()
    with open('prefs.jpg', 'r') as f:
        m = f.read()
        if len(m) > 1:
            k = json.loads(m)
            for i in k:
                flags[i] = k[i]
    message_queue = Queue()
    input_queue = Queue()
    main_proc = Process(target=main_hull, args=(flags, input_queue, message_queue, token,))
    handlers = []
    for i in range(5):
        handlers.append(Process(target=handler_hull, args=(input_queue, message_queue, token, flags,)))
    sender_proc = Process(target=sender, args=(message_queue, token,))
    main_proc.start()
    for i in handlers:
        i.start()
    sender_proc.start()
    main_proc.join()
    for i in handlers:
        i.join()
    sender_proc.join()


def main_hull(flags, input_queue, message_queue, token):
    from vk_api.longpoll import VkLongPoll, VkEventType
    from database import group_id
    import vk_api
    import json
    from translations import get_translation, langlist

    def main(flags, input_queue, message_queue):
        print('Initialized')
        for event in longpoll.listen():
            try:
                print(event.from_chat)
            except Exception as e:
                print(e)
            if event.type == VkEventType.MESSAGE_NEW and event.to_me or event.from_chat:
                try:
                    print(12, 67485637843)
                    f = True
                    vk.messages.markAsRead(peer_id=event.user_id, group_id=group_id())
                    uid = str(event.user_id)
                    settings = False
                    if uid not in flags:
                        flags[uid] = {
                            'translate': False,
                            'voices': False,
                            'lang_sent': 'ru',
                            'lang_translate': 'en'
                        }
                    try:
                        if event.text:
                            try:
                                if event.message_data['fwd_messages']:
                                    raise ZeroDivisionError
                            except ZeroDivisionError:
                                raise KeyError
                            except Exception:
                                print(end='')
                            text = event.text.lower()
                            m = flags[uid].copy()
                            if 'нач' in text or 'прив' in text:
                                message = 'Привет! Отправь боту голосовое или введи одну из команд:\n\n' \
                                          'автоперевод включить/выключить - присылать ответ голосовым сообщением\n' \
                                          'перевод вкл/выкл - переводить ли на другой язык (по умолчанию - английский)\n' \
                                          'перевод английский - переводить на английский\n\n' \
                                          'Tips and tricks:\n\n' \
                                          '+ Можно сокращать некоторые запросы (кроме названий языков): авто вкл (автоперевод)\n' \
                                          '+ Хотя в примере показан лишь английский, бот позволяет распознавать, переводить и' \
                                          ' озвучивать 103 языка.'
                                message_queue.put({
                                    'user_id': event.user_id,
                                    'message': message
                                })
                                settings = True
                            elif 'авто' in text:
                                if 'вкл' in text:
                                    m['voices'] = True
                                elif 'выкл' in text:
                                    m['voices'] = False
                                settings = True
                            elif 'перевод' in text:
                                if ' с ' in text and ' на ' in text:
                                    txt = text.split()
                                    fr0m, to = txt[txt.index('с') + 1], txt[txt.index('на') + 1]
                                    if fr0m != to:
                                        d = get_translation(to, 'en')
                                        if d in langlist:
                                            m['lang_translate'] = langlist[d]
                                        d = get_translation(fr0m, 'en')
                                        if d in langlist:
                                            m['lang_sent'] = langlist[d]
                                elif ' на ' in text:
                                    h = m['lang_translate']
                                    for i in text.split():
                                        d = get_translation(i, 'en')
                                        if d in langlist:
                                            m['lang_translate'] = langlist[d]
                                    if flags[uid]['lang_translate'] == flags[uid]['lang_sent']:
                                        m['lang_sent'] = h
                                elif ' с ' in text:
                                    h = m['lang_sent']
                                    for i in text.split():
                                        d = get_translation(i, 'en')
                                        if d in langlist:
                                            m['lang_sent'] = langlist[d]
                                    if flags[uid]['lang_translate'] == flags[uid]['lang_sent']:
                                        m['lang_translate'] = h
                                if 'вкл' in text:
                                    m['translate'] = True
                                elif 'выкл' in text:
                                    m['translate'] = False
                                settings = True
                            if settings:
                                if m['translate']:
                                    one = 'включен'
                                else:
                                    one = 'выключен'
                                if m['voices']:
                                    two = 'включен'
                                else:
                                    two = 'выключен'
                                message = 'Перевод: %s\nАвтоперевод: %s\nОсновной язык: %s\nЯзык перевода: %s' % (
                                one, two, m['lang_sent'], m['lang_translate'])
                                message_queue.put({
                                    'user_id': event.user_id,
                                    'message': message
                                })
                            flags[uid] = m
                            with open('prefs.jpg', 'w') as f:
                                json.dump(flags.copy(), f)
                            f = False
                    except Exception as e:
                        print(e)
                    if event.message_data is None:
                        continue
                    if f:
                        input_queue.put(event.message_data)
                except Exception as e:
                    print(e)

    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session, preload_messages=True)
    while True:
        try:
            main(flags, input_queue, message_queue)
        except Exception:
            vk_session = vk_api.VkApi(token=token)
            vk = vk_session.get_api()
            longpoll = VkLongPoll(vk_session, preload_messages=True)


def sender(message_queue, token):
    from random import randint
    import vk_api
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    while True:
        while message_queue.empty() is False:
            message_data = message_queue.get()
            try:
                if 'document' in message_data:
                    vk_session.method('messages.send', {'peer_id': message_data['user_id'], 'attachment': message_data['document'], 'random_id': randint(0, 10000)})
                else:
                    vk.messages.send(user_id=message_data['user_id'], random_id=randint(10, 20000), message=message_data['message'])
            except Exception as e:
                print(e)
                message_queue.put(message_data)
                vk_session = vk_api.VkApi(token=token)
                vk = vk_session.get_api()


def handler_hull(input_queue, message_queue, token, flags):
    from database import group_id
    from cloud import recognize
    import vk_api
    import requests
    import json
    from texttospeech import synthesis
    import os
    from langdetect import detect
    from pprint import pprint
    from translations import get_translation
    from random import randint

    def handler(message_data, message_queue, from_id):
        try:
            try:
                for i in message_data['fwd_messages']:
                        handler(i, message_queue, from_id)
            except KeyError:
                print('caught')
            attachment = message_data['attachments'][0]['audio_message']
            audio_url = attachment['link_ogg']
            print(str(randint(1, 100)), attachment["access_key"] + ".ogg", audio_url, flags[from_id]['lang_sent'])
            message = recognize(str(randint(1, 100)), attachment["access_key"] + ".ogg", audio_url, lang=flags[from_id]['lang_sent'])
            if flags[from_id]['translate']:
                message = get_translation(message, flags[from_id]['lang_translate'])
            if flags[from_id]['voices']:
                audio_url = vk_session.method('docs.getMessagesUploadServer',
                                              {'type': 'audio_message',
                                               'peer_id': from_id,
                                               'group_id': group_id()})['upload_url']
                print(audio_url)
                if message_data['from_id'] > 0:
                    s = vk.users.get(user_id=message_data['from_id'], fields="sex")[0]['sex']
                else:
                    s = randint(1, 2)
                print(s)
                s = {0: 'n', 1: 'f', 2: 'm'}[s]
                print(s)
                meow = synthesis(message, detect(message), s)
                if meow != 0:
                    message_queue.put({
                        'user_id': from_id,
                        'message': meow,
                    })
                    message_queue.put({
                        'user_id': from_id,
                        'message': 'Извините, но сейчас доступны следующие языки:\n'
                                   'Английский, голландский, датский, испанский, итальянский, корейский, немецкий,'
                                   'польский, португальский, русский, словацкий, турецкий, украинский, французский,'
                                   'шведский, японский'
                    })
                else:
                    files = [('file', ('output.mp3', open('output.mp3', 'rb')))]
                    url2 = requests.post(audio_url, files=files).text
                    os.remove('output.mp3')
                    RESPONSE = json.loads(url2)['file']
                    RESPONSE_2 = vk_session.method('docs.save', {'file': RESPONSE})
                    pprint(RESPONSE_2)
                    _id = RESPONSE_2['audio_message']['id']
                    owner_id = RESPONSE_2['audio_message']['owner_id']
                    document = 'doc%s_%s' % (str(owner_id), str(_id))
                    message_queue.put({
                        'user_id': from_id,
                        'document': document,
                    })
            else:
                message_queue.put({
                    'user_id': from_id,
                    'message': message,
                })
        except Exception as e:
            print(e)
            return

    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    while True:
        while input_queue.empty() is False:
            print('got....')
            h = input_queue.get()
            try:
                handler(h, message_queue, str(h['from_id']))
            except Exception as e:
                print(e)
                vk_session = vk_api.VkApi(token=token)
                vk = vk_session.get_api()


starter()
