# googleCrawler

一个google hack自动化的小工具，可以获取站点的链接，标题，状态码

代码功底不太行，希望各位师傅多提提意见

## 作者

- [@D3n13d](https://github.com/D3n13d)

## Demo

```cmd
python .\googleCrawler.py -w "example.com" -n 1
```

## 食用方法

1、检查环境 `pip install -r requirements.txt
`

2、可以电子出国(程序默认代理端口7890)

3、根据需求调整代码中的googlehack语句

4、`python .\googleCrawler.py -w "example.com" -n 1`

5、备注：

测试程序 -w 代表你要搜索的字符串 -n 代表搜索的页数

如果访问状态码显示-1代表请求失败

## 参考项目

1、https://github.com/littlebin404/Google_Spider

2、https://github.com/weishen250/Google-Spider