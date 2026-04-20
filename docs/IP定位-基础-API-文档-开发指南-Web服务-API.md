---
created: 2026-04-20T12:59:17 (UTC +08:00)
tags: [IP定位-基础 API 文档-开发指南-Web服务 API]
source: https://lbs.amap.com/api/webservice/guide/api/ipconfig
author: 
---

# IP定位-基础 API 文档-开发指南-Web服务 API

> ## Excerpt
> IP定位-基础 API 文档-开发指南-Web服务 API

---
[开发](https://lbs.amap.com/api) Web服务 API 开发指南 基础 API 文档 IP定位

## IP定位 最后更新时间: 2026年02月02日

## 产品介绍

IP 定位是一套简单的 HTTP 接口，根据用户输入的 IP 地址，能够快速的帮用户定位 IP 的所在位置。

IP 定位：仅支持 IPV4，不支持国外 IP 解析。

## 适用场景

希望能够将 IP 信息转换为地理位置信息。

## 使用限制

服务调用量的限制请点击 [这里](https://lbs.amap.com/api/webservice/guide/tools/flowlevel) 查阅。  

## 使用说明

1

第一步

2

第二步

拼接 HTTP 请求 URL，第一步申请的 Key 需作为必填参数一同发送

3

第三步

接收 HTTP 请求返回的数据（JSON 或 XML 格式），解析数据

如无特殊声明，接口的输入参数和输出数据编码全部统一为 UTF-8。

成为开发者并创建 Key 

为了正常调用 Web 服务 API ，请先注册成为高德开放平台开发者，并申请 Web 服务的 key ，点击[具体操作](https://lbs.amap.com/api/webservice/create-project-and-key)。

#### IP 定位API服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/ip?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网 [申请 Web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|ip|ip 地址|需要搜索的 IP 地址（仅支持国内）
若用户不填写 IP，则取客户 http 之中的请求来进行定位|可选|无|
|sig|签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)，选择数字签名认证的付费用户必填|可选|无|

#### 返回结果参数说明

IP定位查询的响应结果的格式由请求参数output指定。

|名称|含义|规则说明|
|---|---|---|
|status|返回结果状态值|值为0或1,0表示失败；1表示成功|
|info|返回状态说明|返回状态说明，status 为0时，info 返回错误原因，否则返回“OK”。|
|infocode|状态码|返回状态说明,10000代表正确,详情参阅 info 状态表|
|province|省份名称|若为直辖市则显示直辖市名称；
如果在局域网 IP 网段内，则返回“局域网”；
非法 IP 以及国外 IP 则返回空|
|city|城市名称|若为直辖市则显示直辖市名称；
如果为局域网网段内 IP 或者非法 IP 或国外 IP，则返回空|
|adcode|城市的 adcode 编码|adcode 信息可参考 [城市编码表](https://lbs.amap.com/api/webservice/download) 获取|
|rectangle|所在城市矩形区域范围|所在城市范围的左下右上对标对|

#### 服务示例

```
https://restapi.amap.com/v3/ip?ip=114.247.50.2&output=xml&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|ip|需要搜索的 IP 地址（仅支持国内）
若用户不填写 IP，则取客户 HTTP 之中的请求来进行定位|否|

是查询的城市范围，offset(20)为每

这篇文档有帮助吗？

完全没有非常有

本页目录

-   [产品介绍](https://lbs.amap.com/api/webservice/guide/api/ipconfig#t0 "产品介绍")
-   [适用场景](https://lbs.amap.com/api/webservice/guide/api/ipconfig#t1 "适用场景")
-   [使用限制](https://lbs.amap.com/api/webservice/guide/api/ipconfig#t2 "使用限制")
-   [使用说明](https://lbs.amap.com/api/webservice/guide/api/ipconfig#t3 "使用说明")
-   [IP 定位](https://lbs.amap.com/api/webservice/guide/api/ipconfig#t4 "IP 定位")
-   [IP 定位API服务地址](https://lbs.amap.com/api/webservice/guide/api/ipconfig#s0 "IP 定位API服务地址")
-   [请求参数](https://lbs.amap.com/api/webservice/guide/api/ipconfig#s1 "请求参数")
-   [返回结果参数说明](https://lbs.amap.com/api/webservice/guide/api/ipconfig#s2 "返回结果参数说明")
-   [服务示例](https://lbs.amap.com/api/webservice/guide/api/ipconfig#s3 "服务示例")
