---
created: 2026-04-20T13:00:19 (UTC +08:00)
tags: [高级IP定位-高级 API 文档-开发指南-Web服务 API]
source: https://lbs.amap.com/api/webservice/guide/api-advanced/ip
author: 
---

# 高级IP定位-高级 API 文档-开发指南-Web服务 API

> ## Excerpt
> 高级IP定位-高级 API 文档-开发指南-Web服务 API

---
[开发](https://lbs.amap.com/api) Web服务 API 开发指南 高级 API 文档 高级IP定位

## 高级IP定位 最后更新时间: 2026年02月02日

## 产品介绍

IP 定位是一套简单的 HTTP 接口，根据用户输入的 IP 地址，能够快速的帮用户定位 IP 的所在位置。同时支持 IPV4、IPV6，同时支持国外 IP 解析。高级IP定位服务由高德开放平台与埃文科技联合提供。

提示

高级 IP 定位属于高级服务接口。如需申请，请通过 [工单](https://console.amap.com/dev/ticket/create/66) 进行商务咨询。

## 适用场景

希望能够将 IP 信息转换为地理位置信息。

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

#### IP 定位 API 服务地址：

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v5/ip/location?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网 [申请 Web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|type|ip 类型|可选值：
4：ipv4
6：ipv6|必填|4|
|ip|ip 地址|需要搜索的 IP 地址（支持国内、国外地址解析）|必填|无|
|sig|签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)，选择数字签名认证的付费用户必填|可选|无|

#### 服务示例

```
https://restapi.amap.com/v5/ip/location?key=<用户的key>&ip=114.247.50.2&type=4
```

#### 返回结果参数说明

|名称|含义|规则说明|
|---|---|---|
|status|返回结果状态值|值为0或1,0表示失败；1表示成功|
|info|返回状态说明|返回状态说明，status 为0时，info 返回错误原因，否则返回“OK”。|
|infocode|状态码|返回状态说明,10000代表正确,详情参阅 [info 状态表](https://lbs.amap.com/api/webservice/guide/tools/info)|
|country|国家名称|例：中国|
|province|省份名称|若为直辖市则显示直辖市名称；
如果在局域网 IP 网段内，则返回“局域网”；
非法 IP 则返回空|
|city|城市名称|若为直辖市则显示直辖市名称；
如果为局域网网段内 IP 或者非法 IP，则返回空|
|district|区县|区（四级）|
|adcode|区县 adcode 编码|adcode 信息可参考 [城市编码表](https://lbs.amap.com/api/webservice/download) 获取|
|location|经纬度|经度在前，纬度在后|
|isp|运营商|
|ip|ip 地址|查询的 ip|

提示

返回结果：country=中国时，接口将把提供的经纬度数据转换为高德坐标系（GCJ-02）；若country≠中国时，则将直接输出原始的经纬度数据（即WGS-84坐标系）。

这篇文档有帮助吗？

完全没有非常有

本页目录

-   [产品介绍](https://lbs.amap.com/api/webservice/guide/api-advanced/ip#t0 "产品介绍")
-   [适用场景](https://lbs.amap.com/api/webservice/guide/api-advanced/ip#t1 "适用场景")
-   [使用说明](https://lbs.amap.com/api/webservice/guide/api-advanced/ip#t2 "使用说明")
-   [高级 IP 定位](https://lbs.amap.com/api/webservice/guide/api-advanced/ip#t3 "高级 IP 定位")
-   [IP 定位 API 服务地址：](https://lbs.amap.com/api/webservice/guide/api-advanced/ip#s0 "IP 定位 API 服务地址：")
-   [请求参数](https://lbs.amap.com/api/webservice/guide/api-advanced/ip#s1 "请求参数")
-   [服务示例](https://lbs.amap.com/api/webservice/guide/api-advanced/ip#s2 "服务示例")
-   [返回结果参数说明](https://lbs.amap.com/api/webservice/guide/api-advanced/ip#s3 "返回结果参数说明")
