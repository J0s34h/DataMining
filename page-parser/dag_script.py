import datetime
import re
import emoji
import nltk
import psycopg2
import vk_api
from airflow.models import DAG
from airflow.operators.python import PythonOperator
from nltk.corpus import stopwords

args = {
    'owner': 'airflow',
    'start_date': datetime.datetime(2021, 3, 18),
    'retries': 1,
    'schedule_interval': '@daily',
    'retry_delay': datetime.timedelta(days=1),
    'depends_on_past': False,
}

urlFilter = r'\S((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z0-9\&\.\/\?\:@\-_=#])*\S'
metaCharFilter = r'[!@#»«$%^&*(;":,./<>?`~=_+\]\}\{\[\|\-)r]'
clubFilter = r'club[0-9]+[A-Z]*\S*'

post_cache = {}

try:
    conn = psycopg2.connect(dbname='', user='postgres',
                            password='Erika1944', host='database-1.cfrqfkiv7xzd.us-east-1.rds.amazonaws.com')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS COUNTER")

    sql = '''CREATE TABLE COUNTER(
       WORD VARCHAR NOT NULL UNIQUE,
       ENCOUNTERS INT NOT NULL
    )'''
    cursor.execute(sql)
except psycopg2.errors as e:
    print('Error %s' % e)


def captcha_handler(captcha):
    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()
    return captcha.try_again(key)


def char_checker(char) -> bool:
    if char in emoji.UNICODE_EMOJI_ENGLISH:
        return False
    else:
        return True


def split(word):
    return [char for char in word]


def word_handler(word):
    word = word.replace("\n", "")
    if not re.search(urlFilter, repr(word)):
        word = re.sub(clubFilter, "", word)
        word = re.sub(metaCharFilter, "", word)
        if word != "":
            raw_word = repr(word.lower())
            if post_cache.__contains__(raw_word):
                post_cache[raw_word] += 1
            else:
                post_cache[raw_word] = 0


def post_handler(post):
    for key in post:
        cursor.execute('select * from COUNTER where word=%s', (key,))
        if cursor.rowcount != 0:
            row = cursor.fetchone()
            cursor.execute('UPDATE COUNTER SET ENCOUNTERS = %s  WHERE word=%s', (row[1] + 1, key))
        else:
            cursor.execute('INSERT INTO COUNTER (WORD, ENCOUNTERS) VALUES (%s, %s)', (key, 0))


def main(login=None, password=None):
    vk_session = vk_api.VkApi(
        login, password,
        captcha_handler=captcha_handler
    )

    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return

    tools = vk_api.VkTools(vk_session)
    wall = tools.get_all_slow_iter('wall.get', 1, {'domain': "itis_kfu"})

    print("Starting processing posts")

    count = 0

    for post in wall.__iter__():
        text = post['text']
        word = ""
        for char in split(text):
            if char == " ":
                word_handler(word)
                word = ""
            elif char_checker(char):
                word += char
        post_handler(post_cache)
        post_cache.clear()
        conn.commit()
        print("Post number " + str(count) + " is loaded")
        count += 1

    print("Total " + str(count) + " posts processed")

    conn.close()


def starter():
    main(login="LOGIN", password="PASSWORD")


with DAG(dag_id='dag_script', default_args=args, schedule_interval=datetime.timedelta(days=1)) as dag:
    task = PythonOperator(
        task_id='dag_script_task',
        python_callable=starter,
        dag=dag
    )
