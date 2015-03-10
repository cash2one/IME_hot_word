
from tools import *
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

try:
    THIS_PATH = os.path.dirname(__file__)    
except NameError:
    THIS_PATH = os.getcwd()

def get_parent(p):
    if not os.path.sep in p or os.path.ismount(p):
        return None
    
    return os.path.split(p)[0]

def find_file(filename):

    if os.path.isabs(filename):
        if not os.path.isfile(filename):
            raise ValueError('File %s not found!' % filename)
        return filename
    
    search_path = THIS_PATH
    
    while search_path:
        expect_file = os.path.join(search_path, filename)        
        if os.path.isfile(expect_file):
            break
        search_path = get_parent(search_path)

    if os.path.isfile(expect_file):
        return expect_file

    raise ValueError('File %s not found!' % filename)

################################################################################
#
# Codemap
#
################################################################################
class Codemap(object):
    """
    convert unicode to hzcode, hzcode has relation to unicode and pinyin
    
        hzcode is:
            [0x4E00, 0x9FAF]     normal pinyin for hanzi
            [0x9FAF + 1, 0x9FB0 + dyz_num] dyz sorted by unicode
            [0x9FB0 + dyz_num + 1, extra]  CJK ideographs extra A sorted by unicode
    """
    def __init__(self, code, pinyin_element, keyboard):
        self._code = code
        self._elem = pinyin_element
        self._keyboard = keyboard
        if type(self._elem) is ZhuyinElement:
            print 'HasTone'
            self._bHasTone = True
        else:
            self._bHasTone = False
        
        self._hz_beg, self._hz_end = 0, 0
        self._hz_py = []
        self._dyz_hz, self._dyz_py = [], []
        self._extra_hz, self._extra_py = [], []

        self.BuildCodemap()
        return

    def GetCharset(self):
        if 'gb2312special' in self._code:
            return 0x0100
        
        code2charset = {'gb2312' : 0x0100, 'gbk':0x0200, 'gb18030' : 0x0400,
                        'big5':0x0800, 'big5normal':0x1000, 'big5hkscs':0x2000}
        if not code2charset.has_key(self._code):
            print 'Error code...'
        
        return code2charset[self._code]
    
    def Print(self, f, name, offset, le, be):
        size = 0
        if self._hz_py:
            name_hzpy = "hzpyTable_%s" % name
            data = []
            data.extend([self._elem.Pinyin2Code(pinyin) if pinyin else 0 for pinyin in self._hz_py])
            PrintWordArray(f, name_hzpy, data)
            size += 2 * len(data)

            off_hzpy = offset
            offset = offset + DumpWordArray(le, be, data)
            
        else:
            name_hzpy = "0"
            off_hzpy = 0

        if self._dyz_hz:
            name_dyz = "dyzTable_%s" % name
            n = len(self._dyz_hz) * 2
            data = [0 for i in range(n)]
            data[0:n:2] = [ord(ch) for ch in self._dyz_hz]
            data[1:n:2] = [self._elem.Pinyin2Code(pinyin) for pinyin in self._dyz_py]
            PrintWordArray(f, name_dyz, data)
            size += 2 * len(data)

            off_dyz = offset
            offset = offset + DumpWordArray(le, be, data)
        else:
            name_dyz = "0"
            off_dyz = 0

        if self._extra_hz:
            name_extra = "extraTable_%s" % name
            n = len(self._extra_hz) * 2
            data = [0 for i in range(n)]
            data[0:n:2] = [ord(ch) for ch in self._extra_hz]
            data[1:n:2] = [self._elem.Pinyin2Code(pinyin) for pinyin in self._extra_py]
            PrintWordArray(f, name_extra, data)
            size += 2 * len(data)

            off_extra = offset
            offset = offset + DumpWordArray(le, be, data)
        else:
            name_extra = "0"
            off_extra = 0

        if self._hz_py:
            nFormat = 1
        else:
            nFormat = 2

        if type(self._elem) is ZhuyinElement:
            nFormat = 0x0020 + nFormat
        else:
            nFormat = 0x0010 + nFormat

        nFormat = nFormat + self.GetCharset()
        
        lines = []
        lines.append("/* nFormat */             0x%04X" % (nFormat))
        lines.append("/* hanzi number */        %d" % len(self._hz_py))
        lines.append("/* dyz number */          %d" % len(self._dyz_hz))
        lines.append("/* extra number */        %d" % len(self._extra_hz))
        lines.append("")
        lines.append("/* hzpy table */          %s" % name_hzpy)
        lines.append("/* dyz table */           %s" % name_dyz)
        lines.append("/* extra table */         %s" % name_extra)
        lines.append("")
        lines.append("/* pycode_id size */      %d" % 0)
        lines.append("/* pycode_id table */     %s" % "0")
        lines.append("/* pycode table */        %s" % "0")
        lines.append("")

        struct_array = [nFormat, len(self._hz_py), len(self._dyz_hz), len(self._extra_hz), \
                        off_hzpy, off_dyz, off_extra, 0, 0, 0]
        return lines, size, offset, struct_array

    def BuildCodemap(self):
        if self._code is 'big5' or self._code is 'big5normal' or self._code is 'big5hkscs':
            if self._bHasTone:
                name = r'hanzi_tc.txt'
            else:
                name = r'hanzi_tc_no_tone.txt'
        else:
            if self._bHasTone:
                name = r'hanzi_sc.txt'
            else:
                # update by chenchao
                name = find_file('doc/HZout_NoTone.txt')                

        name_extra = 'extra_a.txt'
        
        hz2py, dyz_hz2py = self.LoadHanziPinyin(name)
        if self._code is 'big5hkscs':
            self.AppendHkscsCjk(hz2py, dyz_hz2py)

        self._valid_pinyin = set(hz2py.values())
        for pinyins in dyz_hz2py.values():
            self._valid_pinyin = self._valid_pinyin | set(pinyins)
            
        # use compact format if code is 'gb2312'
        if self._code == 'gb2312' or 'gb2312special' in self._code:
            for hanzi, pinyin in hz2py.iteritems():
                dyz_hz2py.setdefault(hanzi, []).insert(0, pinyin)
            hz2py.clear()

        max_dyz = max([len(item) for item in dyz_hz2py.values()])
        print "max dyz is:", max_dyz, \
              ''.join([key for key in dyz_hz2py.keys() if len(dyz_hz2py[key]) == max_dyz])
        
        # normal pinyin
        if hz2py:
            self._hz_beg = 0x4E00
            self._hz_end = 0x9FAF
            self._hz_py = [u'' for i in range(0x9FAF - 0x4E00 + 1)]
            for hanzi, pinyin in hz2py.iteritems():
                self._hz_py[ord(hanzi) - 0x4E00] = pinyin

        # dyz
        for hanzi in sorted(dyz_hz2py.keys()):
            for pinyin in dyz_hz2py[hanzi]:
                self._dyz_hz.append(hanzi)
                self._dyz_py.append(pinyin)

        # extra A                
        if self._code == 'gb18030':
            self.LoadExtra(name_extra)

        if self._code is 'big5hkscs':
            self.LoadHkscsExtra()

        self._valid_pinyin = self._valid_pinyin | set(self._extra_py)
        # remove tone for valid pinyin
        if self._bHasTone:
            self._valid_pinyin = set([item[0:-1] for item in self._valid_pinyin])
        
        if len(self._hz_py) + len(self._dyz_hz) + len(self._extra_hz) > (0xFFFF - 0x4E00):
            print "Error: the biggest code must less than 0xFFFF"
            sys.exit()
        return

    def hzpy2hzcode(self, hanzi, pinyin):
        if not self._bHasTone and pinyin[-1] in self._elem._shengdiao:
            pinyin = pinyin[:-1]

        # normal pinyin
        if self._hz_py:
            if self._hz_py[ord(hanzi) - 0x4E00] == pinyin:
                return ord(hanzi)

        # extra A 
        if ord(hanzi) < self._hz_beg:   # extra a
            iBeg = bisect.bisect_left(self._extra_hz, hanzi)
            iEnd = bisect.bisect_right(self._extra_hz, hanzi)
            for index in range(iBeg, iEnd):
                if self._extra_py[index] == pinyin:
                    return (self._hz_end) + len(self._dyz_hz) + index

            print 'There isn\'t this pinyin:', hanzi, pinyin
            sys.exit()

        # dyz
        iBeg = bisect.bisect_left(self._dyz_hz, hanzi)
        iEnd = bisect.bisect_right(self._dyz_hz, hanzi)
        for index in range(iBeg, iEnd):
            if (self._dyz_py[index] == pinyin):
                return self._hz_end + index
            
        print 'There isn\'t this pinyin:', hanzi, pinyin
        sys.exit()
        return
    
    def LoadHanziPinyin(self, name):
        print name, "is loading...",
        hz2py = {}
        dyz_hz2py = {}

        charset = Charset(self._code)
        
        m = re.compile("^;")
        f = codecs.open(name, 'r', 'utf-16')
        for line in f:
            line = line.strip()
            if line and not m.search(line):
                hanzi, pinyin = line.split()[:2]
                if hanzi == u'\u3007':
                    hanzi = u'\u9fa7'
                if charset.HasChar(hanzi):
                    if hz2py.has_key(hanzi):
                        dyz_hz2py.setdefault(hanzi, []).append(pinyin)
                    else:
                        hz2py[hanzi] = pinyin
        f.close()
        print "Done!"

        return hz2py, dyz_hz2py

    def AppendHkscsCjk(self, hz2py, dyz_hz2py):
        f = open('hkscs_pinyin.txt')
        for line in f:
            line = line.strip()
            v = line.split('\t')
            if len(v) is 2:
                hanzi = unichr(int(v[0][2:], 16))
                if ord(hanzi) >= 0x4e00 and ord(hanzi) <= 0x9FAF and hanzi not in hz2py:
                    pinyins = v[1].split()
                    pinyins = [item.lower() for item in pinyins]

                    hz2py[hanzi] = pinyins[0]
                    for pinyin in pinyins[1:]:
                        dyz_hz2py.setdefault(hanzi, []).append(pinyin)
                        
        f.close()
        return
    
    def LoadExtra(self, name):
        m = re.compile("^;")
        f = open(name)
        for line in f:
            if line and not m.search(line):
                v = line.split()
                uni = v[0][2:]
                pinyin_list = v[1:]
                if self._bHasTone:
                    pinyin_list = [item.lower() for item in pinyin_list]
                else:
                    pinyin_list = [item[:-1].lower() for item in pinyin_list]
                    pinyin_list = list(set(pinyin_list))
                for pinyin in pinyin_list:
                    self._extra_hz.append(unichr(int(uni, 16)))
                    self._extra_py.append(unicode(pinyin))
        f.close()
        return

    def LoadHkscsExtra(self):
        f = open('hkscs_pinyin.txt')
        for line in f:
            line = line.strip()
            v = line.split('\t')
            if len(v) is 2:
                hanzi = unichr(int(v[0][2:], 16))
                if ord(hanzi) < 0x4E00:
                    pinyin_list = v[1].split()
                    pinyin_list = [item.lower() for item in pinyin_list]

                for pinyin in pinyin_list:
                    self._extra_hz.append(hanzi)
                    self._extra_py.append(unicode(pinyin))
        f.close()
        return
    
class Codemap_Compact(Codemap):
    def __init__(self, code, pinyin_element, keyboard, syslextree):
        super(Codemap_Compact, self).__init__(code, pinyin_element, keyboard)

        self._zipin_hz = syslextree._zipin_hz
        self._zipin_py = syslextree._zipin_py
        
    def Print(self, f, name, offset, le, be):
        size = 0
        if type(self._elem) is ZhuyinElement:
            data = []
            for pinyin in self._zipin_py:
                pycode = self._elem.Pinyin2Code(pinyin)
                data.append(pycode)
            PrintWordArray(f, "pycode_table_%s" % name, data)
            size += 2 * len(data)

            off_pycode_table = offset
            offset = offset + DumpWordArray(le, be, data)
            
            nFormat = 0x0004
            
        else:
            pinyin_list = sorted(self._valid_pinyin)
            pycode_list = [self._elem.Pinyin2Code(pinyin) for pinyin in pinyin_list]

            tab = bit_tab()
            for pycode in pycode_list:
                tab.add(pycode, 11)
            data = tab.get()
            PrintByteArray(f, "pycode_id_table_%s" % name, data)
            size += len(data)

            off_pycode_id_table = offset
            offset = offset + DumpByteArray(le, be, data)
            
            tab = bit_tab()
            for pinyin in self._zipin_py:
                idPycode = pinyin_list.index(pinyin)
                tab.add(idPycode, 9)
            data = tab.get()
            PrintByteArray(f, "pycode_table_%s" % name, data)
            size += len(data)

            off_pycode_table = offset
            offset = offset + DumpByteArray(le, be, data)
            
            nFormat = 0x0004

        if type(self._elem) is ZhuyinElement:
            nFormat = 0x0020 + nFormat
        else:
            nFormat = 0x0010 + nFormat

        nFormat = nFormat + self.GetCharset()

        lines = []
        lines.append("/* nFormat */             0x%04X" % (nFormat))
        lines.append("/* hanzi number */        %d" % len(self._zipin_py))
        lines.append("/* dyz number */          %d" % 0)
        lines.append("")
        lines.append("/* hzpy table */          %s" % "0")
        lines.append("/* dyz table */           %s" % "0")
        lines.append("/* extra number */        %d" % 0)
        lines.append("/* extra table */         %s" % "0")
        lines.append("")
        if type(self._elem) is ZhuyinElement:
            lines.append("/* pycode id size */      %d" % 0)
            lines.append("/* pycode id table */     %s" % 0)
        else:            
            lines.append("/* pycode id size */      %d" % len(pinyin_list))
            lines.append("/* pycode id table */     %s" % ("pycode_id_table_%s" % name))
        lines.append("/* pycode table */        %s" % ("(const unsigned char*)pycode_table_%s" % name))
        lines.append("")

        if type(self._elem) is ZhuyinElement:
            struct_array = [nFormat, len(self._zipin_py), 0, 0, 0, 0, 0, 0, 0, off_pycode_table]
        else:
            struct_array = [nFormat, len(self._zipin_py), 0, 0, 0, 0, 0, \
                            len(pinyin_list), off_pycode_id_table, off_pycode_table]
            
        return lines, size, offset, struct_array
        
        return
    
            
        
            
