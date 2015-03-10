import os
import time
import codecs
try:
    THIS_PATH = os.path.dirname(__file__)
except NameError, e:
    THIS_PATH = os.getcwd()
SRC_FILE_NAME = os.path.join(THIS_PATH, "data","result_all.txt")#coding:utf8
# DES_FILE_NAME1 = os.path.join(THIS_PATH, "data","Add_Name.txt")#coding:gbk
# DES_FILE_NAME = os.path.join(r"E:\SVN\chocolate_ime\doc\Cizu_komoxo95K.txt")#coding:gbk
# DES_FILE_LIST = [DES_FILE_NAME1,DES_FILE_NAME2]
IME_FILENAME =  os.path.dirname(os.path.dirname(os.path.dirname(THIS_PATH)))
DES_FILE_NAME = os.path.join(IME_FILENAME, 'doc', 'Cizu_komoxo95K.txt')
def smart_open(filename, default_encoding = 'utf-8'):
    ''' Auto-detect file encoding, and open for read in correct encoding. '''
    if not os.path.isfile(filename):
        raise ValueError('File %s not exist!' % filename)
    with open(filename, 'rb') as f:
        bom = f.read(2)
        if bom in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE):
            encoding = 'utf-16'
        else:
            bom = bom + f.read(1)
            if bom == codecs.BOM_UTF8:
                encoding = 'utf-8-sig'
            else:
                encoding = default_encoding
    return codecs.open(filename, mode = 'rb', encoding = encoding)

def source_words(source_file_name):
    '''return words list in source file'''
    fileObj=smart_open(source_file_name,"utf-8")
    source_words_set = set()
    for line in fileObj:
        splited_line_list = line.split("\t")
        splited_line_tuple = tuple(splited_line_list)
        source_words_set.add(splited_line_tuple)
    return source_words_set

def dest_file_words():
    ''' return words list in destination file'''
    dest_words_list = set()
    # for dest_file_name in DES_FILE_LIST:
    fileObj = smart_open(DES_FILE_NAME,"gbk")
    print DES_FILE_NAME
    for line in fileObj:
        splited_line = line.split("\t")[0]
        if splited_line.startswith(";"):
            pass
        else:
            dest_words_list.add(splited_line)
    return dest_words_list

def source_norepeat_words(filename):
    source_words_set = source_words(filename)
    dest_words_total_set = dest_file_words()
    words_freq_list = []
    for word in source_words_set:
        if word[0] not in dest_words_total_set:
            words_freq_list.append(word)
        # else:
        #     print word[0]

            # words_freq_str = "\t".join(word)
            # print words_freq_str
    # print len(words_freq_list)
    return words_freq_list
# filename = r'E:\SVN\chocolate_ime\script\tools\crawl_hot_word\result\result_all.txt'
# source_norepeat_words(filename)

# if __name__ == "__main__":
#     # output_norepeat_words()
#     source_norepeat_words(SRC_FILE_NAME)
