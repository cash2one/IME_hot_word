## IME_hot_word
mdev:/home/mdev/hank/update_hot_words.sh）(百度词频爬虫分布在s1，故晚上8点开始至第二天10点之间，s1不能部署百度相关的爬虫)    
	   svn版本控制:svn://srv2/droid_ime/branches/chocolate_ime/script/gen_update_words/gen_new_hot_words.py    
	   1、判断s1上词频抓取进程是否仍在执行，若存在词频进程则跳过所有步骤，将上次上次的update.txt文件转换为bin文件并上传    
	   2、若s1上没有词频抓取进程，则在mdev上集合搜狗、百度、新浪热词到一个文件（combine_hot_words.txt），scp该文件到s1上    
	   3、执行词频抓取操作(cd /home/gaius/wanghuafeng/hot_word_freq; python baidu_freq_spider.py -f     combine_hot_words.txt')，并生成词频文件（combine_hot_words.freq）    
	   4、词频抓取任务结束，将新生成的词频文件（combine_hot_words.freq）scp到mdev    
	   5、若步骤4中scp操作执行成功，且词频抓取失败数量在1000以内，则将利用txt,freq文件生成words, pinyin, freq格式倒序排列的文件（words_pinyin_freq.txt）    
	   6、筛选出倒序排列文件（words_pinyin_freq.txt）中最多7200个高频词，添加本地手工加入的热词     
	   7、若此时高频及本地词加一起数字在5000,8000之间则写入本地（update.txt），否则上传上次生成的update.txt    
	热词数据源:    
	1、百度风云榜爬虫:svn://srv2/droid_ime/branches/chocolate_ime/script/tools/CrawlHotWord    
	2、新浪风云榜爬虫:（新浪风云榜改版升级中，现没有相关网页数据。待完成）    
	3、搜狗细胞词库的下载与解析爬虫:svn://srv2/droid_ime/branches/chocolate_ime/script/gen_update_words/gen_hot_words/sougou_cell_words.py    
