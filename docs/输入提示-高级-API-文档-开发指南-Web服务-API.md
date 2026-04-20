---
created: 2026-04-20T13:02:18 (UTC +08:00)
tags: [输入提示-高级 API 文档-开发指南-Web服务 API]
source: https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips
author: 
---

# 输入提示-高级 API 文档-开发指南-Web服务 API

> ## Excerpt
> 输入提示-高级 API 文档-开发指南-Web服务 API

---
[开发](https://lbs.amap.com/api) Web服务 API 开发指南 高级 API 文档 输入提示

## 输入提示 最后更新时间: 2026年02月02日

## 产品介绍

输入提示是一类简单的 HTTP 接口，提供根据用户输入的关键词查询返回建议列表。

## 适用场景

在高德客户端的使用场景，输入“仙林”之后出现提示相关。

![](%E8%BE%93%E5%85%A5%E6%8F%90%E7%A4%BA-%E9%AB%98%E7%BA%A7-api-%E6%96%87%E6%A1%A3-%E5%BC%80%E5%8F%91%E6%8C%87%E5%8D%97/doc_1719913276682_db867.png)

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

## 输入提示

#### 输入提示API服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/assistant/inputtips?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网 [申请 Web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|keywords|查询关键词|必填|无|
|type|POI 分类|服务可支持传入多个分类，多个类型剑用“|”分隔
可选值：POI 分类名称、分类代码
此处强烈建议使用分类代码，否则可能会得到不符合预期的结果|可选|
|location|坐标|格式：“X,Y”（经度,纬度），不可以包含空格
建议使用 location 参数，可在此 location 附近优先返回搜索关键词信息
在请求参数 city 不为空时生效|可选|无|
|city|搜索城市|可选值：citycode、adcode，不支持县级市。
如：010/110000
adcode 信息可参考 [城市编码表](https://lbs.amap.com/api/webservice/download) 获取。
填入此参数后，会尽量优先返回此城市数据，但是不一定仅局限此城市结果，若仅需要某个城市数据请调用 citylimit 参数。
如：在深圳市搜天安门，返回北京天安门结果。|可选|无（默认在全国范围内搜索）|
|citylimit|仅返回指定城市数据|可选值：true/false|可选|false|
|datatype|返回的数据类型|多种数据类型用“|”分隔，可选值：all-返回所有数据类型、poi-返回POI数据类型、bus-返回公交站点数据类型、busline-返回公交线路数据类型|可选|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|output|返回数据格式类型|可选值：JSON,XML|可选|JSON|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output=JSON 时有效|可选|无|

#### 返回结果参数说明

输入提示的响应结果的格式由请求参数 output 指定。

|参数名|含义|规则说明|
|---|---|---|
|status|返回状态|值为0或1
1：成功；0：失败|
|info|返回的状态信息|status 为0时，info 返回错误原；否则返回“OK”。详情参阅 [info 状态表](https://lbs.amap.com/api/webservice/guide/tools/info/)|
|count|返回结果总数目|
|tips|建议提示列表|
|tip|提示信息|
|id|返回数据 ID|若数据为 POI 类型，则返回 POI ID;若数据为 bus 类型，则返回 bus id;若数据为 busline 类型，则返回 busline id。|
|name|tip 名称|
|district|所属区域|省+市+区（直辖市为“市+区”）|
|adcode|区域编码|六位区县编码|
|location|tip 中心点坐标|当搜索数据为 busline 类型时，此字段不返回|
|address|详细地址|

#### 服务示例

```
https://restapi.amap.com/v3/assistant/inputtips?output=xml&city=010&keywords=招商银行&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|keywords|查询关键词|是|
|type|查询 POI 类型|否|
|location|经度,纬度;建议使用 location 参数，可在此 location 附近优先返回搜索关键词信息|否|
|city|查询城市。可选值：城市中文、中文全拼、citycode、adcode|否|
|datatype|多种数据类型用“|”分隔
可选值：
all：返回所有数据类型；
poi：返回POI数据类型；
bus：返回公交站点数据类型；
busline：返回公交线路数据类型|

是查询的城市范围，offset(20)为每

这篇文档有帮助吗？

完全没有非常有

本页目录

-   [产品介绍](https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips#t0 "产品介绍")
-   [适用场景](https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips#t1 "适用场景")
-   [使用限制](https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips#t2 "使用限制")
-   [使用说明](https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips#t3 "使用说明")
-   [输入提示](https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips#t4 "输入提示")
-   [输入提示API服务地址](https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips#s0 "输入提示API服务地址")
-   [请求参数](https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips#s1 "请求参数")
-   [返回结果参数说明](https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips#s2 "返回结果参数说明")
-   [服务示例](https://lbs.amap.com/api/webservice/guide/api-advanced/inputtips#s3 "服务示例")
