from ruamel import yaml
import sys
import pymysql
import os


def load_yaml(yaml_file):
    """

    :param yaml_file: yaml文件地址
    :return: 字典化的yaml
    """

    file = open(yaml_file, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()

    # 将字符串转化为字典或列表
    data = yaml.load(file_data, Loader=yaml.RoundTripLoader)

    return data


def dump_yaml(yaml_file, data):
    """
    Dump info of data into a yaml file
    :param yaml_file:
    :param data:
    :return:
    """
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f, Dumper=yaml.RoundTripDumper)


def add_yaml(yaml_file, data):
    """
    add info of data into a yaml file
    :param yaml_file:
    :param data:
    :return:
    """
    with open(yaml_file, 'a') as f:
        yaml.dump(data, f, Dumper=yaml.RoundTripDumper)


def progress_bar(transferred, toBeTransferred, suffix=''):
    """
    show the progress of a process
    :param transferred:
    :param toBeTransferred:
    :param suffix:
    :return:
    """
    # print "Transferred: {0}\tOut of: {1}".format(transferred, toBeTransferred)
    bar_len = 60
    filled_len = int(round(bar_len * transferred/float(toBeTransferred)))
    percents = round(100.0 * transferred/float(toBeTransferred), 1)
    bar = '*' * filled_len + '-' * (bar_len - filled_len)
    # with open('./test.txt','w') as file:
    #     file.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.write('[%s] %s%s  finished: %s, total: %s%s\r' % (bar, percents, '%', transferred,toBeTransferred, suffix))
    sys.stdout.flush()


def easy_bar(transferred, toBeTransferred):
    bar_len = 60
    filled_len = int(round(bar_len * transferred / float(toBeTransferred)))
    percents = round(100.0 * transferred / float(toBeTransferred), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    print('[{}] {}%  finished:{}, total:{}'.format(bar, percents, transferred, toBeTransferred))


if __name__ == '__main__':
    # load_yaml('./config.yaml')
    cf_dict = load_yaml('./config.yaml')




