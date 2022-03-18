---
date: "2020-02-20"
layout: post
title: 用Docker快速部署NextCloud和WordPress, 以及开启Https
subheading: Deploy NextCloud & WordPress with docker and enable HTTPS.
author: JamzumSum
categories: Linux
banner:
  image: https://unsplash.com/photos/GnvurwJsKaY/download?force=true&w=1920
tags: Linux docker nextcloud wordpress
---

# 用Docker快速部署NextCloud和WordPress, 以及开启Https

Deploy NextCloud & WordPress with docker and enable HTTPS.

> 第一次发文emmmm 有点紧张hhh

话说zzs买了个小VPS觉得太闲了, 前几天逛基安的时候看见有人发文搞nextcloud离线下载, 这就心痒痒起来(其实我是因为想倒腾EFB微信转发tg才想起来我还有一VPS...(不过没什么关系我就不说了(实际上是因为折腾了两天发现怎么弄也不好使QAQ)))

废话少说, 大家买来VPS都做什么呢? 国外的可以拿来飞飞机? 除了这个呢? (开始滑稽) NextCloud是一款肥肠棒的个人云存储服务, 自己用或者家里用, 再或者小团队什么的非常nice(还有离线下载哦你懂的). WordPress, 就是你现在看见的, 做个个人主站啊博客什么的...~~好像也可以拿来鸽的样子(咕!)~~

行了上面都是废话, 我写的可能 __不能算是教程__, 毕竟我原本的目的只是记录一下自己的失败经历...然后给大家说说我是怎么解决的, 教程还是上网搜合适, 文末我会列出来我到最后还开着的几个网页(捂脸)

## 环境

* Debian9, 厂家是Vultr
* 域名一个, 阿里云一块钱一年那个 ~~(贫穷.jpg)~~ , 已搞定域名解析.

## 安装Docker

> 我从没想过第一步就有这么大的岔子(比比划划)

### 问题: docker.socket: Control process exited, code=exited status=127

~~~ bash
systemctl start docker
~~~

咱都是按着教程来的, 装都装好了为啥就启不动捏? 查日志看见上面这句话, 啥意思啊? 咋回事啊? 嘎哈啊? 百度罢. 结果百度一番, 错误码216的, 203的, 还有什么`1/FAILURE`的, __就是没有错误码127__...Google了一下, 看见一个可能是127的还~~TM~~是日语的...

> zzs的话: 请务必注意自己的错误码/退出码 __是不是和网上的教程一样__, zzs因为找了错误的教程把用户组整的一团糟

多余的咱就不说了, 最后还是叫咱找着办法了: [ubuntu安装docker-ce](1) 这篇打开了局面, 里面的0x03部分, 说的是`libltdl7和libsystemd-journal0依赖问题`, 要安装libltdl7和libsystemd-journal0彩星. 然而实际操作发现libsystemd-journal0没有这个玩意(可能因为我是Debian stretch罢, 跟ubuntu还是有点区别), 那就

~~~ bash
apt-get install libsystemd-journal*
~~~

一波, 反正真是给我莽上了...然后, 又碰见0x02所述错误, 按照教程解决.

#### Solution

1. 安装libltdl7和libsystemd-journal0
2. 到上面教程里给的网站, 找到对应的操作系统, 手动下载安装`docker-ce-cli`和`containerd.io`的deb包
3. 还是哪个网站, 就在那个页面, 下载安装`docker-ce`

~~~ bash
systemctl start docker
~~~

Nice.

## 安装WordPress和NextCloud

### 问题1: 我不想用Nginx, 也不想用docker-compose

> 看官dalao见笑了, 毕竟小白 整不懂那些高级货...

#### subQ1: 数据库为啥只能开一个吖? 

我本来是想用docker起两个数据库来着, 但是第二个mysql container就是起不来, 刚start就exit了...进去一瞧, 是这样的:

~~~ bash
mysql mmap(137363456 bytes) failed; errno 12
~~~

搜了一下, 大概就是swap分区不够...我free了一下, 好像确实不够...~~不过当时确实没打算管了, 就只开了一个给wordpress, nextcloud用它自己的sqlite就得了...~~

2019-12月记: 我这次弄了个阿里云的学生机, 空间还够, 我就开两个MySQL.

开一个MySQL:

~~~ bash
docker run --name mysql-nextcloud \
-d -v /root/nextcloud/mysql/:/var/lib/mysql \
--innodb-buffer-pool-size=64M \
-e MYSQL_ROOT_PASSWORD="这写密码" \
mysql
~~~

为了不出`The server requested authentication method unknown to the client`的错误, 进去配置数据库:

~~~ bash
# 切换软件源, 国外的VPS就不用这步骤
echo -e "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main contrib non-free\n\
# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main contrib non-free\n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-updates main contrib non-free\n\
# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-updates main contrib non-free\n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-backports main contrib non-free\n\
# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-backports main contrib non-free\n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security buster/updates main contrib non-free\n\
# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian-security buster/updates main contrib non-free" > /etc/apt/sources.list
apt-get update && apt-get install vim
vim /etc/my.cnf
# 输入这些内容
[mysqlId]
default_authentication_plugin=mysql_native_password
~~~

重启MySQL. 然后重新进入, 建立nextcloud数据库.

~~~ SQL
CREATE DATABASE nextcloud;
create user 'nextclouduser'@'%' identified by '这写数据库密码';
grant all privileges on nextcloud.* to 'nextclouduser'@'%' with grant option;
flush privileges;
~~~

注意, 新pull来的镜像是MySQL8, 授权语句变得不一样了.
其实之前修改配置文件也是因为nextcloud镜像的php还不能使用新验证方式验证, 还得修改默认的认证插件.

NextCloud:

~~~ bash
docker run --name nextcloud \
-v /root/nextcloud/data:/data \
-v /etc/letsencrypt:/etc/letsencrypt \
-p 8080:80 \
-p 8088:443 \
--link mysql-nextcloud:mysql \
--privileged=true \
-d nextcloud
~~~

#### subQ2: WordPress连不上数据库???

这个问题应该不算疑难, 网上比较好搜...大致就是数据库拒绝访问? 可以看看这两篇教程:

* [使用docker搭建wordpress网站](3)
  启动数据库容器的命令比较有参考价值. 
* [docker 安装wordpress](4)
  里面提及的SQL操作解决了数据库访问问题. 

~~~ bash
docker exec -it mysql-wordpress bash
mysql -u root -p
这写密码
~~~

~~~ SQL
ALTER USER 'root'@'%' IDENTIFIED BY 'password' PASSWORD EXPIRE NEVER;
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '这写密码';
FLUSH PRIVILEGES;
~~~

上边是我用的命令...我看有的只用一句就行...爱咋咋地罢...顺便贴上我跑数据库和WordPress的命令

~~~ bash
docker run --name mysql-wordpress \
-d -v /root/wordpress/mysql/:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD="这写密码" \
mysql

docker run --name wordpress \
-p 80:80 \
-p 443:443 \
--link mysql-wordpress:mysql \
--privileged=true \
-v /etc/letsencrypt:/etc/letsencrypt \
-v /root/wordpress-html:/var/www/html \
-d wordpress
~~~

您可能看见了我挂载了`/etc/letsencrypt`, 毕竟我们是要开Https的...所以, 端口
80和 __443__ 都要留出来.

> 如果想不重开一个容器, 还要修改端口, 那就要修改一两个文件...zzs改了半天发现它老是自己改回去... 明明是照着教程做的结果却一点都不一样...所以请务必留出443端口.

#### subQ3: NextCloud提示不信任的域名?

直接IP访问没有问题, 用域名访问会提示不信任的域名, 给了你办法, 修改`config/config.php`. zzs进了容器之后直接

~~~ bash
whereis config
~~~

, 告诉我是`/usr/src/nextcloud/config`...然后那里面也没有`config.php`, 我就苦逼地在那新建, 然后怎么改怎么没用...实际上是在`/var/www/html`里面, 就是刚进容器的目录...在它下面有一个`config`目录, 里面有`config.php`, 这才是运行时配置, `*src*`什么的, 一看就是源码啥的(捂脸)

在里面加上这么一段配置就行了.

~~~ PHP
'trusted_domains' =>
  array (
   0 => 'localhost',
   1 => 'zzsblog.top',
   2 => 'www.zzsblog.top',
   3 => '我这行写的是服务器地址, 实际上应该不用',
),
~~~

## 开启SSL

开头贴两篇教程以示尊敬. 不管用不用的上, 进去瞅瞅.

* [烂泥：wordpres和nextcloud启用https访问](5)
* [Docker 安装 Wordpress 并开启 HTTPS](2)

### 问题2: certbot啥玩意啊?

网上搜了一下大家都用的是Let's Encrypt的SSL证书, 有个叫certbot的工具来自动帮你注册证书...于是乎就发现certbot不会用...(捂脸) 网上的教程与我们的实际情况相差比较大, 于是在certbot的官网上找找, 折腾出了一个办法. (安装请自行搞定)

~~~ bash
certbot certonly -–webroot
~~~

敲上之后, 程序会让你填邮箱啊同意协议这些, 你知道该怎么做. 之后看到, 要让你填域名了, 把你解析到你服务器上的域名填上, 可以填多个, 空格分隔. 

下一步, 划重点. __webroot是个啥玩意啊?__ zzs很惭愧, 看名字就能领悟的问题想了两天. 答案就是, 你启动容器的时候宿主机上链接的位置. 比如我的挂载的路径就是`/root/wordpress-html`, 如果你忘了自己敲了啥, 可以去docker的配置文件里自己瞅瞅...~~过于复杂, 咱就不说了哈.~~ 这里要注意, webroot模式要保持你机器上webserver开启, 也就是说这个时候你的 __80端口一定要在LISTEN__ 千万别把映射80端口那个容器关了.

于是你就能看到, 在`/etc/letsencrypt/live/zzsblog.top/`下(反正在`live`文件夹下找就行了)有一堆证书啊私钥啊什么的, 这些证书的物理存储在`/etc/letsencrypt/archive/`下 ~~, 请注意`cert1.pem` `privkey1.pem` `fullchain1.pem`这几个文件, 一会开https要用.~~
这几个软连接也是可以用的, 也就是`/etc/letsencrypt/live/zzsblog.top/`下的`cert.pem`, `privkey.pem`, `fullchain.pem`.

### 问题3: 证书有了, 咋用啊?

进入docker容器, 无论NextCloud还是WordPress __都是一样的__ 操作.
先安一波vim, 发现安不了(fxxk). 这时你需要update一下.

~~~ bash
apt-get update && apt-get install vim -y
~~~

然后测试一下openssl安上没, 命令`openssl`, 进入了就对了, 敲`exit`退出. 

~~~ bash
a2enmod ssl && exit
docker restart wordpress
~~~

其实运行过`a2enmod ssl`后第一次只要重启apache即可, 图省事就直接重启容器了. 

> 有兴趣可以看看我贴的教程链接, 里面对各个步骤有一些解释. 

~~~ bash
ln -s /etc/apache2/sites-available/default-ssl.conf \
/etc/apache2/sites-enabled/default-ssl.conf
~~~

然后修改刚才软连接的源, 也就是`/etc/apache2/sites-available/default-ssl.conf`. 这里就是我和原教程不一样的地方了. 要改的有三处:

* SSLCerticicateFile
  填cert.pem, 具体路径自己写(你之前已经挂载了`/etc/letsencrypt`了罢?)
* SSLCertificateKeyFile
  这个是privkey.pem
* SSLCertificateChainFile
  这个被注掉了, 把注释去掉, 填fullchain.pem那个.

然后修改`/etc/apache2/sites-available/`下的`000-default.conf`文件, 在最外层标签里增加下面一段:

~~~
<Directory "/var/www/html">
    RewriteEngine   on
    RewriteBase /
    # FORCE HTTPS
    RewriteCond %{HTTPS} !=on
    RewriteRule ^/?(.*) https://%{SERVER_NAME}/$1 [R,L]
</Directory>
~~~

然后呢, 就算完了, https访问成功, http重定向到https. 有关收尾工作, 可以看一下[这篇教程](2), 在wordpress里设置本站网址(实际上好像就是你浏览器地址栏里显示的地址), 然后在数据库里替换一下http链接(如果你之前没在上面发过链接啊图片啊什么的应该是不用), 命令是这个, 原教程里也有

~~~ SQL
update wp_posts set post_content = replace(post_content, 'http://zzsblog.top','https://zzsblog.top');
~~~

记得把域名改了啊(滑稽)

## 结尾

1. https://www.cnblogs.com/pcat/p/7977877.html ubuntu安装docker-ce
2. https://blog.csdn.net/yori_chen/article/details/88577249 Docker 安装 Wordpress 并开启 HTTPS
3. https://www.jianshu.com/p/cdd94d6c2d68 使用docker搭建wordpress网站
4. https://my.oschina.net/langwanghuangshifu/blog/2965662 docker 安装wordpress
5. https://www.ilanni.com/?p=13347 烂泥：wordpres和nextcloud启用https访问

除了上面提到的教程, 还向我翻到的一万个教程的作者们表示感谢. 

> 现在是2021年8月份, 此时我刚刚重建了博客, 以github托管的形式(笑, 也就是你所见的此处. 于是也就没有什么wordpress之类了, 发这篇的目的呢, 充数罢了(笑. 不过好歹也算自己以前的试错经历, 发出来说不定能帮到你呢?

[1]: https://www.cnblogs.com/pcat/p/7977877.html "ubuntu安装docker-ce"
[2]: https://blog.csdn.net/yori_chen/article/details/88577249 "Docker 安装 Wordpress 并开启 HTTPS"
[3]: https://www.jianshu.com/p/cdd94d6c2d68 "使用docker搭建wordpress网站"
[4]: https://my.oschina.net/langwanghuangshifu/blog/2965662 "docker 安装wordpress"
[5]: https://www.ilanni.com/?p=13347 "烂泥：wordpres和nextcloud启用https访问"