import time
from ebooklib import epub
import requests
import tqdm
import re
import os


# 获得小说
def get_novel(bk_id, write_type=1):
    url = "https://www.bqg70.com/book/" + str(bk_id)
    text = requests.get(url=url).text
    length = len(re.findall("<dd><a href =\"/book/" + str(bk_id) + "/.*</dd>", text))
    novel_name = re.findall(">.*</h1>", text)[0][1:-5]
    author_name = re.findall("作者[：:]\\w*", text)[0][3:]
    print(f"本小说为《{novel_name}》,总共有{length}个章节")
    if write_type == 1:
        print("开始下载txt多文件格式")
        store_content(novel_name, url, length, write_type)
    elif write_type == 2:
        print("开始下载txt单文件格式")
        store_content(novel_name, url, length, write_type)
    elif write_type == 3:
        print("开始下载epub格式")
        # 创建一个EPUB电子书对象
        book = epub.EpubBook()
        # 设置电子书的元数据
        book.set_identifier(novel_name)
        book.set_title(novel_name)
        book.set_language('zh')
        book.add_author(author_name)
        spine = store_content(novel_name, url, length, write_type, book=book)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = spine
        epub.write_epub("《" + novel_name + "》.epub", book)
        print('EPUB文件生成成功！')
    else:
        print("由于选择的类型并不是1~3，所以不下载小说")


# 获得内容与标题
def get_result_and_title(url):
    text = requests.get(url=url).text
    pattern = ">.*<br ?/?>"
    pattern2 = ">.*</h1>"
    content = re.findall(pattern, text)[0]
    title = re.findall(pattern2, text)[0]
    li = content.replace("<br /><br />", "\n")[1:].splitlines()[:-2]
    epub_result = "<br/>".join(li)
    result = "\n".join(li)
    title = title[1:-5]
    return [result, title, epub_result]


# 写入内容
def store_content(package_name, url, length, t, book=None):
    end = length + 1
    i = 1
    spine = []
    # v1.0.2
    tqdm_tqdm = tqdm.tqdm(range(end - i), desc="下载进度", colour="#f0f0f0", unit="章", ncols=60)
    while i < end:
        url_ = url + "/" + str(i) + ".html"
        try:
            li = get_result_and_title(url_)
        except:
            continue
        result = li[0]
        title = li[1]
        # v1.0.1 更新，去除/:*?"<>|\，替换成其他可以显示的字符
        title = replace_special_character(title)
        epub_result = li[2]
        # print(f"当前为第{i}章")
        if t == 1:
            filename = package_name + "/" + title + ".txt"
            write_file(filename, result, title)
        elif t == 2:
            write_in_one_file("《" + package_name + "》.txt", result, title)
        elif t == 3:
            chapter = epub.EpubHtml(title=title, file_name=title + '.xhtml',
                                    content="<h1>" + title + "</h1>" + epub_result)
            book.add_item(chapter)
            book.toc.append(chapter)
            spine.append(chapter)
        tqdm_tqdm.update()
        i += 1
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
    folder = os.path.dirname(filename)
    if not os.path.exists(folder):
        os.makedirs(folder)
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
                type_id = int(
                    input("选择类型：1为下载多个txt文件，2为下载单个txt文件，3为epub格式文件，-1为退出本级菜单\n"))
                if type_id == -1:
                    continue
                get_novel(book_id, write_type=type_id)
            elif choice == 2:
                break
        except Exception as exception:
            print(exception)
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
