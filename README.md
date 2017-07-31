PyRedisAdmin
============

A web GUI for Redis data management

About
========
PyRedisAdmin 是一个方便查看和管理Redis数据的web界面工具，使用Python开发。基于开源的轻量级python Web框架"Mole"
构建而成，不依赖于其他第三方库，部署相当方便。

Quick start
========
1. 下载源码
2. 配置config.py,加入要管理的redis的主机地址和端口、密码等
3. 运行: python routes.py

Next work
========
1. ~~完善数据编辑和管理~~[已完成]
2. ~~加入redis数据分库的管理~~[已完成]
3. ~~加入redis账号验证功能~~[已完成]
4. ~~千万级以上海量数据的支持~~[已完成]
5. 完善的数据导入导出功能
6. 加入json数据的友好支持，提供json编辑器

Screenshots
========
![info](/media/images/info.jpg)

![info](/media/images/desc.png)

![data](/media/images/data.jpg)

1. 模糊搜索
2. 查看下一批
3. 精确查看某key
4. 展开/折叠所有
5. 删除选定的key
6. 实时自动刷新key的数据
7. 重命名key/删除当前查看的key/导出key的数据到文件
8. 更新key的过期时间
9. 修改/删除key的成员数据
10. 为key的数据添加新的成员
11. 批量清除当前列出的所有key
