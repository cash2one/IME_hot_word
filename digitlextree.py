
from tools import *

################################################################################
#
# DigitTree class
#
################################################################################

class DigitTree:
    def __init__(self, digit):
        self._digit = digit
        self._child = []
        self._codemask = []
        
    def Add(self, digits, codemask):
        self._codemask.append(codemask)

        if len(digits) == 0 :
            return
        
        for child in self._child:
            if child._digit == digits[0] :
                child.Add(digits[1:], codemask)
                break
        else:
            child = DigitTree(digits[0])
            self._child.append(child)
            child.Add(digits[1:], codemask)

    def Count(self, index):
        for tree in self._child:
            index = tree.Count(index + 1)
        return index
    
    def PrintTree(self, f, index):
        line = "%-4d %2c  %-8d%-8d\n" % (index, self._digit, \
                                            self._codemask[0], \
                                            self._codemask[-1] + 1)
        f.write(line)
        for tree in self._child:
            index = tree.PrintTree(f, index + 1)

        return index

################################################################################
#
# DigitLextree class
#
################################################################################

class DigitLextree(object):
    def __init__(self, codemap):
        self._codemap = codemap
        self._keyboard = codemap._keyboard

        self._elem = codemap._elem

        self._pinyin2digit = self.BuildPinyinDigitMap()

        if type(self._elem) is not ZhuyinElement:
            self._digit_dic, self._lextree = self.BuildDigitLextree()
            
        return
    
    def Print(self, f, name, offset, le, be):
        size = 0
        data = []
        for i, shengmu in enumerate(self._elem._shengmu):
            if type(self._elem) is ZhuyinElement:
                p = [0 for i in range(2)]
            else:
                p = [0 for i in range(3)]
            p[:len(shengmu)] = [ord(ch) for ch in shengmu]
            data.extend(p)
        PrintWordArray(f, "shengmu_%s" % name, data)
        size += 2 * len(data)

        off_shengmu = offset
        offset = offset + DumpWordArray(le, be, data)
        
        data = []
        for yunmu in self._elem._yunmu:
            if type(self._elem) is ZhuyinElement:
                p = [0 for i in range(3)]
            else:
                p = [0 for i in range(5)]
                
            p[:len(yunmu)] = [ord(ch) for ch in yunmu]
            data.extend(p)
        PrintWordArray(f, "yunmu_%s" % name, data)
        size += 2 * len(data)

        off_yunmu = offset
        offset = offset + DumpWordArray(le, be, data)
        
        if type(self._elem) is ZhuyinElement:
            data = []
            for shengdiao in self._elem._shengdiao:
                p = [0 for i in range(2)]
                p[:len(shengdiao)] = [ord(ch) for ch in shengdiao]
                data.extend(p)
            PrintWordArray(f, "shengdiao_%s" % name, data)
            size += 2 * len(data)

            off_shengdiao = offset
            offset = offset + DumpWordArray(le, be, data)

        data = []
        if type(self._elem) is ZhuyinElement:
            pinyin_list = [self._elem.Pinyin2Zhuyin(item) for item in self._codemap._valid_pinyin]
            pinyin_list.extend(self._elem._shengmu)
            pinyin_list = sorted(pinyin_list)

            for pinyin in pinyin_list:
                p = [0 for i in range(4)]
                p[:len(pinyin)] = [ord(ch) for ch in pinyin]
                data.extend(p)
            PrintWordArray(f, "pinyin_%s" % name, data)
            size += 2 * len(data)

            off_pinyin = offset
            offset = offset + DumpWordArray(le, be, data)
            
        else:
            pinyin_list = sorted((self._codemap._valid_pinyin | set(self._elem._shengmu)))
            for pinyin in pinyin_list:
                p = [0 for i in range(7)]
                p[:len(pinyin)] = [ord(ch) for ch in pinyin]
                data.extend(p)
            PrintWordArray(f, "pinyin_%s" % name, data)
            size += 2 * len(data)

            off_pinyin = offset
            offset = offset + DumpWordArray(le, be, data)

        if self._codemap._keyboard != 'qwerty':
            data = []
            for dic in self._digit_dic:
                data.append(dic._code)
                data.append(dic._mask)
            PrintWordArray(f, "pinyin_dic_%s" % name, data)
            size += 2 * len(data)

            off_pinyin_dic = offset
            offset = offset + DumpWordArray(le, be, data)
            
            data = []
            for lex in self._lextree:
                data.extend([ord(lex._digit), lex._idStartNode, lex._numLink, lex._idBegCode, lex._idEndCode, 0])
            PrintWordArray(f, "lextree_node_%s" % name, data)
            size += 2 * len(data)

            off_lextree_node = offset
            offset = offset + DumpWordArray(le, be, data)

        struct_array = []
        
        lines = []
        lines.append("/* shengmu number */      %d" % len(self._elem._shengmu))
        lines.append("/* yunmu number */        %d" % len(self._elem._yunmu))
        struct_array = [len(self._elem._shengmu), len(self._elem._yunmu)]
        
        if type(self._elem) is ZhuyinElement:
            lines.append("/* shengdiao number */    %d" % len(self._elem._shengdiao))
            struct_array.append(len(self._elem._shengdiao))
        else:
            lines.append("/* shengdiao number */    %d" % 0)
            struct_array.append(0)

        if self._codemap._keyboard != 'qwerty':
            lines.append("/* pinyin dic number */   %d" % len(self._digit_dic))
            lines.append("/* lextree node number */ %d" % len(self._lextree))
            struct_array.append(len(self._digit_dic))
            struct_array.append(len(self._lextree))
        else:
            lines.append("/* pinyin dic number */   %d" % 0)
            lines.append("/* lextree node number */ %d" % 0)
            struct_array.append(0)
            struct_array.append(0)

        lines.append("/* pinyin number */       %d" % len(pinyin_list))
        lines.append("")

        struct_array.append(len(pinyin_list))
        
        lines.append("/* shengmu table */       %s" % ("shengmu_%s" % name))
        lines.append("/* yunmu table */         %s" % ("yunmu_%s" % name))

        struct_array.append(off_shengmu)
        struct_array.append(off_yunmu)
        
        if type(self._elem) is ZhuyinElement:
            lines.append("/* shengdiao table */     %s" % ("shengdiao_%s" % name))
            struct_array.append(off_shengdiao)
        else:
            lines.append("/* shengdiao table */     %s" % "0")
            struct_array.append(0)
            
        lines.append("/* pinyin table */        %s" % ("pinyin_%s" % name))
        struct_array.append(off_pinyin)
        
        if self._codemap._keyboard != 'qwerty':
            lines.append("/* pinyin dic table */    (const PinyinDic*)%s" % ("pinyin_dic_%s" % name))
            lines.append("/* lextree node table */  (const LextreeNode*)%s" % ("lextree_node_%s" % name))

            struct_array.append(off_pinyin_dic)
            struct_array.append(off_lextree_node)
            
        else:
            lines.append("/* pinyin dic table */    %s" % "0")
            lines.append("/* lextree node table */  %s" % "0")

            struct_array.append(0)
            struct_array.append(0)
            
        lines.append("")            
        return lines, size, offset, struct_array
        
    def BuildDigitLextree(self):

        digit_dic = self.CreateDic()
##        self.DumpDic(digit_dic)

        root = DigitTree(u'\u0000')
        for i, dic in enumerate(digit_dic):
            root.Add(dic._digits, i)

        node_num = root.Count(0) + 1
        
        lextree = []
        for i in range(node_num):
            lextree.append(self.LextreeNode())

        self.LextreeNode._idNext = 1
        self.StoreTree(lextree, root, 0, 0)

        return digit_dic, lextree
    
    def StoreTree(self, lextree, tree, idx, idParent):
        lex = lextree[idx]

        lex._digit = tree._digit
        lex._idBegCode = tree._codemask[0]
        lex._idEndCode = tree._codemask[-1] + 1

        lex._numLink = len(tree._child)
        if len(tree._child) == 0:
            lex._idStartNode = idParent
        else:
            lex._idStartNode = self.LextreeNode._idNext

        self.LextreeNode._idNext += lex._numLink

        for i in range(0, lex._numLink):
            self.StoreTree(lextree, tree._child[i], lex._idStartNode + i, idx)

        return

    def DumpDic(self, digit_dic):
        print 'Dump digit dictionary to DigitDicDump.txt...', 
        f = open('DigitDicDump.txt', 'w')
        
        for i, dic in enumerate(digit_dic):

            #print i, "\t", dic._digits, "\t",
            sm_index = dic._code & 0x001F
            ym_index = dic._code >> 5

            if sm_index:
                shengmu = self._elem._shengmu[sm_index - 1]
            else:
                shengmu = ''
            if ym_index:
                yunmu = self._elem._yunmu[ym_index - 1]
            else:
                yunmu = ''

            line = "%d: \t%s\t%s\n" % (i, dic._digits, shengmu + yunmu)
            f.write(line)
            #print shengmu + yunmu

        f.close()
        print 'Done!'
        
        return
        
    def CreateDic(self):
        fuzzy = Fuzzy()
        pinyin_list = sorted((self._codemap._valid_pinyin | set(self._elem._shengmu)))

        digit_dic = []

        for pinyin in pinyin_list:
            sm_index, shengmu, ym_index, yunmu = self._elem.SplitePinyin(pinyin)

            digits = self.Pinyin2Digit(pinyin)
            code = sm_index | (ym_index << 5)
            mask = 0
            digit_dic.append(self.DigitDic(digits, code, mask))      # append dic

            shengmu_fz, shengmu_mask = fuzzy.FindFuzzy(shengmu, True)
            yunmu_fz, yunmu_mask = fuzzy.FindFuzzy(yunmu, False)
            yunmu_mask = (yunmu_mask << 8)

            if shengmu_mask:
                code = self._elem.Pinyin2Code(shengmu_fz + yunmu, False)
                dic = self.DigitDic(digits, code, shengmu_mask)
                digit_dic.append(dic)                   # append shengmu_fz dic
            if yunmu_mask:
                code = self._elem.Pinyin2Code(shengmu + yunmu_fz, False)
                dic = self.DigitDic(digits, code, yunmu_mask)
                digit_dic.append(dic)                   # append yunmu_fz to dic
            if shengmu_mask and yunmu_mask:
                code = self._elem.Pinyin2Code(shengmu_fz + yunmu_fz, False)
                dic = self.DigitDic(digits, code, shengmu_mask | yunmu_mask)
                digit_dic.append(dic)   # append shengmu_fz and yunmu_fz to dic

        digit_dic.sort(self.DicCompare)

        return digit_dic

    def BuildPinyinDigitMap(self):
        if self._keyboard == 'digit' or self._keyboard == 'qwerty':
            return dict(zip(u'abcdefghijklmnopqrstuvwxyz', u'22233344455566677778889999'))
        elif self._keyboard == 'suretype':
            digit = [u'\x3a', u'1', u'2', u'3', u'\x3d',
                     u'\x3b', u'4', u'5', u'6', u'\x3e',
                     u'\x3c', u'7', u'8', u'9']

            alphabeta = [u'wq', u'er', u'ty', u'ui', u'op',
                         u'as', u'df', u'gh', u'jk', u'l',
                         u'zx', u'cv', u'bn', u'm']

            temp_dict = dict(zip(alphabeta, digit))
            alpha2digit = dict()
            for key in temp_dict.keys():
                for ch in key:
                    alpha2digit[ch] = temp_dict[key]

            return alpha2digit
        else:
            return dict()

    def Pinyin2Digit(self, pinyin):
        digit = [self._pinyin2digit[item] for item in pinyin]

        return ''.join(digit) + u'\u0000'

    class DigitDic:
        def __init__(self, digits, code, mask):
            self._digits = digits
            self._code = code
            self._mask = mask

    class LextreeNode:
        def __init__(self):
            self._idStartNode = 0
            self._numLink = 0
            self._idBegCode = 0
            self._idEndCode = 0
            self._digit = 0
            

    def DicCompare(self, left, right):
        if left._digits < right._digits: return -1
        if left._digits > right._digits: return 1

        if left._mask == 0 and right._mask != 0: return -1
        if left._mask != 0 and right._mask == 0: return 1

        id_left = left._code & 0x1F
        id_right = right._code & 0x1F
        if id_left == 0 : id_left = 50
        if id_right == 0 : id_right = 50
        if id_left > id_right : return -1
        if id_left < id_right : return 1
        
        return (left._code >> 5) - (right._code >> 5)

class DigitLextree_Compact(DigitLextree):
    def __init__(self, codemap, syslextree):
        self._codemap = codemap
        self._elem = codemap._elem
        self._syslextree = syslextree
        self._keyboard = codemap._keyboard
        self._pinyin2digit = self.BuildPinyinDigitMap()

    def PrintZhuyin(self, f, name, offset, le, be):
        size = 0
        data = []
        for i, shengmu in enumerate(self._elem._shengmu):
            p = [0 for i in range(2)]

            p[:len(shengmu)] = [ord(ch) for ch in shengmu]
            data.extend(p)
        PrintWordArray(f, "shengmu_%s" % name, data)
        size += 2 * len(data)

        off_shengmu = offset
        offset = offset + DumpWordArray(le, be, data)
        
        data = []
        for yunmu in self._elem._yunmu:
            p = [0 for i in range(3)]

            p[:len(yunmu)] = [ord(ch) for ch in yunmu]
            data.extend(p)
        PrintWordArray(f, "yunmu_%s" % name, data)
        size += 2 * len(data)

        off_yunmu = offset
        offset = offset + DumpWordArray(le, be, data)

        data = []
        for shengdiao in self._elem._shengdiao:
            p = [0 for i in range(2)]
            p[:len(shengdiao)] = [ord(ch) for ch in shengdiao]
            data.extend(p)
        PrintWordArray(f, "shengdiao_%s" % name, data)
        size += 2 * len(data)

        off_shengdiao = offset
        offset = offset + DumpWordArray(le, be, data)

        data = []
        pinyin_list = [self._elem.Pinyin2Zhuyin(item) for item in self._codemap._valid_pinyin]
        pinyin_list.extend(self._elem._shengmu)
        pinyin_list = sorted(pinyin_list)

        for pinyin in pinyin_list:
            p = [0 for i in range(4)]
            p[:len(pinyin)] = [ord(ch) for ch in pinyin]
            data.extend(p)
        PrintWordArray(f, "pinyin_%s" % name, data)
        size += 2 * len(data)

        off_pinyin = offset
        offset = offset + DumpWordArray(le, be, data)

        lines = []
        lines.append("/* shengmu number */      %d" % len(self._elem._shengmu))
        lines.append("/* yunmu number */        %d" % len(self._elem._yunmu))
        lines.append("/* shengdiao number */    %d" % len(self._elem._shengdiao))

        lines.append("/* pinyin dic number */   %d" % 0)
        lines.append("/* lextree node number */ %d" % 0)

        lines.append("/* pinyin number */       %d" % len(pinyin_list))
        lines.append("")

        lines.append("/* shengmu table */       %s" % ("shengmu_%s" % name))
        lines.append("/* yunmu table */         %s" % ("yunmu_%s" % name))
        lines.append("/* shengdiao table */     %s" % ("shengdiao_%s" % name))
        lines.append("/* pinyin table */        %s" % ("pinyin_%s" % name))
        
        lines.append("/* pinyin dic table */    %s" % "0")
        lines.append("/* lextree node table */  %s" % "0")

        lines.append("")

        struct_array = [len(self._elem._shengmu), len(self._elem._yunmu), len(self._elem._shengdiao),
                        0, 0, len(pinyin_list), off_shengmu, off_yunmu, off_shengdiao, off_pinyin,\
                        0, 0]
        return lines, size, offset, struct_array
        
    def Print(self, f, name, offset, le, be):
        if type(self._elem) is ZhuyinElement:
            return self.PrintZhuyin(f, name, offset, le, be)
        
        size = 0
        pinyin_list = sorted(list(set(self._syslextree._zipin_py) | set(self._elem._shengmu)))

        digit2pinyin = [dict() for i in range(6)]
        for pinyin in pinyin_list:
            digit = self.Pinyin2Digit(pinyin)
            d2y = digit2pinyin[len(pinyin) - 1]

            d2y.setdefault(digit, []).append(pinyin)
            
        data = []
        for shengmu in self._elem._shengmu:
            p = [0 for i in range(3)]
            p[:len(shengmu)] = [ord(ch) for ch in shengmu]
            data.extend(p)
        PrintByteArray(f, "shengmu_%s" % name, data)
        size += len(data)

        off_shengmu = offset
        offset = offset + DumpByteArray(le, be, data)
        
        data = []
        for yunmu in self._elem._yunmu:
            p = [0 for i in range(5)]
            p[:len(yunmu)] = [ord(ch) for ch in yunmu]
            data.extend(p)
        PrintByteArray(f, "yunmu_%s" % name, data)
        size += len(data)

        off_yunmu = offset
        offset = offset + DumpByteArray(le, be, data)

        data = []
        for d2y in digit2pinyin:
            data.append(sum([len(d2y[key]) for key in d2y.keys()]))

            for digit in sorted(d2y.keys()):
                for pinyin in d2y[digit]:
                    p = [0 for i in range(len(pinyin)+1)]
                    p[:len(pinyin)] = [ord(ch) for ch in pinyin]
                    data.extend(p)
        PrintByteArray(f, "pinyin_%s" % name, data)
        size += len(data)

        off_pinyin = offset
        offset = offset + DumpByteArray(le, be, data)
        
        pinyin_table_len = len(data)

        lines = []
        lines.append("/* shengmu number */      %d" % len(self._elem._shengmu))
        lines.append("/* yunmu number */        %d" % len(self._elem._yunmu))
        lines.append("/* shengdiao number */    %d" % 0)

        lines.append("/* pinyin dic number */   %d" % 0)
        lines.append("/* lextree node number */ %d" % 0)

        lines.append("/* pinyin number */       %d" % pinyin_table_len)
        lines.append("")

        lines.append("/* shengmu table */       %s" % ("(const unsigned short*)shengmu_%s" % name))
        lines.append("/* yunmu table */         %s" % ("(const unsigned short*)yunmu_%s" % name))
        lines.append("/* shengdiao table */     %s" % 0)
        lines.append("/* pinyin table */        %s" % ("(const unsigned short*)pinyin_%s" % name))
        
        lines.append("/* pinyin dic table */    %s" % "0")
        lines.append("/* lextree node table */  %s" % "0")
        lines.append("")

        struct_array = [len(self._elem._shengmu), len(self._elem._yunmu), 0, 0, 0, pinyin_table_len,\
                        off_shengmu, off_yunmu, 0, off_pinyin, 0, 0]
        
        return lines, size, offset, struct_array
        
        
                 
