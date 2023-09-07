import configparser
import pathlib


def read_conf(path):
    conf_path = pathlib.Path(__file__).parent / path
    conf = configparser.ConfigParser()
    conf.read(conf_path)

    return conf


conf = read_conf("config.ini")

ACCESS_CODE = conf['ACCESS']['code']