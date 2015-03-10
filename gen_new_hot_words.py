__author__ = 'wanghuafeng'
#coding:utf8
import os
import re
import sys
import codecs
import subprocess
from datetime import datetime, timedelta
from gen_hot_words import add_words_spell_m
from gen_hot_words import remove_repeat_words
from gen_hot_words import sougou_cell_words
ABS_PATH = os.path.abspath(__file__)
try:
    THIS_PATH = os.path.dirname(ABS_PATH)
except:
    THIS_PATH = os.getcwd()
SCTIPT_PATH = os.path.dirname(os.path.dirname(ABS_PATH))#**\chocolate_ime\script
combine_hot_words_filename = os.path.join(THIS_PATH, 'gen_hot_words', "combine_hot_words.txt")

class GenHotWords(object):
    def __init__(self):
        self.words_pinyin_dic = {}
        self.history_word_set = set()
        self._history_hot_words()

    def gen_result_all_txt(self):
        '''generate resust_all.txt'''
        crawl_path = os.path.join(SCTIPT_PATH,"tools","crawl_hot_word")
        sys.path.append(crawl_path)
        try:
            import exportHotWord
        except:
            print ('Module crawl_hot_word not exist!')
        exportHotWord.export()

    def _history_hot_words(self):
        filename = os.path.join(SCTIPT_PATH,"gen_update_words","update_history.txt")
        if not os.path.isfile(filename):
            raise ValueError("File %s not exist"%filename)
        fileObj = codecs.open(filename,mode='rb',encoding='utf-16')
        for line in fileObj.readlines():
            splited_line_tuple = line.split("\t")
            self.history_word_set.add(splited_line_tuple[0])
            check_repeat_word = self.words_pinyin_dic.get(splited_line_tuple[0])
            if check_repeat_word:
                self.words_pinyin_dic[splited_line_tuple[0]] = self.words_pinyin_dic[splited_line_tuple[0]] +\
                                                               ","+ splited_line_tuple[1]
            else:
                self.words_pinyin_dic[splited_line_tuple[0]] = splited_line_tuple[1]

    @staticmethod
    def get_festival_hot_words():
        repeat_time_param_check_list = []
        festival_word_path = os.path.dirname(SCTIPT_PATH)
        filename = os.path.join(festival_word_path, 'doc', 'festival_hot_words.txt')
        file_content_list = []
        with codecs.open(filename, encoding='utf-8') as f:
            file_content_list.extend([item.strip() for item in f.readlines() if item])
        # file_list = [";2014-05-01 : 7", 'a', 'b', 'c',
        #              ';2014-05-08:5', 'd', 'e', 'f',
        #              ';2014-06-01:4', 'g', 'h', 'i']
        festival_word_list = []

        now_datetime = datetime.now()
        current_data_str = now_datetime.strftime('%Y-%m-%d')
        range_valid_flag = False
        for line in file_content_list:
            if line.startswith(';'):
                repeat_time_param_check_list.append(line.strip())
                date_valid_time = line.split(':')
                data_form_str = date_valid_time[0].strip()[1:]
                date_range = date_valid_time[1].strip()
                festival_start_time = data_form_str
                date_end = datetime.strptime(data_form_str, "%Y-%m-%d") + timedelta(days=int(date_range))
                festival_end_time = date_end.strftime("%Y-%m-%d")
                # print festival_start_time,festival_end_time
                if festival_start_time < current_data_str < festival_end_time:
                    range_valid_flag = True
                else:
                    range_valid_flag = False
            elif range_valid_flag:
                festival_word_list.append(line)
        if len(repeat_time_param_check_list) is not len(set(repeat_time_param_check_list)):
            raise ValueError('date_param in festival_hot_words repeated, please check !')

        base_filename = os.path.join(festival_word_path, 'doc', 'Cizu_komoxo95K.txt')
        base_cizu_list = []
        with codecs.open(base_filename, encoding='gbk') as f:
            base_cizu_list.extend([item.split('\t')[0] for item in f.readlines() if not item.startswith(';')])
        base_cizu_set = set(base_cizu_list)
        festival_word_freq_tuple_list =[(item, u'100'+'\n') for item in festival_word_list if item not in base_cizu_set]
        return festival_word_freq_tuple_list

    def gen_sougou_cell_words(self):
        '''搜狗细胞词库'''
        scel_filename = os.path.join(THIS_PATH, 'gen_hot_words', 'sougou_cell_word.scel')
        txt_filename = os.path.join(THIS_PATH, 'gen_hot_words', 'sougou_cell_word.txt')

        sougou_cell_words.download_cell_words(scel_filename)#scel写入到指定文件中
        sougou_cell_words.scel_file_to_txt(scel_filename, txt_filename)#将scel文件转换为.txt文件

        #加载95K本地词库进行过滤
        base_filename = os.path.join(os.path.dirname(SCTIPT_PATH), 'doc', 'Cizu_komoxo95K.txt')
        with codecs.open(base_filename, encoding='gbk') as f:
            base_cizu_set = set([item.split('\t')[0] for item in f.readlines() if not item.startswith(';')])

        hot_words_list = [item.strip() for item in codecs.open(txt_filename, encoding='utf-8').readlines()]
        sougou_words_freq_tuple_list = [(item, u'100'+'\n') for item in hot_words_list if item not in base_cizu_set]
        return sougou_words_freq_tuple_list

    def gen_update_words(self):
        '''
        1、百度、新浪风云榜(result_all.txt)
        2、节日热词(festival_hot_words.txt)
        3、搜狗细胞词库(sougou_cell_word.txt)'''
        src_file_name = os.path.join(SCTIPT_PATH,"tools","crawl_hot_word","result","result_all.txt")#coding:utf8
        searchword = add_words_spell_m.WordsSearch()
        file_obj =  codecs.open(combine_hot_words_filename,mode="wb",encoding="utf-16")
        words_freq_list = [((item[0], u'100'+'\n')) for item in remove_repeat_words.source_norepeat_words(src_file_name)]
        print 'baidu/sina hot words: ', len(words_freq_list)

        #添加节日热词
        festival_word_freq_tuple_list = self.get_festival_hot_words()
        words_freq_list.extend(festival_word_freq_tuple_list)
        print 'festival_words count:', len(festival_word_freq_tuple_list)

        #添加搜狗细胞词库
        sougou_words_freq_tuple_list = self.gen_sougou_cell_words()
        words_freq_list.extend(sougou_words_freq_tuple_list)
        print 'sougou_cell_word count: ', len(sougou_words_freq_tuple_list)

        words_freq_set = set(words_freq_list)
        print 'combine_hot_words.txt count: ', len(words_freq_set)

        for words_freq_tuple in words_freq_set:
            com_str = ""
            freq_strip = re.split(r"\s+",words_freq_tuple[1].strip())[0]#strip '\n' from frequence param
            splited_pinyin_list,splited_word_list = searchword.get_splited_pinyin(words_freq_tuple[0])
            splited_pinyin_str =  " ".join(splited_pinyin_list)
            if len(splited_word_list) > 0:
                for dic in splited_word_list:
                    key_str = "".join(dic.keys()) + " "
                    var_str = ",".join(dic.values()[0]) + ";"
                    key_len = len(dic.keys()[0])
                    dic_value_tuple = dic.values()[0]
                    if key_len > 1:
                        var_str = ",".join(dic_value_tuple[:key_len]) + "-" \
                                  + ",".join(dic_value_tuple[key_len:]) + ";"
                    com_str = com_str + "#" + key_str + var_str
            else:
                com_str = ""
            com_str = com_str + "\n"
            if words_freq_tuple[0] in self.history_word_set:#check if words in history
                words_pinyin_dic_value = self.words_pinyin_dic[words_freq_tuple[0]]
                if "," in words_pinyin_dic_value:#"yu wen le,yu wen yue"
                    splited_pinyin_arr = words_pinyin_dic_value.split(",")#['yu wen le', 'yu wen yue']
                    for repeat_pinyin_str in splited_pinyin_arr:
                        word_pinyin_fre_tuple = (words_freq_tuple[0],repeat_pinyin_str,words_freq_tuple[1])#freq as the last column should add "\n"
                        word_pinyin_fre_format =  "\t".join(word_pinyin_fre_tuple)
                        # print word_pinyin_fre_format
                        file_obj.writelines(word_pinyin_fre_format)
                else:
                    word_pinyin_fre_tuple = (words_freq_tuple[0],words_pinyin_dic_value,words_freq_tuple[1])
                    word_pinyin_fre_format = "\t".join(word_pinyin_fre_tuple)
                    # print word_pinyin_fre_format
                    file_obj.writelines((word_pinyin_fre_format))
            else:#words not in history
                word_pinyin_fre_tuple = (words_freq_tuple[0],splited_pinyin_str,freq_strip,com_str)
                word_pinyin_fre_format =  "\t".join(word_pinyin_fre_tuple)
                # print word_pinyin_fre_format
                file_obj.writelines(word_pinyin_fre_format)

        file_obj.close()

    def filtered_update_txt(self):
        '''去掉数据中的人工校验信息'''
        # txt_filepath = os.path.join(THIS_PATH,"update.txt")
        lines_list = []
        with codecs.open(combine_hot_words_filename, encoding='utf-16') as f:
            for line in f.readlines():
                if "*" in line:
                    line = line.replace('*', '')
                if '#' in line:
                    line = line.split('#')[0].strip() + '\n'
                lines_list.append(line)
        codecs.open(combine_hot_words_filename, mode='wb', encoding='utf-16').writelines(lines_list)

if __name__ =="__main__":
    #判断在否在执行词频抓取操作，若词频抓取仍在执行，则跳过所有步骤，将上次生成的update.txt文件转换为bin文件并上传
    split_pattern = re.compile(r'\s*')
    fab_command = """/usr/local/bin/fab -H s1 -- 'ps -ef | grep "python baidu_freq_spider.py -f combine_hot_words.txt"'"""
    popen = subprocess.Popen(fab_command, shell=True, stdout=subprocess.PIPE)
    baidu_freq_spider = 'python baidu_freq_spider.py -f combine_hot_words.txt'
    IsRunning = baidu_freq_spider in [split_pattern.split(item, 9)[-1].strip() for item in popen.stdout.readlines()]
    print  'IsRunning:*************', IsRunning

    if not IsRunning:#词频抓取任务结束
        #生成新的combine_hot_words.txt文件scp到s1执行词频抓取
        gen_hot_words = GenHotWords()
        gen_hot_words.gen_result_all_txt()
        gen_hot_words.gen_update_words()
        gen_hot_words.filtered_update_txt()
        #移动combine_hot_words.txt到s1：~/wanghuafeng/hot_word_freq目录下
        scp_command = 'scp %s s1:/home/gaius/wanghuafeng/hot_word_freq/' % combine_hot_words_filename
        IsFailed = subprocess.call(scp_command, shell=True)
        if IsFailed:
            print 'combine_hot_words.txt scp from mdev to s1, failed...'
        else:
            print 'combine_hot_words.txt scp from mdev to s1, sucess...'
        #在s1执行抓取操作，生成新的词频文件combine_hot_words.freq
        crawl_fab_command = "/usr/local/bin/fab -H s1 --keepalive=10 -- 'cd /home/gaius/wanghuafeng/hot_word_freq; python baidu_freq_spider.py -f combine_hot_words.txt'"
        IsFailed = subprocess.call(crawl_fab_command, shell=True)
        if IsFailed:
            raise ValueError('baidu_freq_spider exec failed...')
        print 'baidu_freq_spider exec sucess...'

        #将新生成的词频文件combine_hot_words.freq scp到mdev
        scp_command = 'scp s1:/home/gaius/wanghuafeng/hot_word_freq/combine_hot_words.freq ./gen_hot_words'
        IsFailed = subprocess.call(scp_command, shell=True)
        if not IsFailed:#scp 操作成功执行
            print 'combine_hot_words.freq scp from s1 to mdev, sucess...'
            import math
            txt_filename = os.path.join(THIS_PATH, 'gen_hot_words', "combine_hot_words.txt")#utf-16
            freq_filename = os.path.join(THIS_PATH, 'gen_hot_words', 'combine_hot_words.freq')#utf-8
            words_pinyin_freq_filename = os.path.join(THIS_PATH, 'gen_hot_words', 'words_pinyin_freq.txt')#utf-8
            with codecs.open(txt_filename, encoding='utf-16') as txtf:
                txt_file_length = len(txtf.readlines())
            with codecs.open(freq_filename, encoding='utf-8') as freqf:
                freq_file_length = len(freqf.readlines())
            if math.fabs(freq_file_length - txt_file_length) < 1000:#失败量在1000以内
                sougou_cell_words.combine_words_pinyin_freq(txt_filename, freq_filename,
                                                            words_pinyin_freq_filename)#生成words,pinyin,freq格式文件words_pinyin_freq.txt
                sougou_cell_words.make_inorder_by_freq(words_pinyin_freq_filename)#按freq进行排序
                sougou_cell_words.filtered_hot_words_by_freq(words_pinyin_freq_filename)#生成update.txt，行数应在5000，8000之间

                #将此时生成的update.txt文件移动到父目录中，以生成bin文件
                mv_command = 'cp ./gen_hot_words/update.txt .'
                subprocess.call(mv_command, shell=True)
            else:
                print 'txt_file count: %s, freq_file count: %s' % (txt_file_length, freq_file_length)
                # #删除s1上的.freq文件
                # fab_command = "fab -H s1 -- 'rm /home/gaius/wanghuafeng/hot_word_freq/combine_hot_words.freq'"
                # subprocess.call(fab_command, shell=True)
        else:
            print 'combine_hot_words.freq scp from s1 to mdev, failed...'