import os
import random
import urllib
import urllib.parse
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
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
            response = requests.get(url, headers=headers, proxies=proxies)

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
            print(f"[-] 页面访问失败请检查代理")
            print(url)
            break

        pagenum += 10

    return results


def get_search_words(keyword):
    rule_dict = {
        "数据泄露": "{} intext:vpn OR 用户名 OR 密码 OR 帐号 OR 默认密码".format(keyword),
        # "相关文件": "{} filetype:.doc OR .docx OR .xls OR .xlsx OR .ppt OR .pptx OR .odt OR .pdf OR .rtf OR .sxw OR .psw OR .csv".format(
        #     keyword),
        # "文件泄露": "{} ext:.bkf OR .bkp OR .old OR .backup OR .bak OR .swp OR .rar OR .txt OR .zip OR .7z OR .sql OR .tar.gz OR .tgz OR .tar OR .conf OR .cnf OR .reg OR .inf OR .rdp OR .cfg OR .txt OR .ora OR .ini".format(
        #     keyword),
        # "数据库文件泄露": "{} ext:.sql OR .dbf OR .mdb OR .db".format(keyword),
        # "日志信息": "{} ext:.log".format(keyword),
        # "报错页面": '{} intext:"sql syntax near" OR intext:"error" OR intext:"syntax error has occurred" OR intext:"incorrect syntax near" OR intext:"unexpected end of SQL command" OR intext:"Warning: mysql_connect()" OR intext:"Warning: mysql_query()" OR intext:"Warning: pg_connect()'.format(
        #     keyword),
        # "SSO/VPN": "{} intext:统一认证 OR intext:vpn OR intext:webvpn OR intext:sslvpn".format(keyword),
        # "网站功能": '{} intext:后台 OR intext:留言 OR intext:邮箱'.format(keyword)
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


def load_excel(file_path):
    return pd.read_excel(file_path, engine='openpyxl')


def save_to_output(df, filename):
    output_path = f"./output/{filename}"
    df.to_excel(output_path, index=False, engine='openpyxl')
    return output_path


def load_data2file(clean_data, filename):
    if not os.path.exists("./output"):
        os.mkdir("./output")

    # 构造DataFrame
    types = [data['type'] for data in clean_data]
    titles = [data['title'] for data in clean_data]
    links = [data['link'] for data in clean_data]
    status_codes = [data['status_code'] for data in clean_data]

    df = pd.DataFrame({'事件类型': types, '标题': titles, '链接': links, '状态码': status_codes})
    df.to_excel(filename, index=False)


def gen_filename(search_word):
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%m-%d-%H-%M")
    formatted_search_word = search_word.replace(" ", "_").replace(".", "_")  # 将空格替换为下划线以美化搜索词
    filename = f"./output/{formatted_datetime}_{formatted_search_word}.xlsx"
    return filename


def display_dataframe_with_links(df):  # 将DataFrame中的链接列替换为HTML链接
    links_html = df['link'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>').tolist()
    df_display = df.copy()
    df_display['链接'] = links_html
    st.write(df_display.to_html(escape=False), unsafe_allow_html=True)


def main_page():
    st.markdown("<h2 style='text-align: center; color: black;'>googleCrawler</h2>", unsafe_allow_html=True)

    search_word = st.text_input("请输入搜索词:", value="")
    page_number = st.slider("选择页码数", 1, 20, 1)

    if st.button("开始搜索"):
        if not search_word:
            st.warning("未提供搜索词。")
            return
        if not page_number:
            st.warning("未提供页码数。")
            return
        if page_number <= 0:
            st.warning("页码数必须大于等于 1。")
            return

        with st.spinner("正在搜索......"):
            all_results = get_all_results(search_word, page_number=page_number)
            clean_data = process_data(search_word, all_results)
            filename = gen_filename(search_word)

        with st.spinner("正在检测目标是否可访问..."):
            load_data2file(check_url_status(clean_data), filename)
            st.success("搜索完成!")
            # 从文件读取一次
            df = pd.read_excel(filename, engine='openpyxl')
            st.dataframe(df)

    if st.button("查看历史搜索结果"):
        st.session_state.page = "history"
        st.experimental_rerun()


def history_page():
    st.markdown("<h4 style='color: black;'>历史搜索结果检测</h4>", unsafe_allow_html=True)
    try:
        files = os.listdir("./output")
        excel_files = [file for file in files if file.endswith('.xlsx')]

        if not excel_files:
            st.warning("没有找到历史搜索的Excel文件")
            return

        selected_file = st.selectbox("选择一个历史文件:", ["请选择文件"] + excel_files)

        if selected_file != "请选择文件":
            df = load_excel(f"./output/{selected_file}")
            st.dataframe(df)
    except Exception as e:
        st.error(f"出现错误：{e}")

    # 提供返回到主页面的按钮
    if st.button("返回主页面"):
        st.session_state.page = "main"


def main():
    if "page" not in st.session_state:
        st.session_state.page = "main"

    if st.session_state.page == "main":
        main_page()
    elif st.session_state.page == "history":
        history_page()


# 调用主函数
if __name__ == "__main__":
    main()
