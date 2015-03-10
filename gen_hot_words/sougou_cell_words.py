__author__ = 'wanghuafeng'
# -*- coding: utf-8 -*-
import requests
import time
import struct
import codecs
import sys
import os

PATH = os.path.dirname(os.path.abspath(__file__))
DOC_95K_PATH = os.path.dirname(os.path.dirname(os.path.dirname(PATH)))
scel_filename = os.path.join(PATH, 'hot_word.scel')

def read_utf16_str (f, offset=-1, len=2):
    if offset >= 0:
        f.seek(offset)
    str = f.read(len)
    return str.decode('UTF-16LE')

def read_uint16 (f):
    return struct.unpack ('<H', f.read(2))[0]

def get_word_from_sogou_cell_dict (fname):
    f = open (fname, 'rb')
    file_size = os.path.getsize (fname)

    hz_offset = 0
    mask = struct.unpack ('B', f.read(128)[4])[0]
    if mask == 0x44:
        hz_offset = 0x2628
    elif mask == 0x45:
        hz_offset = 0x26c4
    else:
        sys.exit(1)

    title   = read_utf16_str (f, 0x130, 0x338  - 0x130)
    type    = read_utf16_str (f, 0x338, 0x540  - 0x338)
    desc    = read_utf16_str (f, 0x540, 0xd40  - 0x540)
    samples = read_utf16_str (f, 0xd40, 0x1540 - 0xd40)

    py_map = {}
    f.seek(0x1540+4)

    while 1:
        py_code = read_uint16 (f)
        py_len  = read_uint16 (f)
        py_str  = read_utf16_str (f, -1, py_len)

        if py_code not in py_map:
            py_map[py_code] = py_str

        if py_str == 'zuo':
            break

    f.seek(hz_offset)
    while f.tell() != file_size:
        word_count   = read_uint16 (f)
        pinyin_count = read_uint16 (f) / 2

        py_set = []
        for i in range(pinyin_count):
            py_id = read_uint16(f)
            py_set.append(py_map[py_id])
        py_str = "'".join (py_set)

        for i in range(word_count):
            word_len = read_uint16(f)
            word_str = read_utf16_str (f, -1, word_len)
            f.read(12)
            yield py_str, word_str

    f.close()

def showtxt (records):
    for (pystr, utf8str) in records:
        print len(utf8str), utf8str

def store(records, f):
    for (pystr, utf8str) in records:
        # f.write("%s\t1\n" %(utf8str.encode("utf8")))
        #f.write("x:1\n")
        f.write("%s\n" %(utf8str.encode("utf8")))

def scel_file_to_txt(scel_filename, txt_filename):
    '''将scel词库转换为.txt格式数据以抓取词频'''
    if not isinstance(scel_filename, unicode):
        scel_filename = scel_filename.decode('utf-8')
    generator = get_word_from_sogou_cell_dict(scel_filename)
    # new_filename = os.path.splitext(filename)[0] + '.txt'
    try:
        with open(txt_filename, 'w') as wf:
            store(generator, wf)
    except:
        pass

def download_cell_words(scel_filename):
    '''下载网络流行词细胞词库'''
    url = 'http://download.pinyin.sogou.com/dict/download_cell.php?id=4&name=网络流行新词【官方推荐】&f=detail'
    headers= {
        'Host': 'download.pinyin.sogou.com',
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36',
        'DNT': '1',
        'Referer': 'http://pinyin.sogou.com/dict/detail/index/4',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        }
    try:
        r = requests.get(url, headers = headers, timeout=20)
    except:
        time.sleep(60)
        try:
            r = requests.get(url, headers = headers, timeout=20)
        except:
            time.sleep(60)
            try:
                r = requests.get(url, headers = headers, timeout=20)
            except:
                return
    codecs.open(scel_filename, mode='wb').write(r.content)

def get_sougou_cell_words():
    base_filename = os.path.join(DOC_95K_PATH, 'doc', 'Cizu_komoxo95K.txt')
    with codecs.open(base_filename, encoding='gbk') as f:
        base_cizu_set = set([item.split('\t')[0] for item in f.readlines() if not item.startswith(';')])
    hot_words_filename = os.path.join(PATH, 'hot_word.txt')
    hot_words_list = [item.strip() for item in codecs.open(hot_words_filename, encoding='utf-8').readlines()]
    print len(hot_words_list)
    filtered_hot_words = [item for item in hot_words_list if item not in base_cizu_set]

def combine_words_pinyin_freq(txt_filename, freq_filename, word_pinyin_freq_filename):
    '''文件的words, pinyin, Pinyin合并到同一个文件中'''
    words_freq_dic = {}
    # words_freq_filename = os.path.join(PATH, 'update.freq')
    with codecs.open(freq_filename, encoding='utf-8') as f:
        for line in f.readlines():
            splited_line = line.split('\t')
            words = splited_line[0]
            freq = splited_line[1]
            words_freq_dic[words] = freq
    # words_pinyin_filename = os.path.join('..', 'update.txt')
    com_str_list = []
    with codecs.open(txt_filename, encoding='utf-16') as f:
        for line in f.readlines():
            splited_line = line.strip().rsplit('\t', 1)
            words_pinyin = splited_line[0]
            words = words_pinyin.split('\t')[0]
            freq = words_freq_dic.get(words)
            if not freq:
                continue
            com_str = words_pinyin + '\t' + freq
            com_str_list.append(com_str)
    codecs.open(word_pinyin_freq_filename, mode='wb', encoding='utf-8').writelines(set(com_str_list))

def make_inorder_by_freq(filename):
    '''使文件按词频倒序排列
    文件格式: 第一列为词，最后一列为词频, \t 分割'''
    with codecs.open(filename, encoding='utf-8') as f:
        line_list_inorder = sorted(f.readlines(), key=lambda x:int(x.split('\t')[-1]), reverse=True)
        codecs.open(filename, mode='wb', encoding='utf-8').writelines(line_list_inorder)

def filtered_hot_words_by_freq(filename):
    update_filename = os.path.join(PATH, 'update.txt')
    total_hot_word_count = 7200
    from gen_new_hot_words import GenHotWords
    festival_words_set = set([item[0] for item in GenHotWords.get_festival_hot_words()])
    with codecs.open(filename, encoding='utf-8') as f:
        line_list = [item for item in f.readlines() if len(item.split('\t')[0])<8]
        filtered_hot_word_set = set(line_list[:total_hot_word_count])
        for line in line_list:
            words = line.split('\t')[0]
            if words in festival_words_set:
                filtered_hot_word_set.add(line)

    if  5000 < len(filtered_hot_word_set) < 8000:
        line_list_inorder = sorted(filtered_hot_word_set, key=lambda x: int(x.split('\t')[-1]), reverse=True)
        codecs.open(update_filename, mode='wb', encoding='utf-16').writelines(line_list_inorder)
    else:
        print ('lenght of filtered_hot_word_set lenght: %s, not between 5000,8000' % (len(filtered_hot_word_set)))

if __name__ == '__main__':

    filename = os.path.join(PATH, 'words_pinyin_freq.txt')
    filtered_hot_words_by_freq(filename)

    # combine_all_words_freq()
    # with codecs.open('words_pinyin_freq.txt', encoding='utf-16') as f:
    #     line_list = f.readlines()
    #     line_set = set(line_list)
    #     print len(line_set),len(line_list)

    def download_test():
        scel_filename = os.path.join(PATH, 'sougou_cell_word.scel')
        download_cell_words(scel_filename)

    def scel_to_txt_test():
        scel_filename = os.path.join(PATH, 'sougou_cell_word.scel')
        txt_filename = os.path.join(PATH, 'sougou_cell_word.txt')
        scel_file_to_txt(scel_filename, txt_filename)