import argparse
import random
import sys
import urllib
import urllib.parse
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Style
from pyfiglet import Figlet
from urllib3.exceptions import InsecureRequestWarning

proxies = {
    "HTTP": "http://127.0.0.1:7890",
    "HTTPS": "http://127.0.0.1:7890"
}
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 "
    "Safari/537.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.0.3 "
    "Safari/602.4.8",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36",
    # 可根据需要添加更多的 User-Agent
]
init(autoreset=True)
'''
Note：
你这里使用clash可能会出现问题，解决方法同样适用命令行代理问题，在设置里找到 System Proxy开启 Specify Protocol 设置为On即可解决
推荐使用 香港、美国节点，如果出现没有结果也没有报错的情况，请切换节点，这是个有点玄学的问题...

'''


def print_logo():
    f = Figlet(font='slant')
    logo = f.renderText('GoogleCrawler')
    print(Fore.CYAN + logo)


# 忽略证书验证警告
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_random_user_agent(user_agents):
    return random.choice(user_agents)


def search_and_get_results(query, page_number=4):
    pagenum = 0
    results = []

    while pagenum < page_number * 10:
        url = f'https://google.com/search?q=' + urllib.parse.quote(query) + f'&start={pagenum}'
        print(url)
        headers = {
            'User-Agent': get_random_user_agent(user_agents)
        }
        try:
            response = requests.get(url, headers=headers)

            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            for g in soup.find_all('div'):
                link_element = g.find('a')
                if link_element:
                    try:
                        link = link_element['href']
                        if not link.startswith('/url?'):
                            continue
                        title = link_element.find('h3').get_text(strip=True)
                        if not title:
                            title = "title not match"
                        if link.startswith('/url?esrc='):
                            start_page_number = link.find('url=') + 4
                            target_link = urllib.parse.unquote(link[start_page_number:])
                            if title and target_link:
                                results.append((title, target_link,))
                    except Exception as e:
                        pass  # 处理 get_text异常
        except Exception as e:
            # print(e)
            print(f"[-] 页面访问失败请检查代理" + url)
            break

        pagenum += 10

    return results


def get_search_words(keyword):
    rule_dict = {
        "数据泄露": "{} intext:vpn OR 用户名 OR 密码 OR 帐号 OR 默认密码".format(keyword),
        "相关文件": "{} filetype:.doc OR .docx OR .xls OR .xlsx OR .ppt OR .pptx OR .odt OR .pdf OR .rtf OR .sxw OR .psw OR .csv".format(
            keyword),
        "文件泄露": "{} ext:.bkf OR .bkp OR .old OR .backup OR .bak OR .swp OR .rar OR .txt OR .zip OR .7z OR .sql OR .tar.gz OR .tgz OR .tar OR .conf OR .cnf OR .reg OR .inf OR .rdp OR .cfg OR .txt OR .ora OR .ini".format(
            keyword),
        "数据库文件泄露": "{} ext:.sql OR .dbf OR .mdb OR .db".format(keyword),
        "日志信息": "{} ext:.log".format(keyword),
        "报错页面": '{} intext:"sql syntax near" OR intext:"error" OR intext:"syntax error has occurred" OR intext:"incorrect syntax near" OR intext:"unexpected end of SQL command" OR intext:"Warning: mysql_connect()" OR intext:"Warning: mysql_query()" OR intext:"Warning: pg_connect()'.format(
            keyword),
        "SSO/VPN": "{} intext:统一认证 OR intext:vpn OR intext:webvpn OR intext:sslvpn".format(keyword),
        "网站功能": '{} intext:后台 OR intext:留言 OR intext:邮箱'.format(keyword)
    }

    return rule_dict


def process_data(search_word, all_results):
    filtered_links = []
    unique_list = {tuple(d.items()) for d in all_results}

    for item_tuple in unique_list:
        item_dict = dict(item_tuple)
        result_data = item_dict['result']
        link = result_data[1].split('&')[0]
        if search_word in link:
            item_dict['result'] = (result_data[0], link)
            filtered_links.append(item_dict)

    return filtered_links


def get_all_results(search_word, page_number=1):
    all_results = []
    for type, keyword in get_search_words(search_word).items():
        print(f"[*] {Fore.LIGHTYELLOW_EX}Query-String: {keyword}{Style.RESET_ALL}")
        results = search_and_get_results(query=keyword, page_number=page_number)
        for result in results:
            all_results.append({"type": type, "result": result})

    return all_results


def gen_filename(search_word):
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%m-%d-%H-%M")
    formatted_search_word = search_word.replace(" ", "_").replace(".", "_")  # 将空格替换为下划线以美化搜索词
    filename = f"{formatted_datetime}_{formatted_search_word}.xlsx"
    return filename


def load_data2file(clean_data, filename):
    types = [data['type'] for data in clean_data]
    titles = [data['title'] for data in clean_data]
    links = [data['link'] for data in clean_data]
    status_codes = [data['status_code'] for data in clean_data]
    df = pd.DataFrame({'事件类型': types, '标题': titles, '链接': links, '状态码': status_codes})
    df.to_excel(filename, index=False)


def check_url_status(data_list):
    status_codes = []

    for data in data_list:
        link = data['result'][1]
        try:
            response = requests.get(link, verify=False, proxies=None)
            status_code = response.status_code
        except requests.exceptions.RequestException:

            status_code = -1
        status_codes.append(status_code)

    clean_data_with_status = []
    for i, data in enumerate(data_list):
        type_value = data['type']
        title = data['result'][0]
        link = data['result'][1]
        status_code = status_codes[i]
        clean_data_with_status.append({'type': type_value, 'title': title, 'link': link, 'status_code': status_code})

    return clean_data_with_status


def main():
    print_logo()
    parser = argparse.ArgumentParser(description='Process data from command line', add_help=True)
    parser.add_argument('-w', '--search-word', type=str, help='The search word')
    parser.add_argument('-n', '--page-number', type=int, default=1, help='The search page_number')
    args = parser.parse_args()

    search_word = args.search_word
    page_number = args.page_number

    if not search_word:
        print("[!] 未提供搜索词，请使用 -w 或 --search-word 参数指定搜索词")
        sys.exit()
    if not page_number:
        print("[!] 未提供页码数，请使用 -n 或 --page-number 参数指定页码数")
        sys.exit()
    if page_number <= 0:
        print("页码数必须大于等于 1，请使用 -n 或 --page-number 参数指定正确的页码数")
        sys.exit()

    all_results = get_all_results(search_word, page_number=page_number)  # page_number为搜索的页数

    clean_data = process_data(search_word, all_results)
    print(clean_data)

    load_data2file(check_url_status(clean_data), gen_filename(search_word))  # 结果写入文件


if __name__ == '__main__':
    main()
