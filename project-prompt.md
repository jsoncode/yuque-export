### ai提示词
```
帮我写一个语雀文档导出的功能：
导出流程如下：
1.登录（我可以给你cookie）
2. 访问页面：https://www.yuque.com/{username}/{project}, 这里可配置username=xx,project=xx
页面里会生成一个js对象：
(function() {
  window.appData = JSON.parse(decodeURIComponent("...."))
})();

可以拿到appData.book.toc 所有文档的列表，里面的每一项id，就是下一步要用到的参数（还有title字段，用于下面导出时的文件名）

3. 请求接口 https://www.yuque.com/api/docs/{id}/export

入参：{"type":"markdown","force":0,"options":"{\"latexType\":2}"}
返回值：
{
    "data": {
        "state": "success",
        "url": "https://www.yuque.com/xxxx"
    }
}

这个url，就是导出的md文档地址了。

4. 将这个md下载下来，并解析下载里面的图片等资源地址：
https://cdn.nlark.com/yuque/....

所有资源下载下来，并将md中的链接替换成本地路径 ，保存到当前md同名的assets下面，导出的目录结构如下：
/{appData.book.name}
    /{title}/
        index.md
        /assets/


你可以用python来实现，目前只是一个空项目，你可以从头创建一个新项目。

上面的username,project,cookie能够通过配置文件进行配置。
```