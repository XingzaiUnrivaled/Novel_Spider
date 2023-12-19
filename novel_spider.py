import threading
import time
from ebooklib import epub
import requests
import tqdm
import re
import os
import traceback

# 多线程个数（速度倍数，默认为十倍）
thread_count_global = 10


# v1.0.4 加入多线程
class SpiderThread(threading.Thread):
    def __init__(self, url, end, package_name, choice, thread_id, count):
        super().__init__()
        self.url = url
        self.end = end
        self.package_name = package_name
        self.t = choice
        self.thread_id = thread_id
        self.thread_count = count

    def run(self):
        global flag
        global chapters
        global tqdm_tqdm
        for i in range(self.thread_id, self.end, self.thread_count):
            url_ = self.url + "/" + str(i) + ".html"
            li = get_result_and_title(url_)
            result = li[0]
            title = li[1]
            # v1.0.1 更新，去除/:*?"<>|\，替换成其他可以显示的字符
            title_replace = replace_special_character(title)
            # v1.0.3 更新路径
            if self.t == 1:
                filename = "multi txt/" + self.package_name + "/" + title + ".txt"
                write_file(filename, result, title_replace)
            else:
                # print(abc)
                chapters[i] = li
            # print(f"当前为第{i}章")
            tqdm_tqdm.update()
        flag += 1


# 获得小说
def get_novel(bk_id, write_type=1):
    param_list = get_book_name(bk_id, False)
    novel_name = param_list["novel_name"]
    url = param_list["url"]
    length = param_list["length"]
    author_name = param_list["author_name"]

    if write_type == 1:
        os.makedirs("multi txt", exist_ok=True)
        print("开始下载txt多文件格式")
        store_content(novel_name, url, length, write_type, thread_count=thread_count_global)
    elif write_type == 2:
        os.makedirs("single txt", exist_ok=True)
        print("开始下载txt单文件格式")
        store_content(novel_name, url, length, write_type, thread_count=thread_count_global)
    elif write_type == 3:
        print("开始下载epub格式")
        os.makedirs("epub", exist_ok=True)
        # 创建一个EPUB电子书对象
        book = epub.EpubBook()
        # 设置电子书的元数据
        book.set_identifier(novel_name)
        book.set_title(novel_name)
        book.set_language('zh')
        book.add_author(author_name)
        spine = store_content(novel_name, url, length, write_type, book=book, thread_count=thread_count_global)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = spine
        epub.write_epub("epub/《" + novel_name + "》.epub", book)
        print('EPUB文件生成成功！')
    else:
        print("由于选择的类型并不是1~3，所以不下载小说")


# v1.0.4 获得书名
def get_book_name(bk_id, print_c=True):
    url = "https://www.bqg70.com/book/" + str(bk_id)
    text = requests.get(url=url).text
    length = len(re.findall("<dd><a href =\"/book/" + str(bk_id) + "/.*</dd>", text))
    novel_name = re.findall(">.*</h1>", text)[0][1:-5]
    author_name = re.findall("作者[：:]\\w*", text)[0][3:]

    if print_c:
        print(f"本小说为《{novel_name}》,总共有{length}个章节")
    return {"url": url, "length": length, "novel_name": novel_name, "author_name": author_name}


# 获得内容与标题
def get_result_and_title(url):
    while True:
        try:
            text = requests.get(url=url).text
            pattern = ">.*<br ?/?>"
            pattern2 = ">.*</h1>"
            content = re.findall(pattern, text)[0]
            title = re.findall(pattern2, text)[0]
            li = content.replace("<br /><br />", "\n")[1:].splitlines()[:-1]
            epub_result = "<br/>".join(li)
            result = "\n".join(li)
            title = title[1:-5]
            return [result, title, epub_result]
        except:
            # traceback.print_exc()
            continue


# 写入内容
def store_content(package_name, url, length, t, book=None, thread_count=10):
    end = length + 1
    global flag
    global chapters
    global tqdm_tqdm
    flag = 0
    spine = []
    chapters = {}
    # v1.0.2
    tqdm_tqdm = None
    tqdm_tqdm = tqdm.tqdm(range(length), desc="下载进度", colour="#f0f0f0", unit="章", ncols=60)

    thread_collection = []
    for j in range(thread_count):
        thread_collection.append(SpiderThread(url, end, package_name, t, j + 1, thread_count))
    for j in thread_collection:
        j.start()
    while flag != thread_count:
        time.sleep(5)
    for n in range(1, end):
        li = chapters[n]
        result = li[0]
        title = li[1]
        epub_result = li[2]
        if t == 2:
            write_in_one_file("single txt/《" + package_name + "》.txt", result, title)
        elif t == 3:
            chapter = epub.EpubHtml(title=title, file_name=title + '.xhtml',
                                    content="<h1>" + title + "</h1>" + epub_result)

            book.add_item(chapter)
            book.toc.append(chapter)
            spine.append(chapter)
    print()
    print(f"小说{package_name}下载完毕")
    return spine


# v1.0.1添加的方法
def replace_special_character(title):
    search = re.findall(r'[/:*?"<>|\\]', title)
    if len(search) > 0:
        title = title.replace("*", "星")
        title = title.replace("/", "丿")
        title = title.replace(":", "：")
        title = title.replace("?", "？")
        title = title.replace("<", "《")
        title = title.replace(">", "》")
        title = title.replace("\\", "、")
        title = title.replace("|", "丨")
        title = title.replace("\"", "'")
    return title


def write_in_one_file(filename, content, title):
    with open(filename, 'at', encoding='utf8') as f:
        f.write("\t\t\t\t\t\t" + title + "\n")
        f.write(content + "\n")


def write_file(filename, content, title):
    with open(filename, "wt", encoding='utf8') as f:
        f.write(title + "\n\n")
        f.write(content)


# v1.0.1把主方法内部封装成main函数，然后让程序运行main()
def main():
    while True:
        try:
            choice = int(input("输入1进行书本下载\n输入2退出\n"))

            if choice == 1:
                book_id = int(input("输入id号\n"))
                # v1.0.4 新增输入id后查询书本和章节数量
                get_book_name(book_id)
                type_id = int(
                    input("选择类型：1为下载多个txt文件，2为下载单个txt文件，3为epub格式文件，-1为退出本级菜单\n"))
                if type_id == -1:
                    continue
                get_novel(book_id, write_type=type_id)
            elif choice == 2:
                break
        except:
            traceback.print_exc()
            print("不许输入除数字之外的其他字母文字等等")
    print("退出程序，三秒后自动关闭")
    print("三")
    time.sleep(1)
    print("二")
    time.sleep(1)
    print("一")
    time.sleep(1)


if __name__ == '__main__':
    main()
