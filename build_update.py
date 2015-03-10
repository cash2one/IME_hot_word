from tools import *
from codemap import *
from digitlextree import *
import sys

################################################################################
#
# build update database
#
################################################################################

class LextreeUpdate(object):
    def __init__(self, codemap, name, version):
        self._codemap = codemap
        self._elem = codemap._elem
        self._code = codemap._code
        self._word_len = 8
        self._keyboard = codemap._keyboard

        try:
            self._sub_len = {'digit': 6, 'qwerty' : 24, 'suretype' : 12}[self._keyboard]
        except KeyError:
            print 'keyboard type error:', self._keyboard
            sys.exit()
        
        self._version = version

        code = {'gb2312' : 1, 'gbk' : 2, 'gb18030' : 3}
        keyboard = {'digit' : 1, 'suretype' : 2}
        self._v3 = code[self._code] + (self._sub_len << 8)

        print self._version, self._v3

        self._index_map = self.BuildIndexmap()

        self._data = self.GenerateData(name)
        
        return

    def BuildIndexmap(self):
        if self._keyboard == 'digit':
            digit_map = list(u'22233333344444455556667777')
            index_map = [ord(item) - ord('2') for item in digit_map]
        elif self._keyboard == 'qwerty':
            #            a  b  c  d  e  f  g  h  i  j  k  l  m  n  o  p  q  r  s  t  u  v  w  x  y  z 
            index_map = [0, 1, 2, 3, 4, 5, 6, 5, 7, 8, 9, 10,11,10,12,13,14,15,16,17,18,19,20,21,22,23]
        elif self._keyboard == 'suretype':
            digit = [8,  0, 1, 2, 11,
                     9,  3, 3, 4, 6,
                     10, 5, 6, 7 ]
            
            alphabeta = [u'wq', u'er', u'ty', u'ui', u'op',
                         u'as', u'df', u'gh', u'jk', u'l',
                         u'zx', u'cv', u'bn', u'm']

            temp_dict = dict(zip(alphabeta, digit))
            alpha2digit = dict()
            for key in temp_dict.keys():
                for ch in key:
                    alpha2digit[ch] = temp_dict[key]

            index_map = [alpha2digit[item] for item in sorted(alpha2digit.keys())]
        else:
            print 'Erorr keyboard type:', keyboard
            sys.exit()
            
        return index_map

    def Pinyin2Index(self, pinyin):
        if type(self._elem) is ZhuyinElement:
            zhuyin = self._elem.Pinyin2Zhuyin(pinyin)
            return ord(zhuyin[0]) - ord(u'\u3105')
        else:
            return self._index_map[ord(pinyin[0]) - ord('a')]

    def LoadUpdateFile(self, name):
        charset = Charset(self._code)

        word_hanzi = []
        word_pinyin = []
        
        p = re.compile(r'^(\w+)\t(.+)\t(\w+)$', re.U)

        f = codecs.open(name, 'r', 'utf-16')

        for line in f:
            m = p.match(line.strip())
            if m:
                entry, pinyin, freq = m.groups()#words, pinyin, freq
                pinyin = pinyin.encode('ascii').translate(None, '^').decode('ascii')
                
                if len(entry) > self._word_len or not charset.HasChar(entry):
                    print line
                    continue

                word_hanzi.append(entry)
                word_pinyin.append(pinyin)

        word_hz = [[[] for sub in range(self._sub_len)] for l in range(self._word_len - 1)]
        word_py = [[[] for sub in range(self._sub_len)] for l in range(self._word_len - 1)]

        for entry, pinyin in zip(word_hanzi, word_pinyin):
            hz_idx = len(entry) - 2
            sub_idx = self.Pinyin2Index(pinyin.split()[0])
            
            word_hz[hz_idx][sub_idx].append(entry)
            word_py[hz_idx][sub_idx].append(pinyin)

        f.close()
                
        return word_hz, word_py

    def GenerateData(self, name):
        word_hz, word_py = self.LoadUpdateFile(name)

        lexNumber = [ [ 0 for r1 in range(self._sub_len)] for r3 in range(self._word_len - 1)]
        lexOffset = [ [ 0 for r1 in range(self._sub_len)] for r3 in range(self._word_len - 1)]

        for n in range(self._word_len - 1):
            for i in range(self._sub_len):
                lexNumber[n][i] = len(word_hz[n][i])
        print lexNumber
        
        offset = 0
        for n in range(self._word_len - 1):
            for i in range(self._sub_len):
                lexOffset[n][i] = offset
                offset += (n + 2) * lexNumber[n][i] * 2
        print "Max offset must less then 0xFFFF, maxOffset = 0x%04X" % offset
        print lexOffset
        
        data = []
        data.append(self._version >> 16)
        data.append(self._version & 0xFFFF)
        data.append(self._v3)

        for lex in lexNumber:
            for num in lex:
                data.append(num)
                
        for lex in lexOffset:
            for offset in lex:
                data.append(offset)

        for lex_word, lex_pinyin in zip(word_hz, word_py):
            for sub_word, sub_pinyin in zip(lex_word, lex_pinyin):
                for word, pinyin_string in zip(sub_word, sub_pinyin):
                    pinyin_list = pinyin_string.split()
                    if len(word) is not len(pinyin_list):
                        print "Wrong pinyin:", word, pinyin

                    pinyin_list = [item.encode('ascii').translate(None, '^12345').decode('ascii') \
                               for item in pinyin_list]

                    hzCodes = [self._codemap.hzpy2hzcode(hanzi, item) \
                          for (hanzi, item) in zip(word, pinyin_list)]
                
                    data.extend(hzCodes)

        return data

    def WriteShortList(self, f, value_list):
        for value in value_list:
            s = struct.pack(self._fmt, value)
            f.write(s)

    def WriteTotal(self, f, fmt):
        total = 0
        
        total = total + 0xFF
        total = total + 0xFE
        for v in self._data:
            total += v & 0xFF
            total += (v >> 8) & 0xFF

        os = struct.pack(fmt, total)
        f.write(os)
        
    def WriteData(self):
        name = 'update_file_%s_%s_le_%d.bin' % (self._code, self._keyboard, self._version)
        self._fmt = '<H'
        f = open(name, 'wb')
        print 'Write to file', name, '...',

        self.WriteShortList(f, [0xFFFE])
        self.WriteShortList(f, self._data)
        self.WriteTotal(f, '<L')

        f.close()
        print 'Done.'

        name = 'update_file_%s_%s_be_%d.bin' % (self._code, self._keyboard, self._version)
        self._fmt = '>H'
        f = open(name, 'wb')
        print 'Write to file', name, '...',

        self.WriteShortList(f, [0xFFFE])
        self.WriteShortList(f, self._data)
        self.WriteTotal(f, '>L')

        f.close()
        print 'Done.'
        
def Build_Update(name, version):
    codes = {'gb2312' : 1, 'gbk' : 2, 'gb18030':3, 'big5':4, 'big5normal':5}
    for code in ['gbk']:
        for keyboard in ['digit']:
            elem = PinyinElement()
            codemap = Codemap(code, elem, keyboard)

            lextree = LextreeUpdate(codemap, name, version)
            lextree.WriteData()

if __name__=='__main__':
    Build_Update(sys.argv[1], int(sys.argv[2], 10))
        
