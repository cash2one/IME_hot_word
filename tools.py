
"""
    usefull tools

"""

import re
import codecs
import struct
import bisect
import sys

def crc(buf):
    CRC_BASE = 65521
    CRC_NMAX = 5552
    l = len(buf)
    ss = [1, 0]
    b = buf
    
    def CRC_DO1(i):
        ss[0] += ord(b[i])
        ss[1] += ss[0]

    def CRC_DO2(i):
        CRC_DO1(i)
        CRC_DO1(i + 1)

    def CRC_DO4(i):
        CRC_DO2(i)
        CRC_DO2(i + 2)

    def CRC_DO8(i):
        CRC_DO4(i)
        CRC_DO4(i + 4)
            
    def CRC_DO16():
        CRC_DO8(0)
        CRC_DO8(8)

    while l > 0:
        k = min(l, CRC_NMAX)
        l -= k
        while k >= 16:
            CRC_DO16()
            b = b[16:]
            k -= 16
        while k != 0:
            ss[0] += ord(b[0])
            b = b[1:]
            ss[1] += ss[0]
            k -= 1
    
        ss[0] %= CRC_BASE
        ss[1] %= CRC_BASE
    
    return ss[1] << 16 | ss[0]

def PrintLongArray(f, name, data):
    f.write("static const unsigned long %s[%d] = {"  % (name, len(data)))
    for i in range(len(data)):
        if i % 10 == 0:
            f.write("\n")
            
        f.write("  0x%08X" % data[i])

        if i == len(data) - 1:
            f.write("\n};\n\n")
        else:
            f.write(",")
    return

def PrintWordArray(f, name, data):
    f.write("static const unsigned short %s[%d] = {"  % (name, len(data)))
    for i in range(len(data)):
        if i % 10 == 0:
            f.write("\n")
            
        f.write("  0x%04X" % data[i])

        if i == len(data) - 1:
            f.write("\n};\n\n")
        else:
            f.write(",")
    return

def PrintByteArray(f, name, data):
    f.write("static const unsigned char %s[%d] = {"  % (name, len(data)))
    for i in range(len(data)):
        if i % 10 == 0:
            f.write("\n")
            
        f.write("  0x%02X" % data[i])

        if i == len(data) - 1:
            f.write("\n};\n\n")
        else:
            f.write(",")
    return

def DumpLongArray(le, be, data):
    pad = len(data) % 2
    
    for item in data:
        le.append(struct.pack('<L', item))
        be.append(struct.pack('>L', item))

    for i in range(pad):
        le.append(struct.pack('L', 0))
        be.append(struct.pack('L', 0))
    
    return (len(data) + pad) * 2

def DumpWordArray(le, be, data):
    pad = len(data) % 2
    
    for item in data:
        le.append(struct.pack('<H', item))
        be.append(struct.pack('>H', item))

    for i in range(pad):
        le.append(struct.pack('H', 0))
        be.append(struct.pack('H', 0))
    
    return (len(data) + pad) * 2

def DumpByteArray(le, be, data):
    pad = 4 - len(data) % 4
    for item in data:
        le.append(struct.pack('<B', item))
        be.append(struct.pack('>B', item))

    if pad is 1 or pad is 3:
        print pad
        
    for i in range(pad):
        le.append(struct.pack('B', 0))
        be.append(struct.pack('B', 0))
        
    return len(data) + pad

################################################################################
#
# Fuzzy class
#
################################################################################

class Fuzzy:
    def __init__(self):
        self._shengmu_dic = {}
        self._yunmu_dic = {}
        shengmu_fuzzy = ( \
            u"zh", u"z", u"ch", u"c", u"sh", u"s", u"h", u"f", u"n", u"l")
        yunmu_fuzzy = ( \
            u"in", u"ing", u"en", u"eng", u"an", u"ang", u"ian", u"iang",\
            u"uan", u"uang")
        
        self.BuildFuzzyDic(shengmu_fuzzy, True)
        self.BuildFuzzyDic(yunmu_fuzzy, False)
        return

    def BuildFuzzyDic(self, fuzzy_list, isShengmu):
        for i, yin in enumerate(fuzzy_list):
            if (i % 2):
                fuzzy = fuzzy_list[i - 1]
            else:
                fuzzy = fuzzy_list[i + 1]
            mask = 0x01 << (i / 2)
            if (isShengmu):
                self._shengmu_dic[yin] = (fuzzy, mask)
            else:
                self._yunmu_dic[yin] = (fuzzy, mask)

        return
    
    def FindFuzzy(self, yin, isShengmu):
        if (isShengmu):
            fuzzy_dic = self._shengmu_dic
        else:
            fuzzy_dic = self._yunmu_dic

        if yin in fuzzy_dic:
            return fuzzy_dic[yin]
        else:
            return "", 0
#============================================================================

class bit_tab:
    
    def __init__(self):
        self.data = [ ]
        self.remain_bits = 0
        self.remain_data = 0

    def add(self, code, bits):
        assert( (code >= 0) and (code < 65536) )
        assert( (bits > 0) and (bits <= 16) )

        assert( (self.remain_bits >= 0) and (self.remain_bits < 8) )
        assert( (self.remain_data >= 0) and (self.remain_data < 256) )

        self.remain_data += code << self.remain_bits
        self.remain_bits += bits
        
        if self.remain_bits >= 8:
            self.data.append(self.remain_data % 256)
            self.remain_data >>= 8
            self.remain_bits -= 8

        if self.remain_bits >= 8:
            self.data.append(self.remain_data % 256)
            self.remain_data >>= 8
            self.remain_bits -= 8

        assert( (self.remain_bits >= 0) and (self.remain_bits < 8) )
        assert( (self.remain_data >= 0) and (self.remain_data < 256) )

    def get(self):
        assert( (self.remain_bits >= 0) and (self.remain_bits < 8) )
        assert( (self.remain_data >= 0) and (self.remain_data < 256) )

        if self.remain_bits > 0:
            self.data.append(self.remain_data)

        self.data.append(0)
        self.data.append(0)
        self.data.append(0)

        return self.data

###############################################################################
#
# charset
#
###############################################################################

class Charset:
    """
    charset define gb2312, gbk, gb18030, big5, big5normal
    """
    def __init__(self, code):
        self._code = code
        if self._code is 'big5hkscs':
            self._hkscs = set()
            f = open('hkscs_pinyin.txt')
            for line in f:
                line = line.strip()
                v = line.split('\t')
                if len(v) is 2:
                    self._hkscs.add(unichr(int(v[0][2:], 16)))

            f.close()

        if 'gb2312special' in self._code:
            l = len('gb2312special')
            special_name = 'subset_%s.txt' % self._code[l:]
            self._gb2312special = set()
            f = codecs.open(special_name, 'r', 'utf-16')
            for line in f:
                line = line.strip()
                for ch in line:
                    self._gb2312special.add(ch)

            f.close()
            print 'length of gb2312spceial is:', len(self._gb2312special)
        return
    
    def HasChar(self, su):
        if self._code is 'gb2312':
            return len(su.encode('gb2312', 'ignore')) == len(su) * 2
        elif self._code is 'gbk':
            if len(su) == 1 and ord(su[0]) == 0x9fa7:
                return True
            return len(su.encode('gbk', 'ignore')) == len(su) * 2
        elif self._code is 'gb18030':
            return len(su.encode('gb18030', 'ignore')) == len(su) * 2
        elif self._code is 'big5':
            return len(su.encode('big5','ignore')) == len(su) * 2
        elif self._code is 'big5normal':
            big5code = su.encode('cp950', 'ignore')
            if len(big5code) != len(su) * 2:
                return False
            return all([ord(item) <= 0xC6 for item in big5code[::2]])
        elif self._code is 'big5hkscs':
            if len(su.encode('big5','ignore')) == len(su) * 2:
                return True
            return all([item in self._hkscs for item in su])
        elif 'gb2312special' in self._code:
            return all([item in self._gb2312special for item in su])
        else:
            print 'No code defined:', code
            sys.exit()

        return

#################################################################################
#
# PinyinElement
#
#################################################################################

class PinyinElement(object):
    def __init__(self):
        """
        Load shengmu, yunmu, shengdiao and pinyin table.
        """
        res_names = ['shengmu.txt', 'yunmu.txt', 'shengdiao.txt', 'pinyin.txt']
        self._shengmu, self._yunmu, self._shengdiao, self._pinyin = \
                       [self.LoadRes(name) for name in res_names]
        self._shengmu.reverse()
        self._yunmu.reverse()
        return
    
    def Pinyin2Code(self, pinyin, bTone = False):
        """
        Get PYCODE for pinyin
        """
        if bTone:
            tone = pinyin[-1]
            if tone in self._shengdiao:
                sd_index = self._shengdiao.index(shengdiao) + 1
            else:
                print 'no sheng diao in:', pinyin
                sys.exit()
        else:
            sd_index = 0
            shengdiao = u''

        sm_index, shengmu, ym_index, yunmu = \
                  self.SplitePinyin(pinyin[:len(pinyin) - len(shengdiao)])

        #Calc pinyin code
        py_code = sm_index | (ym_index << 5) | (sd_index << 11)

        return py_code

    def LoadRes(self, name):
        """
        Load Shengmu, Yunmu, shengdiao and pinyin files.
        """

        ret = []
        m = re.compile("^;")
        f = codecs.open(name, 'r', 'utf-16')
        for line in f:
            line = line.strip()
            if not line or m.search(line):
                continue
            ret.append(line)

        f.close()
        ret.sort()
        return ret
    
    def SplitePinyin(self, pinyin):
        """
        Splite pinyin without shengdiao
        """
        # check pinyin
        if not pinyin or pinyin[-1] in self._shengdiao:
            print "Error pinyin, or shengdiao is not needed:", pinyin
            sys.exit()

        #shengmu and sm_index
        for i, shengmu in enumerate(self._shengmu):
            if shengmu == pinyin[0 : len(shengmu)]:
                sm_index = i + 1
                break
        else:
            shengmu = u''
            sm_index = 0

        #yunmu and ym_index
        yunmu = pinyin[len(shengmu) :]
        if yunmu in self._yunmu:
            ym_index = self._yunmu.index(yunmu) + 1
        else:
            ym_index = 0
            
        return sm_index, shengmu, ym_index, yunmu
    
class ZhuyinElement(PinyinElement):
    def __init__(self):
        res_names = ['shengmu_zy.txt', 'yunmu_zy.txt', 'tone_zy.txt', 'zhuyin_table.txt']

        self._shengmu = sorted(self.LoadElemTable(res_names[0]).keys())  # r'shenmu.txt'
        self._yunmu = sorted(self.LoadElemTable(res_names[1]).keys())   # r'yunmu.txt'

        tonemap = self.LoadElemTable(res_names[2])              # r'tone.txt'
        self._shengdiao = [tonemap[key] for key in sorted(tonemap.keys())]

        self._pinyin2zhuyin = dict()

        m = re.compile('^;')
        f = codecs.open(res_names[3], 'r', 'utf-16')
        for line in f:
            line = line.strip()
            if line and not m.search(line):
                zhuyin, pinyin = line.split()[:2]
                if self._pinyin2zhuyin.has_key(pinyin):
                    print 'zhuyin-pinyin table error:', line
                    sys.exit()
                else:
                    self._pinyin2zhuyin[pinyin] = zhuyin
        f.close()

    def LoadElemTable(self, name):
        f = codecs.open(name, 'r', 'utf_16')
        lines = f.readlines()
        f.close()

        zhuyinmap = dict()
        for line in lines:
            line = line.strip()
            if line and line[0] != r';':
                v = line.split()
                zhuyinmap[v[0]] = v[1]

        return zhuyinmap
    def Pinyin2Zhuyin(self, pinyin):
        if pinyin[-1] in r'12345':
            pinyin = pinyin[0:-1]
        try:
            zhuyin = self._pinyin2zhuyin[pinyin]
        except:
            print pinyin
        return zhuyin

    def Pinyin2Code(self, pinyin, ):
        """
        Get PYCODE for pinyin
        """
        if pinyin[-1] not in r'12345':
            print "No tone: %s, Exit!" % pinyin
            sys.exit()

        tone = int(pinyin[-1])
        zhuyin = self._pinyin2zhuyin[pinyin[:-1]]

        if not zhuyin:
            print pinyin

        if zhuyin[0] in self._shengmu:
            shengmu = self._shengmu.index(zhuyin[0]) + 1
            zhuyin = zhuyin[1:]
        else:
            shengmu = 0

        if zhuyin:
            try:
                yunmu = self._yunmu.index(zhuyin) + 1
            except ValueError:
                print zhuyin
                sys.exit()
        else:       # zhi chi shi ri zi ci si don't have yunmu
            yunmu = 0

        code = shengmu + (yunmu << 5) + (tone << 11)

        return code
