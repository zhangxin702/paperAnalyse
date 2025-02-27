import PyPDF2
import ollama
from ollama import Client as Client1

from arxiv import Client, Search, SortCriterion
from urllib.error import HTTPError
import requests
import argparse

import os 
import datetime
# 跳转到指定的文件夹
from datetime import datetime

import time
   

# 创建文件夹和子目录 文件夹的名字为当天日期
def create_folder():
    # 获取精确到毫秒的时间
    now = datetime.now()
    # 格式化为 年月日_时分秒毫秒
    time_str = now.strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]  # 截取毫秒前三位
    folder_name = f"{time_str}"

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    # 创建子目录
    subfolder_names = ["pdf", "sources","analyze"]


    for subfolder_name in subfolder_names:
        if not os.path.exists(folder_name + "/" + subfolder_name):
            os.makedirs(folder_name + "/" + subfolder_name)
    return folder_name

def safe_download(result):
    # 强制校验PDF链接
    if not result.pdf_url:
        raise ValueError("无效的PDF链接")
    
    # 下载PDF
    title = result.title
    filename = result.title + ".pdf"
    pdf_path = result.download_pdf("./pdf", filename)
    
    # 构造源码链接
    source_url = result.pdf_url.replace("/pdf/", "/src/")
    try:
        # 尝试HEAD请求验证源码存在性
        resp = requests.head(source_url)
        
        if resp.status_code == 200:
            result.download_source("./sources")
    except HTTPError as e:
        print(f"源码不存在: {e}")
    return filename



# 下载pdf文件，输入关键字和下载数量
def download_pdf(keyword, num):
    search = Search(
    query=keyword,  
    max_results=num,                       # 限制获取10篇
    # sort_by=SortCriterion.SubmittedDate    # 按提交日期排序
)
    # 2. 初始化客户端（使用默认参数）
    client = Client(
    page_size=num,          # 每次请求获取50条
    delay_seconds=3.5      # 比官方要求的3秒稍长更安全
)
    filenames = []
    for result in client.results(search):
        try:
            filenme = safe_download(result)
            filenames.append(filenme)
        except Exception as e:
            print(f"搜索失败: {str(e)}")

   
 
            

    with open("filename.txt", "w") as f:
        for filename in filenames:
            filename = filename.split(".")[0]
            f.write(filename + "\n")
    return filenames
        


def read_pdf_text(filename):
  with open(filename, 'rb') as file:
    # 创建一个PDF阅读器对象
    reader = PyPDF2.PdfReader(file)
    res = []
    # 遍历PDF中的每一页
    for page_num in range(len(reader.pages)):
        text = reader.pages[page_num].extract_text()
        # 添加字符清理逻辑
        cleaned_text = text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
        res.append(cleaned_text)
    return ''.join(res)

  

def read_prompt_content():
    prompt_content = open(prompt_content, encoding='utf-8').read()
    return prompt_content


def extract_pdf(filename, prompt_content):
    pdf = read_pdf_text(filename=filename)

    response = client.chat(model='deepseek-r1:70b',
                messages = [
                           {'role': 'system', 'content': prompt_content},
                            {'role': 'user', 'content': "请提取以下关键信息：1,摘要：论文摘要的全文，用 2-3 句话简洁地总结摘要。2,突出重点论文的创新点和解决的问题。"},
                            {'role': 'assistant', 'content': "好的，我已经理解了任务要求，请提供论文的文本内容。"},

                           
                           {'role': 'user', 'content':pdf},

 
                           
                       ],
                
                )

    


    return response['message']['content']


def extract_pdfs(filenames, prompt_content):
    
    

    for filename in filenames:
        filepath = "./pdf/"+ filename
        res = extract_pdf(filepath, prompt_content)
        with open("./analyze/"+filename + ".txt", "w") as f:
            f.write(res)
            print("解析完成：" + filename)
    print("解析完成！")


    







if __name__ == "__main__":


    # 运行脚本时，输出提示信息
    print("开始下载arXiv论文...")
    begin = time.time()

        # 添加命令行参数解析
    parser = argparse.ArgumentParser(description='arXiv论文下载和解析工具')
    parser.add_argument('--keyword', type=str, default='machine learning', 
                       help='搜索关键词，默认为"machine learning"')
    parser.add_argument('--num', type=int, default=5,
                       help='下载论文数量，默认为5')
    parser.add_argument('--path', type=str, default='/home/zhangxinying/vscode/test',)
    args = parser.parse_args()



    client = Client1(
        host='http://192.168.99.106:11434',
        headers={'x-some-header': 'some-value'}
    )

    path = args.path
    os.chdir(path)
    foldername = create_folder()
    # 进入到创建的文件夹中
    os.chdir(foldername)
    # 下载pdf文件……
    filenames = download_pdf(args.keyword, args.num)
    print("正在解析……")
    # 读取prompt.txt中的内容
    prompt_content = open("/home/zhangxinying/vscode/test/arxive/code/scientific_papers_prompt.txt", encoding='utf-8').read()
    # 提取pdf文件
    extract_pdfs(filenames, prompt_content)



    end = time.time()
    folderpath = os.getcwd()
    print("下载完成，文件保存在：" + folderpath)
    print("耗时：" + str(end - begin) + "秒")



    
    
