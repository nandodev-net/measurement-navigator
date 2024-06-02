import datetime
import string
from random import random, seed


class VsfCodeGen:

    def __init__(
        self,
        user_seed=None,
        len_first_charset=9,
        len_second_charset=1,
        base=36,
        first_charset=string.digits,
        second_charset="ABCDEFGHIJKLMNPQRSTUVWXYZ",
    ):

        seed(a=user_seed)
        self.prime_num = 1679979167
        self.first_charset = first_charset
        self.second_charset = second_charset

        if len_first_charset < 1 or len_second_charset < 1:
            raise ValueError("len_fst or len_snd must be greater than 1")

        self.len_first_charset = len_first_charset
        self.len_second_charset = len_second_charset
        self.base = base

    def get_random_number(self):
        return int((random() * self.prime_num) % (36**6))

    def encode_section(self, v: int, base: int, charset: str, section_len: int):
        result = []
        c = 0
        while c < section_len and v >= 0:
            v, remainder = divmod(v, base)
            result.append(charset[remainder])
            c += 1

        result.reverse()
        return "".join(result)

    def gen_vsfc(self, prefix=""):
        num = self.get_random_number()
        now = datetime.datetime.now()
        date = now.strftime("%y%b").upper()

        first_section = self.encode_section(
            num, len(self.first_charset), self.first_charset, self.len_first_charset
        )
        second_section = self.encode_section(
            num, len(self.second_charset), self.second_charset, self.len_second_charset
        )

        if prefix:
            return "%s%s%s%s" % (prefix, date, first_section, second_section)
        else:
            return "%s-%s%s" % (date, first_section, second_section)
