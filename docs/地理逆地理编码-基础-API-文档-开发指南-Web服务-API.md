---
created: 2026-04-20T12:57:21 (UTC +08:00)
tags: [地理/逆地理编码-基础 API 文档-开发指南-Web服务 API]
source: https://lbs.amap.com/api/webservice/guide/api/georegeo
author: 
---

# 地理/逆地理编码-基础 API 文档-开发指南-Web服务 API

> ## Excerpt
> 地理/逆地理编码-基础 API 文档-开发指南-Web服务 API

---
[开发](https://lbs.amap.com/api) Web服务 API 开发指南 基础 API 文档 地理/逆地理编码

## 地理/逆地理编码 最后更新时间: 2026年02月02日

## 产品介绍

地理编码/逆地理编码 API 是通过 HTTP/HTTPS 协议访问远程服务的接口，提供结构化地址与经纬度之间的相互转化的能力。

结构化地址的定义：

首先，地址肯定是一串字符，内含国家、省份、城市、区县、城镇、乡村、街道、门牌号码、屋邨、大厦等建筑物名称。按照由大区域名称到小区域名称组合在一起的字符。一个有效的地址应该是独一无二的。注意：针对大陆、港、澳地区的地理编码转换时可以将国家信息选择性的忽略，但省、市、城镇等级别的地址构成是不能忽略的。暂时不支持返回台湾省的详细地址信息。

## 适用场景 

-   地理编码：将详细的结构化地址转换为高德经纬度坐标。且支持对地标性名胜景区、建筑物名称解析为高德经纬度坐标。 结构化地址举例：北京市朝阳区阜通东大街6号转换后经纬度：116.480881,39.989410  地标性建筑举例：天安门转换后经纬度：116.397499,39.908722
    
-   逆地理编码：将经纬度转换为详细结构化的地址，且返回附近周边的 POI、AOI 信息。 例如：116.480881,39.989410 转换地址描述后：北京市朝阳区阜通东大街6号
    

## 使用限制

详细的服务调用量限制可 [点我查阅](https://lbs.amap.com/api/webservice/guide/tools/flowlevel)。

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

## 地理编码

#### 地理编码 API 服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/geocode/geo?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|高德Key|用户在高德地图官网 [申请 Web 服务 API 类型 Key](https://lbs.amap.com/dev/)|必填|无|
|address|结构化地址信息|规则遵循：国家、省份、城市、区县、城镇、乡村、街道、门牌号码、屋邨、大厦，如：北京市朝阳区阜通东大街6号。|必填|无|
|city|指定查询的城市|可选输入内容包括：指定城市的中文（如北京）、指定城市的中文全拼（beijing）、citycode（010）、adcode（110000），不支持县级市。当指定城市查询内容为空时，会进行全国范围内的地址转换检索。
adcode 信息可参考 [城市编码表](https://lbs.amap.com/api/webservice/download) 获取|可选|无，会进行全国范围内搜索|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|output|返回数据格式类型|可选输入内容包括：JSON，XML。设置 JSON 返回结果数据将会以 JSON 结构构成；如果设置 XML 返回结果数据将以 XML 结构构成。|可选|JSON|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output 参数设置为 JSON 时有效。|可选|无|

#### 返回结果参数说明

响应结果的格式可以通过请求参数 output 指定，默认为 JSON 形式。

以下是返回参数说明：

|名称|含义|规则说明|
|---|---|---|
|status|返回结果状态值|返回值为 0 或 1，0 表示请求失败；1 表示请求成功。|
|count|返回结果数目|返回结果的个数。|
|info|返回状态说明|当 status 为 0 时，info 会返回具体错误原因，否则返回“OK”。详情可以参阅 [info 状态表](https://lbs.amap.com/api/webservice/guide/tools/info)|
|geocodes|地理编码信息列表|结果对象列表，包括下述字段：|
|country|国家|国内地址默认返回中国|
|province|地址所在的省份名|例如：北京市。此处需要注意的是，中国的四大直辖市也算作省级单位。|
|city|地址所在的城市名|例如：北京市|
|citycode|城市编码|例如：010|
|district|地址所在的区|例如：朝阳区|
|street|街道|例如：阜通东大街|
|number|门牌|例如：6号|
|adcode|区域编码|例如：110101|
|location|坐标点|经度，纬度|
|level|匹配级别|参见下方的地理编码匹配级别列表|

提示

部分返回值当返回值存在时，将以字符串类型返回；当返回值不存在时，则以数组类型返回。

#### 服务示例

```
https://restapi.amap.com/v3/geocode/geo?address=北京市朝阳区阜通东大街6号&output=XML&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|address|填写结构化地址信息:省份＋城市＋区县＋城镇＋乡村＋街道＋门牌号码|是|
|city|查询城市，可选：城市中文、中文全拼、citycode、adcode|否|

是查询的城市范围，offset(20)为每

示例说明

address 是需要获取坐标的结构化地址，output（XML）用于指定返回数据的格式，Key 是用户请求数据的身份标识，详细可以参考上方的请求参数说明。

## 逆地理编码

#### 逆地理编码 API 服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/geocode/regeo?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|高德Key|用户在高德地图官网 [申请 Web 服务 API 类型 Key](https://lbs.amap.com/dev/)|必填|无|
|location|经纬度坐标|传入内容规则：经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。|必填|无|
|poitype|返回附近 POI 类型|以下内容需要 extensions 参数为 all 时才生效。
逆地理编码在进行坐标解析之后不仅可以返回地址描述，也可以返回经纬度附近符合限定要求的 POI 内容（在 extensions 字段值为 all 时才会返回 POI 内容）。设置 POI 类型参数相当于为上述操作限定要求。参数仅支持传入 POI TYPECODE，可以传入多个 POI TYPECODE，相互之间用“|”分隔。获取 POI TYPECODE 可以参考 [POI 分类码表](https://a.amap.com/lbs/static/amap_3dmap_lite/amap_poicode.zip)|可选|
|radius|搜索半径|radius 取值范围：0~3000，默认值：1000。单位：米|可选|1000|
|extensions|返回结果控制|extensions 参数默认取值是 base，也就是返回基本地址信息；
extensions 参数取值为 all 时会返回基本地址信息、附近 POI 内容、道路信息以及道路交叉口信息。|可选|base|
|roadlevel|道路等级|以下内容需要 extensions 参数为 all 时才生效。
可选值：0，1  当 roadlevel=0时，显示所有道路 ； 当 roadlevel=1时，过滤非主干道路，仅输出主干道路数据|可选|无|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|output|返回数据格式类型|可选输入内容包括：JSON，XML。设置 JSON 返回结果数据将会以 JSON 结构构成；如果设置 XML 返回结果数据将以 XML 结构构成。|可选|JSON|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output 参数设置为 JSON 时有效。|可选|无|
|homeorcorp|是否优化 POI 返回顺序|以下内容需要 extensions 参数为 all 时才生效。
homeorcorp 参数的设置可以影响召回 POI 内容的排序策略，目前提供三个可选参数：
0：不对召回的排序策略进行干扰。
1：综合大数据分析将居家相关的 POI 内容优先返回，即优化返回结果中 pois 字段的poi 顺序。
2：综合大数据分析将公司相关的 POI 内容优先返回，即优化返回结果中 pois 字段的poi 顺序。|可选|0|

#### 返回结果参数说明

逆地理编码的响应结果的格式由请求参数 output 指定。

|名称|含义|规则说明|
|---|---|---|
|status|返回结果状态值|返回值为 0 或 1，0 表示请求失败；1 表示请求成功。|
|info|返回状态说明|当 status 为 0 时，info 会返回具体错误原因，否则返回“OK”。详情可以参考 [info 状态表](https://lbs.amap.com/api/webservice/guide/tools/info)|
|regeocode|逆地理编码列表|返回 regeocode 对象；regeocode 对象包含的数据如下：|
|addressComponent|地址元素列表|
|country|坐标点所在国家名称|例如：中国|
|province|坐标点所在省名称|例如：北京市|
|city|坐标点所在城市名称|请注意：当城市是省直辖县时返回为空，以及城市为北京、上海、天津、重庆四个直辖市时，该字段返回为空；[省直辖县列表](https://lbs.amap.com/faq/webservice/webservice-api/geocoding/43267)|
|citycode|城市编码|例如：010|
|district|坐标点所在区|例如：海淀区|
|adcode|行政区编码|例如：110108|
|township|坐标点所在乡镇/街道（此街道为社区街道，不是道路信息）|例如：燕园街道|
|towncode|乡镇街道编码|例如：110101001000|
|neighborhood|社区信息列表|
|name|社区名称|例如：北京大学|
|type|POI 类型|例如：科教文化服务;学校;高等院校|
|building|楼信息列表|
|name|建筑名称|例如：万达广场|
|type|类型|例如：科教文化服务;学校;高等院校|
|streetNumber|门牌信息列表|
|street|街道名称|例如：中关村北二条|
|number|门牌号|例如：3号|
|location|坐标点|经纬度坐标点：经度，纬度|
|direction|方向|坐标点所处街道方位|
|distance|门牌地址到请求坐标的距离|单位：米|
|seaArea|所属海域信息|例如：渤海|
|businessAreas|经纬度所属商圈列表|
|businessArea|商圈信息|
|location|商圈中心点经纬度|
|name|商圈名称|例如：颐和园|
|id|商圈所在区域的 adcode|例如：朝阳区/海淀区|
|roads|道路信息列表|请求参数 extensions 为 all 时返回如下内容|
|road|道路信息|
|id|道路 id|
|name|道路名称|
|distance|道路到请求坐标的距离|单位：米|
|direction|方位|输入点和此路的相对方位|
|location|坐标点|
|roadinters|道路交叉口列表|请求参数 extensions 为 all 时返回如下内容|
|roadinter|道路交叉口|
|distance|交叉路口到请求坐标的距离|单位：米|
|direction|方位|输入点相对路口的方位|
|location|路口经纬度|
|first\_id|第一条道路 id|
|first\_name|第一条道路名称|
|second\_id|第二条道路 id|
|second\_name|第二条道路名称|
|pois|poi 信息列表|请求参数 extensions 为 all 时返回如下内容|
|poi|poi 信息列表|
|id|poi 的 id|
|name|poi 点名称|
|type|poi 类型|
|tel|电话|
|distance|该 POI 的中心点到请求坐标的距离|单位：米|
|direction|方向|相对于输入点的方位|
|address|poi 地址信息|
|location|坐标点|
|businessarea|poi 所在商圈名称|
|aois|aoi 信息列表|请求参数 extensions 为 all 时返回如下内容|
|aoi|aoi 信息|
|id|所属 aoi 的 id|
|name|所属 aoi 名称|
|adcode|所属 aoi 所在区域编码|
|location|所属 aoi 中心点坐标|
|area|所属 aoi 点面积|单位：平方米|
|distance|输入经纬度是否在 aoi 面之中|0，代表在 aoi 内
其余整数代表距离 AOI 的距离|
|type|所属 aoi 类型|

提示

部分返回值当返回值存在时，将以字符串类型返回；当返回值不存在时，则以数组类型返回。

#### 服务示例

```
https://restapi.amap.com/v3/geocode/regeo?output=xml&location=116.310003,39.991957&key=<用户的key>&radius=1000&extensions=all 
```

|参数|值|备注|必选|
|---|---|---|---|
|location|经纬度坐标|是|
|poitype|支持传入 POI TYPECODE 及名称；支持传入多个 POI 类型，多值间用“|”分隔|
|radius|查询 POI 的半径范围。取值范围：0~3000,单位：米|否|
|extensions|返回结果控制|否|
|roadlevel|可选值：1，当 roadlevel=1时，过滤非主干道路，仅输出主干道路数据|否|

是查询的城市范围，offset(20)为每

说明

location(116.310003,39.991957) 是所需要转换的坐标点经纬度，radius（1000）为返回的附近 POI 的范围，单位：米，extensions(all)为返回的数据内容，output（XML）用于指定返回数据的格式，Key 是高德 Web 服务 Key。详细可以参考上方的请求参数说明。

## 地理编码匹配级别列表

|匹配级别|示例|
|---|---|
|国家|中国|
|省|河北省、北京市|
|市|宁波市|
|区县|北京市朝阳区|
|开发区|亦庄经济开发区|
|乡镇|回龙观镇|
|村庄|三元村|
|热点商圈|上海市黄浦区老西门|
|道路|北京市朝阳区阜通东大街|
|道路交叉路口|北四环西路辅路/善缘街|
|兴趣点|北京市朝阳区奥林匹克公园(南门)|
|门牌号|朝阳区阜通东大街6号|
|单元号|望京西园四区5号楼2单元|
|楼层|保留字段，建议兼容|
|房间|保留字段，建议兼容|
|公交地铁站点|海淀黄庄站 A1西北口|
|门址  （新增）|北京市朝阳区阜荣街10号|
|小巷（新增）|保留字段，建议兼容|
|住宅区（新增）|广西壮族自治区柳州市鱼峰区德润路华润凯旋门|
|未知|未确认级别的 POI|

这篇文档有帮助吗？

完全没有非常有

本页目录

-   [产品介绍](https://lbs.amap.com/api/webservice/guide/api/georegeo#t0 "产品介绍")
-   [适用场景](https://lbs.amap.com/api/webservice/guide/api/georegeo#t1 "适用场景 ") 
-   [使用限制](https://lbs.amap.com/api/webservice/guide/api/georegeo#t2 "使用限制")
-   [使用说明](https://lbs.amap.com/api/webservice/guide/api/georegeo#t3 "使用说明")
-   [地理编码](https://lbs.amap.com/api/webservice/guide/api/georegeo#t4 "地理编码")
-   [地理编码 API 服务地址](https://lbs.amap.com/api/webservice/guide/api/georegeo#s0 "地理编码 API 服务地址")
-   [请求参数](https://lbs.amap.com/api/webservice/guide/api/georegeo#s1 "请求参数")
-   [返回结果参数说明](https://lbs.amap.com/api/webservice/guide/api/georegeo#s2 "返回结果参数说明")
-   [服务示例](https://lbs.amap.com/api/webservice/guide/api/georegeo#s3 "服务示例")
-   [逆地理编码](https://lbs.amap.com/api/webservice/guide/api/georegeo#t5 "逆地理编码")
-   [逆地理编码 API 服务地址](https://lbs.amap.com/api/webservice/guide/api/georegeo#s4 "逆地理编码 API 服务地址")
-   [请求参数](https://lbs.amap.com/api/webservice/guide/api/georegeo#s5 "请求参数")
-   [返回结果参数说明](https://lbs.amap.com/api/webservice/guide/api/georegeo#s6 "返回结果参数说明")
-   [服务示例](https://lbs.amap.com/api/webservice/guide/api/georegeo#s7 "服务示例")
-   [地理编码匹配级别列表](https://lbs.amap.com/api/webservice/guide/api/georegeo#t6 "地理编码匹配级别列表")
