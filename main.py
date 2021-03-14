import sys
import re
import vk_api
import emoji

# Local Variables
urlFilter = r'\S((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z0-9\&\.\/\?\:@\-_=#])*\S'
metaCharFilter = r'[!@#$%^&*(;":,./<>?`~=_+\]\}\{\[\|\-)r]'
clubFilter = r'club[0-9]+[A-Z]*\S*'


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
            print(repr(word)     + "\n")


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

    for post in wall.__iter__():
        text = post['text']
        word = ""
        for char in split(text):
            if char == " ":
                word_handler(word)
                word = ""
            elif char_checker(char):
                word += char


if __name__ == '__main__':
    main(login=sys.argv[1], password=sys.argv[2])
