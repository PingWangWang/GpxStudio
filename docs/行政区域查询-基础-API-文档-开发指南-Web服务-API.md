---
created: 2026-04-20T12:58:58 (UTC +08:00)
tags: [行政区域查询-基础 API 文档-开发指南-Web服务 API]
source: https://lbs.amap.com/api/webservice/guide/api/district
author: 
---

# 行政区域查询-基础 API 文档-开发指南-Web服务 API

> ## Excerpt
> 行政区域查询-基础 API 文档-开发指南-Web服务 API

---
[开发](https://lbs.amap.com/api) Web服务 API 开发指南 基础 API 文档 行政区域查询

## 行政区域查询 最后更新时间: 2024年10月24日

## 产品介绍

行政区域查询是一类简单的 HTTP 接口，根据用户输入的搜索条件可以帮助用户快速的查找特定的行政区域信息。

例如：中国>山东省>济南市>历下区>舜华路街道（国>省>市>区>街道）。

使用前，特别说明：

-   目前部分城市和省直辖县因为没有区县的概念，故在市级下方直接显示街道。例如：广东-东莞、海南-文昌市。
    
-   街道级别是不能返回边界数据 polyline 的，乡镇街道级别返回的 adcode 是所属区县的 adcode。
    
-   暂时不支持台湾省的详细区划查询。
    

## 适用场景

用户希望通过得到行政区域信息，进行开发工作。

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

## 行政区域查询

#### 行政区域查询 API 服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/config/district?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网 [申请 Web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|keywords|查询关键字|规则：只支持单个关键词语搜索关键词支持：行政区名称、citycode、adcode
例如，在 subdistrict=2，搜索省份（例如山东），能够显示市（例如济南），区（例如历下区）
adcode 信息可参考 [城市编码表](https://lbs.amap.com/api/webservice/download) 获取|可选|无|
|subdistrict|子级行政区|规则：设置显示下级行政区级数（行政区级别包括：国家、省/直辖市、市、区/县、乡镇/街道多级数据）
可选值：0、1、2、3等数字，并以此类推
0：不返回下级行政区；
1：返回下一级行政区；
2：返回下两级行政区；
3：返回下三级行政区；
需要在此特殊说明，目前部分城市和省直辖县因为没有区县的概念，故在市级下方直接显示街道。
例如：广东-东莞、海南-文昌市|可选|1|
|page|需要第几页数据|最外层的 districts 最多会返回20个数据，若超过限制，请用 page 请求下一页数据。
例如：page=2；page=3。默认：page=1|可选|1|
|offset|最外层返回数据个数|可选|20|
|extensions|返回结果控制|此项控制行政区信息中返回行政区边界坐标点； 可选值：base、all;
base:不返回行政区边界坐标点；
all:只返回当前查询 district 的边界值，不返回子节点的边界值；
目前不能返回乡镇/街道级别的边界值|可选|base|
|filter|根据区划过滤|按照指定行政区划进行过滤，填入后则只返回该省/直辖市信息
需填入 adcode，为了保证数据的正确，强烈建议填入此参数|可选|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output=JSON 时有效|可选|
|output|返回数据格式类型|可选值：JSON，XML|可选|JSON|

#### 返回结果参数说明

行政区域查询的响应结果的格式由请求参数output指定。

|名称|含义|规则说明|
|---|---|---|
|status|返回结果状态值|值为0或1，0表示失败；1表示成功|
|info|返回状态说明|返回状态说明，status 为0时，info 返回错误原因，否则返回“OK”。|
|infocode|状态码|返回状态说明，10000代表正确，详情参阅 info 状态表|
|suggestion|建议结果列表|
|keywords|建议关键字列表|
|cities|建议城市列表|
|districts|行政区列表|
|district|行政区信息|
|citycode|城市编码|
|adcode|区域编码|街道没有独有的 adcode，均继承父类（区县）的 adcode|
|name|行政区名称|
|polyline|行政区边界坐标点|当一个行政区范围，由完全分隔两块或者多块的地块组
成，每块地的 polyline 坐标串以|
|center|区域中心点|乡镇级别返回的center是边界线上的形点，其他行政级别返回的center不一定是中心点，若政府机构位于面内，则返回政府坐标，政府不在面内，则返回繁华点坐标。|
|level|行政区划级别|country:国家
province:省份（直辖市会在province显示）
city:市（直辖市会在province显示）
district:区县
street:街道|
|districts|下级行政区列表，包含 district 元素|

#### 服务示例

```
https://restapi.amap.com/v3/config/district?keywords=北京&subdistrict=2&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|keywords|规则：只支持单个关键词语搜索关键词支持：行政区名称、citycode、adcode
例如，在 subdistrict=2，搜索省份（例如山东），能够显示市（例如济南），区（例如历下区）|否|
|subdistrict|规则：设置显示下级行政区级数（行政区级别包括：国家、省/直辖市、市、区/县4个级别）
可选值：0、1、2、3
0：不返回下级行政区；
1：返回下一级行政区；
2：返回下两级行政区；
3：返回下三级行政区；|否|
|extensions|此项控制行政区信息中返回行政区边界坐标点； 可选值：base、all;
base:不返回行政区边界坐标点；
all:只返回当前查询 district 的边界值，不返回子节点的边界值；|否|

是查询的城市范围，offset(20)为每

这篇文档有帮助吗？

完全没有非常有

本页目录

-   [产品介绍](https://lbs.amap.com/api/webservice/guide/api/district#t0 "产品介绍")
-   [适用场景](https://lbs.amap.com/api/webservice/guide/api/district#t1 "适用场景")
-   [使用限制](https://lbs.amap.com/api/webservice/guide/api/district#t2 "使用限制")
-   [使用说明](https://lbs.amap.com/api/webservice/guide/api/district#t3 "使用说明")
-   [行政区域查询](https://lbs.amap.com/api/webservice/guide/api/district#t4 "行政区域查询")
-   [行政区域查询 API 服务地址](https://lbs.amap.com/api/webservice/guide/api/district#s0 "行政区域查询 API 服务地址")
-   [请求参数](https://lbs.amap.com/api/webservice/guide/api/district#s1 "请求参数")
-   [返回结果参数说明](https://lbs.amap.com/api/webservice/guide/api/district#s2 "返回结果参数说明")
-   [服务示例](https://lbs.amap.com/api/webservice/guide/api/district#s3 "服务示例")
