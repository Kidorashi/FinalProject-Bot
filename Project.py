import telebot
import conf
import flask
import re
from random import uniform
from collections import defaultdict

bot = telebot.TeleBot(conf.TOKEN, threaded=False)
bot.remove_webhook()

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

model = train('C:\\Users\\1\\Desktop\\PythonProjects\\Project\\shakespeare.txt')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "А-йоу-йоу, супер-бот на связи.")

@bot.message_handler(content_types=['text'])
def reply(message):
    phrase = message.text.lower()
    phrase = phrase.split()
    try:
        reply = generate_sentence(model, phrase)
    except:
        reply = 'Что-то пошло не так.'
    bot.send_message(message.chat.id, reply)

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'ok'

if __name__ == '__main__':
    bot.polling(none_stop=True)