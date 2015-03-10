__author__ = 'wanghuafeng'
import os
import codecs
RELATIVE_FILE_PATH = os.path.dirname(os.path.dirname(__file__))
def read_des_file():
    des_file_name = os.path.join(RELATIVE_FILE_PATH,"update_history.txt")
    des_set =set()
    if not os.path.isfile(des_file_name):
        raise ValueError("File %s not exist!" % des_file_name)
    fileObj = codecs.open(des_file_name,mode='rb',encoding='utf-16')
    for line in fileObj.readlines():
        des_set.add(line.strip())
        splited_line = line.split("\t")
        line_tuple = (splited_line[0],splited_line[1])
        des_set.add(line_tuple)
    fileObj.close()
    return des_set

def write_src_to_des():
    des_set = read_des_file()
    src_file_name = os.path.join(RELATIVE_FILE_PATH,"update.txt")
    des_file_name = os.path.join(RELATIVE_FILE_PATH,"update_history.txt")
    if not os.path.isfile(des_file_name):
        desFileObj = codecs.open(des_file_name,mode='wb',encoding='utf-16')
    desFileObj = codecs.open(des_file_name,mode='a',encoding='utf-16_le')
    if not os.path.isfile(src_file_name):
        raise ValueError("File %s not exist!" % src_file_name)
    srcFileObj = codecs.open(src_file_name,mode='rb',encoding='utf-16')
    for line in srcFileObj.readlines():
        splited_line = line.split("\t")
        line_tuple = (splited_line[0],splited_line[1])
        if line_tuple not in des_set:
            desFileObj.write(line)
            # print line
    desFileObj.close()
    srcFileObj.close()

if __name__ == "__main__":
    write_src_to_des()

