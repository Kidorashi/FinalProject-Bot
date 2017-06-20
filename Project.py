import telebot
import conf
import flask
import re
from random import uniform
from collections import defaultdict

WEBHOOK_URL_BASE = "https://{}:{}".format(conf.WEBHOOK_HOST, conf.WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)

bot = telebot.TeleBot(conf.TOKEN, threaded=False)
bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

app = flask.Flask(__name__)

r_alphabet = re.compile(u'[а-яА-Я0-9-]+|[.,:;?!]+')

def gen_lines(corpus):
    data = open(corpus, 'r', encoding = 'utf-8')
    for line in data:
        yield line.lower()
    data.close()

def gen_tokens(lines):
    for line in lines:
        for token in r_alphabet.findall(line):
            yield token

def gen_trigrams(tokens):
    t0, t1 = '$', '$'
    for t2 in tokens:
        yield t0, t1, t2
        if t2 in '.!?':
            yield t1, t2, '$'
            yield t2, '$','$'
            t0, t1 = '$', '$'
        else:
            t0, t1 = t1, t2

def train(corpus):
    lines = gen_lines(corpus)
    tokens = gen_tokens(lines)
    trigrams = gen_trigrams(tokens)

    bi, tri = defaultdict(lambda: 0.0), defaultdict(lambda: 0.0)

    for t0, t1, t2 in trigrams:
        bi[t0, t1] += 1
        tri[t0, t1, t2] += 1

    model = {}
    for (t0, t1, t2), freq in tri.items():
        if (t0, t1) in model:
            model[t0, t1].append((t2, freq/bi[t0, t1]))
        else:
            model[t0, t1] = [(t2, freq/bi[t0, t1])]
    return model

def unirand(seq):
    sum_, freq_ = 0, 0
    for item, freq in seq:
        sum_ += freq
    rnd = uniform(0, sum_)
    for token, freq in seq:
        freq_ += freq
        if rnd < freq_:
            return token

def generate_sentence(model,p):
    phrase = p
    t0, t1 = '$', p
    while 1:
        t0, t1 = t1, unirand(model[t0, t1])
        if t1 == '$': break
        if t1 in ('.!?,;:') or t0 == '$':
            phrase += t1
        else:
            phrase += ' ' + t1
    return phrase.capitalize()

model = train('/home/kidorashi/mysite/shakespeare.txt')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Приветствую тебя, путник. Я - маленький бот, который проведёт тебя в мир английского поэта и драматурга Уильяма Шекспира. Напиши мне скорее чего-нибудь. В случае проблемы кричи /help. Или пиши вот этому человечку - @Kidorashi - он что-нибудь придумает.\n\nP.S. Если хочешь литератуно просветиться, тыкай сюда - /info. ")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Пользоваться мной очень легко. Просто пиши мне по-русски. Что-нибудь. Только учитывай, что Шекспир жил не век и не два назад, и язык его произведений отличается от современного русского.")

@bot.message_handler(commands=['info'])
def send_texts(message):
    bot.send_message(message.chat.id,"При создании этого бота участвовали такие прекрасные произведения как:\n1. Антоний и Клеопатра\n2. Буря\n3. Гамлет\n4. Двенадцатая ночь\n5. Комедия ошибок\n6. Кориолан\n7. Король Лир\n8. Макбет\n9. Много шума из ничего\n10. Отелло\n11. Ромео и Джульетта\n12. Сон в летнюю ночь\n\nЕсли какие-то из этих произведений тебе не знакомы, то почему ты всё ещё сидишь в Телеграме, а не восполняешь пробел в знаниях? Шекспир стоит того, чтобы его почитать.")

@bot.message_handler(content_types=['text'])
def reply(message):
    phrase = message.text.lower()
    phrase = phrase.split()
    phrase = phrase[-1].rstrip('.,:;?!')
    try:
        reply = generate_sentence(model, phrase)
    except:
        reply = 'Что-то пошло не так. Причин может быть несколько.' + '\n' + '1. В моей коллекции не нашлось подходящих слов для ответа.' + '\n' + '2. Ты написал не по-русски. Шекспир, конечно, был англичанином. Но я то нет.' + '\n' + '3. Мой создатель где-то напортачил. Но это вряд ли, он программист, лингвист и вообще умничка.' + '\n' + 'Попробуй написать ещё.'
    bot.send_message(message.chat.id, reply)

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'ok'

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
