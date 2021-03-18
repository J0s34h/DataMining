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
    'retry_delay': datetime.timedelta(minutes=20),
    'depends_on_past': False,
}


def logic_function():
    # Local Variables
    TOKEN = "fa267307fa267307fa2673074ffa50e889ffa26fa2673079a11a84f2cb2d50acb0df095"
    url_filter = r'\S((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z0-9\&\.\/\?\:@\-_=#])*\S'
    meta_char_filter = r'[!@#»«$%^&*(;":,./<>?`~=_+\]\}\{\[\|\-)r]'
    club_filter = r'club[0-9]+[A-Z]*\S*'
    post_cache = {}

    conn = psycopg2

    def char_checker(char) -> bool:
        if char in emoji.UNICODE_EMOJI_ENGLISH:
            return False
        else:
            return True

    def split(word):
        return [char for char in word]

    def word_handler(word):
        word = word.replace("\n", "")
        if not (re.search(url_filter, repr(word))):
            word = re.sub(club_filter, "", word)
            word = re.sub(meta_char_filter, "", word)
            if word != "":
                raw_word = word.lower()
                if post_cache.__contains__(raw_word):
                    post_cache[raw_word] += 1
                else:
                    post_cache[raw_word] = 0

    def post_handler(post):
        for key in post:
            cursor.execute('SELECT * FROM COUNTER WHERE word=%s', (key,))
        if cursor.rowcount != 0:
            row = cursor.fetchone()
            cursor.execute('UPDATE COUNTER SET ENCOUNTERS = %s  WHERE word=%s', (row[1] + 1, key))
        else:
            cursor.execute('INSERT INTO COUNTER (WORD, ENCOUNTERS) VALUES (%s, %s)', (key, 1))

    try:
        print("Connecting to database")
        conn = psycopg2.connect(dbname='', user='postgres',
                                password='Erika1944', host='database-1.cfrqfkiv7xzd.us-east-1.rds.amazonaws.com')
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS COUNTER')
        sql = '''CREATE TABLE COUNTER(
                    WORD VARCHAR NOT NULL UNIQUE,
                    ENCOUNTERS INT NOT NULL
                    )'''
        cursor.execute(sql)
    except psycopg2.errors as e:
        print('Error %s' % e)
    print("Successful connection to database")

    vk_session = vk_api.VkApi(
        token=TOKEN
    )

    print("Connecting to VK")

    try:
        vk_session.get_api()
    except vk_api.AuthError as error_msg:
        print(error_msg)

    tools = vk_api.VkTools(vk_session)
    wall = tools.get_all_iter('wall.get', 1, {'domain': "itis_kfu"})

    print("Starting processing posts")

    count = 0

    for post in wall.__iter__():
        text = post['text']
        word = ""
        print("Post number " + str(count) + " is loaded")
        for char in split(text):
            if char == " ":
                word_handler(word)
                word = ""
            elif char_checker(char):
                word += char
        post_handler(post_cache)
        post_cache.clear()
        conn.commit()
        count += 1
    print("Total " + str(count) + " posts processed")
    conn.close()


with DAG(dag_id='dag_script', default_args=args, schedule_interval=None) as dag:
    parse_vk_itis = PythonOperator(
        task_id='dag_script_task_id',
        python_callable=logic_function,
        dag=dag
    )
