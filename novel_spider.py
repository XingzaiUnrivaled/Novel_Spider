import threading
import traceback
from ebooklib import epub
import requests
import tqdm
import re
import os

# 多线程个数（速度倍数，默认为十倍）
thread_count_global = 10
# 可以修改为当前有用的url
global_url = "www.bqg7777.xyz"

# 存储章节内容初始化为字典，使得可以使用关键字当下标存储
chapters = {}
prefix_url = "https://"
api_url = "https://apibi.cc/api"
tqdm_tqdm: tqdm.tqdm
# 填一个头
header = {
    "Accept": "*/*",
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 "
        "Safari/537.36"
}


# v1.0.4 加入多线程
class SpiderThread(threading.Thread):
    """线程类，根据线程数为步长进行跳跃增长"""

    def __init__(self, bk_id, end, package_name, choice, thread_id, count):
        super().__init__()
        self.bk_id = bk_id
        self.end = end
        self.package_name = package_name
        self.t = choice
        self.thread_id = thread_id
        self.thread_count = count

    def run(self):
        global chapters
        global tqdm_tqdm
        for i in range(self.thread_id, self.end, self.thread_count):
            content_info = get_result_and_title(bk_id=self.bk_id, chapter_id=i)
            result = content_info['txt']
            title = content_info['chaptername']
            # v1.0.1 更新，去除/:*?"<>|\，替换成其他可以显示的字符
            title_replace = replace_special_character(title)
            # v1.0.3 更新路径
            if self.t == "1":
                filename = "multi txt/" + self.package_name + "/" + title + ".txt"
                write_file(filename, result, title_replace)
            else:
                # print(abc)
                chapters[i] = content_info
            # print(f"当前为第{i}章")
            tqdm_tqdm.update()


def get_epub_format(chapter):
    return str(chapter['txt']).replace("\n", "<br>")


def get_book_list(bk_id):
    """获得章节列表"""
    url = api_url + "/booklist"
    booklist = requests.get(url=url, params={"id": bk_id}, headers=header).json()
    return booklist['list']


def get_novel(bk_id, bk, write_type="1"):
    """获取小说，根据写入方式进行写入"""
    get_book_list(bk_id)
    novel_name = bk["title"]
    length = int(bk["lastchapterid"])
    author_name = bk["author"]
    cover = requests.get(url=prefix_url + global_url + f"/bookimg/{int(bk_id) // 1000}/{bk_id}.jpg").content

    if write_type == "1":
        os.makedirs("multi txt", exist_ok=True)
        print("开始下载txt多文件格式")
        store_content(bk_id, novel_name, length, write_type, thread_count=thread_count_global)
    elif write_type == "2":
        os.makedirs("single txt", exist_ok=True)
        print("开始下载txt单文件格式")
        store_content(bk_id, novel_name, length, write_type, thread_count=thread_count_global)
    elif write_type == "3":
        print("开始下载epub格式")
        os.makedirs("epub", exist_ok=True)
        # 创建一个EPUB电子书对象
        book = epub.EpubBook()
        # 设置电子书的元数据
        book.set_identifier(novel_name)
        book.set_title(novel_name)
        book.set_language('zh')
        book.add_author(author_name)
        book.set_cover(file_name="cover.jpg", content=cover)
        spine = store_content(bk_id, novel_name, length, write_type, book=book, thread_count=thread_count_global)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = spine
        epub.write_epub("epub/《" + novel_name + "》.epub", book)
        print('EPUB文件生成成功！')
    else:
        print("由于选择的类型并不是1~3，所以不下载小说")


def get_book_name(bk_id):
    """获取书名"""
    url = api_url + "/book"
    book = requests.get(url=url, headers=header, params={"id": bk_id}).json()
    print(f"本小说为《{book['title']}》,总共有{book['lastchapterid']}个章节")
    return book


# 获得内容与标题
def get_result_and_title(bk_id, chapter_id):
    """获取内容"""
    while True:
        try:
            chapter_info = requests.get(url=api_url + "/chapter", headers=header,
                                        params={"id": bk_id, "chapterid": chapter_id}).json()
            return chapter_info
        except Exception as e:
            print("无视当前错误:", e)
            continue


def store_content(bk_id, package_name, length, t, book=None, thread_count=10):
    end = length + 1
    global tqdm_tqdm
    spine = []
    # v1.0.2
    tqdm_tqdm = None
    tqdm_tqdm = tqdm.tqdm(range(length), desc="下载进度", colour="#f0f0f0", unit="章", ncols=60)

    thread_collection = []
    for j in range(thread_count):
        thread_collection.append(SpiderThread(bk_id, end, package_name, t, j + 1, thread_count))
    for j in thread_collection:
        j.start()
    for j in thread_collection:
        j.join()
    tqdm_tqdm.close()
    for n in range(1, end):
        content_info = chapters[n]
        result = content_info['txt']
        title = content_info['chaptername']
        epub_result = get_epub_format(content_info)
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
    """替换特殊字符方法 特殊字符在多文件写入的时候可能会有异常"""
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
    """单文件写入"""
    with open(filename, 'at', encoding='utf8') as f:
        f.write("\t\t\t\t\t\t" + title + "\n")
        f.write(content + "\n")


def write_file(filename, content, title):
    """多文件写入"""
    with open(filename, "wt", encoding='utf8') as f:
        f.write(title + "\n\n")
        f.write(content)


# v1.0.1把主方法内部封装成main函数，然后让程序运行main()
def main():
    """主函数调用"""
    global global_url
    print("郑重声明，此项目仅供学习、研究，请勿用于商业用途，请勿用于非法用途")
    while True:
        try:
            choice = input("输入1进行书本下载\n输入2退出\n").strip()
            if choice == "1":
                print(f"请确认当前url（链接）是否正确 {global_url}")
                print("不正确请按1，正确请按2")
                url_id = input("请输入链接确认数字：").strip()
                if url_id == "1":
                    global_url = input("请输入正确的url：").strip()
                elif url_id == "2":
                    pass
                else:
                    print("请输入正确的数字")
                    continue
                book_id = input("输入id号\n").strip()
                if not book_id.isnumeric():
                    print("id号是数字，请输入数字")
                    continue
                # v1.0.4 新增输入id后查询书本和章节数量
                book = get_book_name(book_id)
                type_id = input(
                    "选择类型：1为下载多个txt文件，2为下载单个txt文件，3为epub格式文件，-1为退出本级菜单\n").strip()
                if type_id == "-1":
                    continue
                if type_id not in ["1", "2", "3"]:
                    print("请输入正确的数字")
                    continue
                get_novel(bk_id=book_id, bk=book, write_type=type_id)
            elif choice == "2":
                break
            else:
                print("请输入正确的数字")
        except Exception as e:
            traceback.print_exc()
            print(e)
            print("上述为报错信息请联系作者")
    print("退出程序")


if __name__ == '__main__':
    main()
