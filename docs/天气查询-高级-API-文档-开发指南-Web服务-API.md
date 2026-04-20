---
created: 2026-04-20T13:00:58 (UTC +08:00)
tags: [天气查询-高级 API 文档-开发指南-Web服务 API]
source: https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo
author: 
---

# 天气查询-高级 API 文档-开发指南-Web服务 API

> ## Excerpt
> 天气查询-高级 API 文档-开发指南-Web服务 API

---
[开发](https://lbs.amap.com/api) Web服务 API 开发指南 高级 API 文档 天气查询

## 天气查询 最后更新时间: 2026年02月02日

## 产品介绍

天气查询是一个简单的 HTTP 接口，根据用户输入的 adcode，查询目标区域当前/未来的天气情况。

提示

如需更高精度，或者更多深度内容（如积水、积雪）等高级天气能力，请通过 [工单](https://console.amap.com/dev/ticket/create/66) 进行商务咨询。

## 适用场景

需要使用相关天气查询的时候。

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

## 天气查询

#### 天气查询API服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/weather/weatherInfo?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网 [申请 web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|city|城市编码|输入城市的 adcode，adcode 信息可参考 [城市编码表](https://lbs.amap.com/api/webservice/download)|必填|无|
|extensions|气象类型|可选值：base/all
base:返回实况天气
all:返回预报天气|可选|无|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|output|返回格式|可选值：JSON,XML|可选|JSON|

#### 返回结果参数说明

实况天气每小时更新多次，预报天气每天更新3次，分别在8、11、18点左右更新。由于天气数据的特殊性以及数据更新的持续性，无法确定精确的更新时间，请以接口返回数据的 reporttime 字段为准。[天气结果对照表>>](https://lbs.amap.com/api/webservice/guide/tools/weather-code/)

|名称|含义|规则说明|
|---|---|---|
|status|返回状态|值为0或1
1：成功；0：失败|
|count|返回结果总数目|
|info|返回的状态信息|
|infocode|返回状态说明,10000代表正确|
|lives|实况天气数据信息|
|province|省份名|
|city|城市名|
|adcode|区域编码|
|weather|天气现象（汉字描述）|
|temperature|实时气温，单位：摄氏度|
|winddirection|风向描述|
|windpower|风力级别，单位：级|
|humidity|空气湿度|
|reporttime|数据发布的时间|
|forecasts|预报天气信息数据|
|city|城市名称|
|adcode|城市编码|
|province|省份名称|
|reporttime|预报发布时间|
|casts|预报数据 list 结构，元素 cast,按顺序为当天、第二天、第三天、第四天的预报数据|
|date|日期|
|week|星期几|
|dayweather|白天天气现象|
|nightweather|晚上天气现象|
|daytemp|白天温度|
|nighttemp|晚上温度|
|daywind|白天风向|
|nightwind|晚上风向|
|daypower|白天风力|
|nightpower|晚上风力|

#### 服务示例

```
https://restapi.amap.com/v3/weather/weatherInfo?city=110101&key=<用户key>
```

|参数|值|备注|必选|
|---|---|---|---|
|city|需要查询天气的城市编码|否|

是查询的城市范围，offset(20)为每

这篇文档有帮助吗？

完全没有非常有

本页目录

-   [产品介绍](https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo#t0 "产品介绍")
-   [适用场景](https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo#t1 "适用场景")
-   [使用限制](https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo#t2 "使用限制")
-   [使用说明](https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo#t3 "使用说明")
-   [天气查询](https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo#t4 "天气查询")
-   [天气查询API服务地址](https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo#s0 "天气查询API服务地址")
-   [请求参数](https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo#s1 "请求参数")
-   [返回结果参数说明](https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo#s2 "返回结果参数说明")
-   [服务示例](https://lbs.amap.com/api/webservice/guide/api-advanced/weatherinfo#s3 "服务示例")
