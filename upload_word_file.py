from build_update import Build_Update
import sys
import os
import subprocess
import re
import random
import commands

if __name__ == '__main__':
    THIS_PATH = os.getcwd()
else:
    THIS_PATH = os.path.dirname(__file__)

if THIS_PATH != os.getcwd():
    raise ValueError('Script must be launched under %s' % THIS_PATH)
    
def find_path(path):
    ''' search from current dir, parent dir, till top'''    
    
    def get_parent(p):
        if not os.path.sep in p or os.path.ismount(p):
            return None
        return os.path.split(p)[0]

    search_path = THIS_PATH
    
    while search_path:
        expect_path = os.path.join(search_path, path)
        if os.path.isdir(expect_path):
            break
        search_path = get_parent(search_path)

    if os.path.isdir(expect_path):
        return expect_path

    raise ValueError('Path %s not found!' % path)

SVN_PATH = find_path(r'svn')
#sys.path.append(find_path(r'tools\upload'))
sys.path.append(find_path(r'tools'+ os.path.sep + r'upload'))
REV_BASE = 20359
WORD_FILE = os.path.join(THIS_PATH, 'update.txt')
DESC_FILE = os.path.join(THIS_PATH, 'desc.txt')

import upload

def get_revision():    
    if sys.platform.lower().startswith('win'):
        exe = os.path.join(SVN_PATH, 'svn.exe')
        args = [exe, 'info', WORD_FILE, '--non-interactive']
        try:
            info = subprocess.check_output(args)
            revision = re.search('Last Changed Rev: (\d+)', info).group(1)
            return int(revision)
        except Exception, e:
            print e
            raise ValueError('Win: Get revision failed')
    else:
        out = os.popen('svn info |grep Revision')
        output = out.read()
        revision = re.search(r'(?P<revision>\d+)', output).group('revision')
        try:
            return int(revision)
        except Exception, e:
            print e
            raise ValueError('Linux: Get revision failed')
            
def get_version():
    return get_revision() - REV_BASE

DESC_TEMPLATE = u'增加了新词: %s'

def load_words(word_file):
    encoding = 'utf-16'
    data = open(word_file, 'rb').read().decode(encoding)
    words = []
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0] == ';':            
            continue
        words.append(line.split('\t', 1)[0])
    return words

def gen_desc():
    encoding = 'utf-16'
    sample_num = 10
    words = get_diff_words()
    if len(words) <= sample_num:
        samples = words
    else:
        samples = []
        while len(samples) < sample_num:
            word = random.choice(words)
            words.remove(word)
            samples.append(word)
    
    desc = DESC_TEMPLATE % ','.join(samples)
    open(DESC_FILE, 'wb').write(desc.encode(encoding))
    return desc

def get_diff_words():
    if sys.platform.lower().startswith('win'):
        exe = os.path.join(SVN_PATH, 'svn.exe')
        args = [exe, 'log', WORD_FILE, '--non-interactive']    
        info = subprocess.check_output(args)
        revs = re.findall('r(\d+) \|', info)
        if len(revs) < 2:
            return load_words(WORD_FILE)
    else:
        out = os.popen('svn log update.txt --non-interactive')
        output = out.read()
        revs = re.findall(r'(?P<revs>\d+) \|', output)
        if len(revs) < 2:
            return load_words(WORD_FILE)
    
    compare_rev = int(revs[1])
    compare_file = export_file(os.path.basename(WORD_FILE), compare_rev)
    words = load_words(WORD_FILE)
    old_words = load_words(compare_file)
    diff_words = set(words) - set(old_words)
    os.remove(compare_file)
    return list(diff_words)

def export_file(name, rev):
    if sys.platform.lower().startswith('win'):
        exe = os.path.join(SVN_PATH, 'svn.exe')
        exported_name = name + '.r%d' % rev
        args = [exe, 'export', '-r', str(rev), name, exported_name]
        info = subprocess.check_output(args)
        return exported_name
    else:
        exported_name = name + '.r%d' % rev
        cmd = 'svn export -r ' + str(rev) + ' ' + name + ' ' + exported_name
        try:
            #out = os.popen(cmd)
            status = commands.getstatusoutput(cmd)
            if status[0] != 0:
                raise ValueError('Command Failed!')
        except Exception, e:
            print "####", e
        return exported_name
        

def run():
    version = get_version()
    Build_Update(WORD_FILE, version)
    desc = gen_desc()
    le_filename = 'update_file_gbk_digit_le_%d.bin' % version
    be_filename = 'update_file_gbk_digit_be_%d.bin' % version
    upload.upload(le_filename, 'hotword', le_filename, desc, '')
    upload.upload(be_filename, 'hotword_be', be_filename, desc, '')

if __name__ == '__main__':
    run() 
    from  gen_hot_words import update_words_to_history
    update_words_to_history.write_src_to_des()  
