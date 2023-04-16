from predict import predict_no_ui
from toolbox import CatchException, report_execption, write_results_to_file, predict_no_ui_but_counting_down
import re
import unicodedata

from newspaper import Article
fast_debug = False

def html_to_text(filename):
    """
    解析html文件内容
    返回标题，正文
    """
    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()

    #tree = HTMLParser(html)
    #title = tree.css_first('title').text()
    #print(html)

    article = Article('', language="zh")
    article.download(input_html=html)
    article.parse()
    #print ('title is ' + article.title)
    #print ('content is ' + article.text)

    return article.title, article.text

def 解析html(file_manifest, project_folder, top_p, temperature, chatbot, history, systemPromptTxt):
    import time, glob, os, fitz
    print('begin analysis on:', file_manifest)
    for index, fp in enumerate(file_manifest):

        title, content = html_to_text(fp)

        ### 第一个问题先进行简短的分析 ###
        #prefix = "接下来请你逐个分析下面的新闻，概括其内容"
        i_say = f'请对下面的新闻用中文做一个非常简短的概述，新闻标题为 ```{title}```，新闻内容是 ```{content}```'
        i_say_show_user = "请分析《" + title + "》文章内容" + f'[{index+1}/{len(file_manifest)}]'
        chatbot.append((i_say_show_user, "[Local Message] waiting gpt response."))
        print('[1] yield chatbot, history')
        yield chatbot, history, '正常'

        if not fast_debug: 
            msg = '正常'
            # ** gpt request **
            gpt_say = yield from predict_no_ui_but_counting_down(i_say, i_say_show_user, chatbot, top_p, temperature, history=[])   # 带超时倒计时

            chatbot[-1] = (i_say_show_user, gpt_say)
            history.append(i_say_show_user); history.append(gpt_say)
            yield chatbot, history, msg
            if not fast_debug: time.sleep(2)

        ### 第二个问题进行正负面分析 ###
        i_say = f'现在有一段新闻，\
            请根据新闻内容生成一个两列的表格，不用给出理由和解释，表格左边是新闻中主要出现的企业名称，表头为\"企业\"，\
                对于表格右边，如果该新闻能提升公众对企业的投资信心，则填入“正面”，\
                    如果会降低公众对企业的投资信心，则填入“负面”，如果不确定，填入“未知”，表头为\"评价\"\
                    新闻标题为 ```{title}```，新闻内容是 ```{content}```'
        i_say_show_user = "请进行分析"
        chatbot.append((i_say_show_user, "[Local Message] waiting gpt response."))
        print('[1] yield chatbot, history')
        yield chatbot, history, '正常'

        if not fast_debug: 
            msg = '正常'
            # ** gpt request **
            gpt_say = yield from predict_no_ui_but_counting_down(i_say, i_say_show_user, chatbot, top_p, temperature, history=[])   # 带超时倒计时

            chatbot[-1] = (i_say_show_user, gpt_say)
            history.append(i_say_show_user); history.append(gpt_say)
            yield chatbot, history, msg
            if not fast_debug: time.sleep(2)

    #all_file = ', '.join([os.path.relpath(fp, project_folder) for index, fp in enumerate(file_manifest)])
    #i_say = f'根据以上你自己的分析，对全文进行概括，用学术性语言写一段中文摘要，然后再写一段英文摘要（包括{all_file}）。'
    #chatbot.append((i_say, "[Local Message] waiting gpt response."))
    #yield chatbot, history, '正常'

    if not fast_debug: 
        msg = '正常'
        # ** gpt request **
        #gpt_say = yield from predict_no_ui_but_counting_down(i_say, i_say, chatbot, top_p, temperature, history=history)   # 带超时倒计时

        #chatbot[-1] = (i_say, gpt_say)
        #history.append(i_say); history.append(gpt_say)
        #yield chatbot, history, msg
        res = write_results_to_file(history)
        #chatbot.append(("完成了吗？", res))
        #yield chatbot, history, msg


@CatchException
def 分析news文件(txt, top_p, temperature, chatbot, history, systemPromptTxt, WEB_PORT):
    import glob, os

    # 基本信息：功能、贡献者
    #chatbot.append([
    #    "函数插件功能？",
    #    "批量总结PDF文档。函数插件贡献者: ValeriaWong，Eralien"])
    #yield chatbot, history, '正常'

    # 尝试导入依赖，如果缺少依赖，则给出安装建议
    try:
        import fitz
    except:
        report_execption(chatbot, history, 
            a = f"解析项目: {txt}", 
            b = f"导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade pymupdf```。")
        yield chatbot, history, '正常'
        return

    # 清空历史，以免输入溢出
    history = []

    # 检测输入参数，如没有给定输入参数，直接退出
    #if os.path.exists(txt):
    #    project_folder = txt
    #else:
    #    if txt == "": txt = '空空如也的输入栏'
    #    report_execption(chatbot, history, a = f"解析项目: {txt}", b = f"找不到本地项目或无权访问: {txt}")
    #    yield chatbot, history, '正常'
    #    return

    # 搜索需要处理的文件清单
    project_folder = 'news'
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.html', recursive=True)] # + \
                    # [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)] + \
                    # [f for f in glob.glob(f'{project_folder}/**/*.cpp', recursive=True)] + \
                    # [f for f in glob.glob(f'{project_folder}/**/*.c', recursive=True)]
    
    # 如果没找到任何文件
    if len(file_manifest) == 0:
        report_execption(chatbot, history, a = f"解析项目: {txt}", b = f"找不到任何.html文件: {txt}")
        yield chatbot, history, '正常'
        return

    # 开始正式执行任务
    yield from 解析html(file_manifest, project_folder, top_p, temperature, chatbot, history, systemPromptTxt)
