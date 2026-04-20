---
created: 2026-04-20T13:01:56 (UTC +08:00)
tags: [搜索POI 2.0-高级 API 文档-开发指南-Web服务 API]
source: https://lbs.amap.com/api/webservice/guide/api-advanced/newpoisearch
author: 
---

# 搜索POI 2.0-高级 API 文档-开发指南-Web服务 API

> ## Excerpt
> 搜索POI 2.0-高级 API 文档-开发指南-Web服务 API

---
## 产品概述

地点搜索服务2.0是一类 Web API 接口服务；服务提供多种场景的地点搜索能力，包括关键字搜索、周边搜索、多边形区域搜索、ID 搜索。

目前搜索是不支持返回全量数据的，同请求参数翻页查询最多支持获取200条数据

## 功能介绍 

-   关键字搜索：开发者可通过文本关键字搜索地点信息，文本可以是结构化地址，例如：北京市朝阳区望京阜荣街10号；也可以是 POI 名称，例如：首开广场；
    
-   周边搜索：开发者可设置圆心和半径，搜索圆形区域内的地点信息；
    
-   多边形区域搜索：开发者可设置首尾连接的几何点组成多边形区域，搜索坐标对应多边形内的地点信息；
    
-   ID搜索：开发者可通过已知的地点 ID（POI ID）搜索对应地点信息，建议结合输入提示接口使用。
    

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

## 关键字搜索

#### 关键字搜索 API 服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v5/place/text?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|高德Key|用户在高德地图官网 [申请 Web 服务 API 类型Key](https://lbs.amap.com/dev/)|必填|无|
|keywords|地点关键字|需要被检索的地点文本信息。
只支持一个关键字 ，文本总长度不可超过80字符|必填（keyword 或者 types 二选一必填）|无|
|types|指定地点类型|地点文本搜索接口支持按照设定的 POI 类型限定地点搜索结果；地点类型与 poi typecode 是同类内容，可以传入多个 poi typecode，相互之间用“|”分隔，内容可以参考 [POI 分类码表](https://lbs.amap.com/api/webservice/download)；地点（POI）列表的排序会按照高德搜索能力进行综合权重排序；|可选（keyword 或者 types 二选一必填）|
|region|搜索区划|增加指定区域内数据召回权重，如需严格限制召回数据在区域内，请搭配使用 city\_limit 参数，可输入 citycode，adcode，cityname；cityname 仅支持城市级别和中文，如“北京市”。|可选|无，默认全国范围内搜索|
|city\_limit|指定城市数据召回限制|可选值：true/false
为 true 时，仅召回 region 对应区域内数据。|可选|false|
|show\_fields|返回结果控制|show\_fields 用来筛选 response 结果中可选字段。show\_fields 的使用需要遵循如下规则：
1、具体可指定返回的字段类请见下方返回结果说明中的“show\_fields”内字段类型；
2、多个字段间采用“,”进行分割；
3、show\_fields 未设置时，只返回基础信息类内字段。|可选|空|
|page\_size|当前分页展示的数据条数|page\_size 的取值1-25|可选|page\_size 默认为10|
|page\_num|请求第几分页|请求第几分页|可选|page\_num 默认为1|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|output|返回结果格式类型|默认格式为 json，目前只支持 json 格式；|可选|json|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output 参数设置为 JSON 时有效。|可选|无|

#### 服务示例

```
https://restapi.amap.com/v5/place/text?keywords=北京大学&types=141201&region=北京市&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|keywords|地点关键字，需要被检索的地点文本信息
只支持一个关键字 ，文本总长度不可超过80字符|keyword 或者 types 二选一|
|types|指定地点类型,地点文本搜索接口支持按照设定的 POI 类型限定地点搜索结果；地点类型与 poi typecode 是同类内容，可以传入多个 poi typecode，相互之间用“|”分隔，内容可以参考 [POI 分类码表](https://lbs.amap.com/api/webservice/download)；地点（POI）列表的排序会按照高德搜索能力进行综合权重排序；|
|region|搜索区划,增加指定区域内数据召回权重，如需严格限制召回数据在区域内，请搭配使用 city\_limit 参数，可输入 citycode，adcode，cityname；cityname 仅支持城市级别和中文，如“北京市”。|可选|

是查询的城市范围，offset(20)为每

#### 返回结果

|名称|类型|说明|
|---|---|---|
|status|string|本次 API 访问状态，如果成功返回1，如果失败返回0。|
|info|string|访问状态值的说明，如果成功返回"ok"，失败返回错误原因，具体见 [错误码说明](https://lbs.amap.com/api/webservice/guide/tools/info)。|
|infocode|string|返回状态说明,10000代表正确,详情参阅info状态表|
|count|string|单次请求返回的实际 poi 点的个数|
|pois|object|返回的 poi 完整集合|
|poi|单个 poi 内包含的完整返回数据|
|name|string|poi 名称|
|id|string|poi 唯一标识|
|parent|string|父 POI 的 ID，当前 POI 如果有父 POI，则返回父 POI 的 ID。可能为空|
|distance|string|离中心点距离，单位米；仅在周边搜索的时候有值返回|
|location|string|poi 经纬度|
|type|string|poi 所属类型|
|typecode|string|poi 分类编码|
|pname|string|poi 所属省份|
|cityname|string|poi 所属城市|
|adname|string|poi 所属区县|
|address|string|poi 详细地址|
|pcode|string|poi 所属省份编码|
|adcode|string|poi 所属区域编码|
|citycode|string|poi 所属城市编码|
|注意以下字段如需返回需要通过“show\_fields”进行参数类设置。|
|children|object|设置后返回子 POI 信息|
|id|string|子 poi 唯一标识|
|name|string|子 poi 名称|
|location|string|子 poi 经纬度|
|address|string|子 poi 详细地址|
|subtype|string|子 poi 所属类型|
|typecode|string|子 poi 分类编码|
|sname|string|子 poi 分类信息|
|business|object|设置后返回 poi 商业信息|
|business\_area|string|poi 所属商圈|
|opentime\_today|string|poi 今日营业时间，如 08:30-17:30 08:30-09:00 12:00-13:30 09:00-13:00|
|opentime\_week|string|poi 营业时间描述，如 周一至周五:08:30-17:30(延时服务时间:08:30-09:00；12:00-13:30)；周六延时服务时间:09:00-13:00(法定节假日除外)|
|tel|string|poi 的联系电话|
|tag|string|poi 特色内容，目前仅在美食poi下返回|
|rating|string|poi 评分，目前仅在餐饮、酒店、景点、影院类 POI 下返回|
|cost|string|poi 人均消费，目前仅在餐饮、酒店、景点、影院类 POI 下返回|
|parking\_type|string|停车场类型（地下、地面、路边），目前仅在停车场类 POI 下返回|
|alias|string|poi 的别名，无别名时不返回|
|keytag|string|poi 标识，用于确认poi信息类型|
|rectag|string|用于再次确认信息类型|
|indoor|object|设置后返回室内相关信息|
|indoor\_map|string|是否有室内地图标志，1为有，0为没有|
|cpid|string|如果当前 POI 为建筑物类 POI，则 cpid 为自身 POI ID；如果当前 POI 为商铺类 POI，则 cpid 为其所在建筑物的 POI ID。
indoor\_map 为0时不返回|
|floor|string|楼层索引，一般会用数字表示，例如8；indoor\_map 为0时不返回|
|truefloor|string|所在楼层，一般会带有字母，例如F8；indoor\_map 为0时不返回|
|navi|object|设置后返回导航位置相关信息|
|navi\_poiid|string|poi 对应的导航引导点坐标。大型面状 POI 的导航引导点，一般为各类出入口，方便结合导航、路线规划等服务使用|
|entr\_location|string|poi 的入口经纬度坐标|
|exit\_location|string|poi 的出口经纬度坐标|
|gridcode|string|poi 的地理格 id|
|photos|object|设置后返回 poi 图片相关信息|
|title|string|poi 的图片介绍|
|url|string|poi 图片的下载链接|

## 周边搜索

#### 周边搜索 API 服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v5/place/around?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|高德Key|用户在高德地图官网 [申请 Web 服务 API 类型 Key](https://lbs.amap.com/dev/)|必填|无|
|keywords|地点关键字|需要被检索的地点文本信息。
只支持一个关键字 ，文本总长度不可超过80字符|可选|无|
|types|指定地点类型|地点文本搜索接口支持按照设定的POI类型限定地点搜索结果；地点类型与 poi typecode 是同类内容，可以传入多个 poi typecode，相互之间用“|”分隔，内容可以参考 [POI 分类码表](https://lbs.amap.com/api/webservice/download)；地点（POI）列表的排序会按照高德搜索能力进行综合权重排序；
当 keywords 和 types 均为空的时候，默认指定 types 为050000（餐饮服务）、070000（生活服务）、120000（商务住宅）|可选|
|location|中心点坐标|圆形区域检索中心点，不支持多个点。经度和纬度用","分割，经度在前，纬度在后，经纬度小数点后不得超过6位|必填|无|
|radius|搜索半径|取值范围:0-50000，大于50000时按默认值，单位：米|可选|5000|
|sortrule|排序规则|规定返回结果的排序规则。
按距离排序：distance；综合排序：weight
sortrule参数设置距离排序在只传keywords参数的情况下不生效。|可选|distance|
|region|搜索区划|增加指定区域内数据召回权重，如需严格限制召回数据在区域内，请搭配使用 city\_limit 参数，可输入行政区划名或对应 citycode 或 adcode|可选|无，默认全国范围内搜索|
|city\_limit|指定城市数据召回限制|可选值：true/false
为 true 时，仅召回 region 对应区域内数据|可选|false|
|show\_fields|返回结果控制|show\_fields 用来筛选 response 结果中可选字段。show\_fields 的使用需要遵循如下规则：
1、具体可指定返回的字段类请见下方返回结果说明中的“show\_fields”内字段类型；
2、多个字段间采用“,”进行分割；
3、show\_fields 未设置时，只返回基础信息类内字段。|可选|空|
|page\_size|当前分页展示的数据条数|page\_size 的取值1-25|可选|page\_size 默认为 10|
|page\_num|请求第几分页|请求第几分页|可选|page\_num 默认为 1|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|output|返回结果格式类型|默认格式为 json，目前只支持 json 格式；|可选|json|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output 参数设置为 JSON 时有效。|可选|无|

#### 服务示例

```
https://restapi.amap.com/v5/place/around?location=116.473168,39.993015&radius=10000&types=011100&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|location|中心点坐标
圆形区域检索中心点，不支持多个点。经度和纬度用","分割，经度在前，纬度在后，经纬度小数点后不得超过6位|是|
|radius|搜索半径
取值范围:0-50000，大于50000时按默认值，单位：米|可选|
|types|指定地点类型,地点文本搜索接口支持按照设定的POI类型限定地点搜索结果；地点类型与 poi typecode 是同类内容，可以传入多个poi typecode，相互之间用“|”分隔，内容可以参考 [POI 分类码表](https://lbs.amap.com/api/webservice/download)；地点（POI）列表的排序会按照高德搜索能力进行综合权重排序；|

是查询的城市范围，offset(20)为每

#### 返回结果

|名称|类型|说明|
|---|---|---|
|status|string|本次 API 访问状态，如果成功返回1，如果失败返回0。|
|info|string|访问状态值的说明，如果成功返回"ok"，失败返回错误原因，具体见 [错误码说明](https://lbs.amap.com/api/webservice/guide/tools/info)。|
|infocode|string|返回状态说明,10000代表正确,详情参阅 info 状态表|
|count|string|单次请求返回的实际 poi 点的个数|
|pois|object|返回的 poi 完整集合|
|poi|单个 poi 内包含的完整返回数据|
|name|string|poi 名称|
|id|string|poi 唯一标识|
|parent|string|父 POI 的 ID，当前 POI 如果有父 POI，则返回父 POI 的 ID。可能为空|
|location|string|poi 经纬度|
|distance|string|离中心点距离，单位米|
|type|string|poi 所属类型|
|typecode|string|poi 分类编码|
|pname|string|poi 所属省份|
|cityname|string|poi 所属城市|
|adname|string|poi 所属区县|
|address|string|poi 详细地址|
|pcode|string|poi 所属省份编码|
|adcode|string|poi 所属区域编码|
|citycode|string|poi 所属城市编码|
|注意以下字段如需返回需要通过“show\_fields”进行参数类设置。|
|children|object|设置后返回子 POI 信息|
|id|string|子 poi 唯一标识|
|name|string|子 poi 名称|
|location|string|子 poi 经纬度|
|address|string|子 poi 详细地址|
|subtype|string|子 poi 所属类型|
|typecode|string|子 poi 分类编码|
|sname|string|子 poi 分类信息|
|business|object|设置后返回 poi 商业信息|
|business\_area|string|poi 所属商圈|
|opentime\_today|string|poi 今日营业时间，如 08:30-17:30 08:30-09:00 12:00-13:30 09:00-13:00|
|opentime\_week|string|poi 营业时间描述，如 周一至周五:08:30-17:30(延时服务时间:08:30-09:00；12:00-13:30)；周六延时服务时间:09:00-13:00(法定节假日除外)|
|tel|string|poi 的联系电话|
|tag|string|poi 特色内容，目前仅在美食 poi 下返回|
|rating|string|poi 评分，目前仅在餐饮、酒店、景点、影院类 POI 下返回|
|cost|string|poi 人均消费，目前仅在餐饮、酒店、景点、影院类 POI 下返回|
|parking\_type|string|停车场类型（地下、地面、路边），目前仅在停车场类 POI 下返回|
|alias|string|poi 的别名，无别名时不返回|
|keytag|string|poi 标识，用于确认poi信息类型|
|rectag|string|用于再次确认信息类型|
|indoor|object|设置后返回室内相关信息|
|indoor\_map|string|是否有室内地图标志，1为有，0为没有|
|cpid|string|如果当前 POI 为建筑物类 POI，则 cpid 为自身 POI ID；如果当前 POI 为商铺类 POI，则 cpid 为其所在建筑物的 POI ID。
indoor\_map 为0时不返回|
|floor|string|楼层索引，一般会用数字表示，例如8；indoor\_map 为0时不返回|
|truefloor|string|所在楼层，一般会带有字母，例如F8；indoor\_map 为0时不返回|
|navi|object|设置后返回导航位置相关信息|
|navi\_poiid|string|poi 对应的导航引导点坐标。大型面状 POI 的导航引导点，一般为各类出入口，方便结合导航、路线规划等服务使用|
|entr\_location|string|poi 的入口经纬度坐标|
|exit\_location|string|poi 的出口经纬度坐标|
|gridcode|string|poi 的地理格 id|
|photos|object|设置后返回 poi 图片相关信息|
|title|string|poi 的图片介绍|
|url|string|poi 图片的下载链接|

## 多边形区域搜索

#### 多边形区域搜索 API 服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v5/place/polygon?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|高德Key|用户在高德地图官网 [申请 Web 服务 API 类型 Key](https://lbs.amap.com/dev/)|必填|无|
|polygon|多边形区域|多个坐标对集合，坐标对用"|"分割。多边形为矩形时，可传入左上右下两顶点坐标对；其他情况下首尾坐标对需相同。|必填|
|keywords|地点关键字|需要被检索的地点文本信息。
只支持一个关键字 ，文本总长度不可超过80字符|可选|无|
|types|指定地点类型|地点文本搜索接口支持按照设定的 POI 类型限定地点搜索结果；地点类型与 poi typecode 是同类内容，可以传入多个 poi typecode，相互之间用“|”分隔，内容可以参考 [POI 分类码表](https://lbs.amap.com/api/webservice/download)；地点（POI）列表的排序会按照高德搜索能力进行综合权重排序；|可选|
|show\_fields|返回结果控制|show\_fields 用来筛选 response 结果中可选字段。show\_fields 的使用需要遵循如下规则：
1、具体可指定返回的字段类请见下方返回结果说明中的“show\_fields”内字段类型；
2、多个字段间采用“,”进行分割；
3、show\_fields 未设置时，只返回基础信息类内字段。|可选|空|
|page\_size|当前分页展示的数据条数|page\_size 的取值1-25|可选|page\_size 默认为10|
|page\_num|请求第几分页|请求第几分页|可选|page\_num 默认为1|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|output|返回结果格式类型|默认格式为 json，目前只支持 json 格式；|可选|json|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output 参数设置为 JSON 时有效。|可选|无|

#### 服务示例

```
https://restapi.amap.com/v5/place/polygon?polygon=116.460988,40.006919|116.48231,40.007381|116.47516,39.99713|116.472596,39.985227|116.45669,39.984989|116.460988,40.006919&keywords=肯德基&types=050301&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|polygon|多边形区域,多个坐标对集合，坐标对用"|"分割。多边形为矩形时，可传入左上右下两顶点坐标对；其他情况下首尾坐标对需相同|
|keywords|地点关键字,需要被检索的地点文本信息
只支持一个关键字|可选|
|types|指定地点类型,地点文本搜索接口支持按照设定的 POI 类型限定地点搜索结果；地点类型与 poi typecode 是同类内容，可以传入多个 poi typecode，相互之间用“|”分隔，内容可以参考 [POI 分类码表](https://lbs.amap.com/api/webservice/download)；地点（POI）列表的排序会按照高德搜索能力进行综合权重排序；|

是查询的城市范围，offset(20)为每

#### 返回结果

|名称|类型|说明|
|---|---|---|
|status|string|本次 API 访问状态，如果成功返回1，如果失败返回0。|
|info|string|访问状态值的说明，如果成功返回"ok"，失败返回错误原因，具体见 [错误码说明](https://lbs.amap.com/api/webservice/guide/tools/info)。|
|infocode|string|返回状态说明,10000代表正确,详情参阅 info 状态表|
|count|string|单次请求返回的实际 poi 点的个数|
|pois|object|返回的 poi 完整集合|
|poi|单个 poi 内包含的完整返回数据|
|name|string|poi 名称|
|id|string|poi 唯一标识|
|parent|string|父 POI 的 ID，当前 POI 如果有父 POI，则返回父 POI 的 ID。可能为空|
|distance|string|离中心点距离，单位米；仅在周边搜索的时候有值返回|
|location|string|poi 经纬度|
|type|string|poi 所属类型|
|typecode|string|poi 分类编码|
|pname|string|poi 所属省份|
|cityname|string|poi 所属城市|
|adname|string|poi所属区县|
|address|string|poi 详细地址|
|pcode|string|poi 所属省份编码|
|adcode|string|poi 所属区域编码|
|citycode|string|poi 所属城市编码|
|注意以下字段如需返回需要通过“show\_fields”进行参数类设置。|
|children|object|设置后返回子 POI 信息|
|id|string|子 poi 唯一标识|
|name|string|子 poi 名称|
|location|string|子 poi 经纬度|
|address|string|子 poi 详细地址|
|subtype|string|子 poi 所属类型|
|typecode|string|子 poi 分类编码|
|business|object|设置后返回子 POI 信息|
|business\_area|string|poi 所属商圈|
|tel|string|poi 的联系电话|
|tag|string|poi 特色内容，目前仅在美食 poi 下返回|
|rating|string|poi 评分，目前仅在餐饮、酒店、景点、影院类 POI 下返回|
|cost|string|poi 人均消费，目前仅在餐饮、酒店、景点、影院类 POI 下返回|
|parking\_type|string|停车场类型（地下、地面、路边），目前仅在停车场类 POI 下返回|
|alias|string|poi 的别名，无别名时不返回|
|indoor|object|设置后返回室内相关信息|
|indoor\_map|string|是否有室内地图标志，1为有，0为没有|
|cpid|string|如果当前 POI 为建筑物类 POI，则 cpid 为自身 POI ID；如果当前 POI 为商铺类 POI，则 cpid 为其所在建筑物的 POI ID。
indoor\_map 为0时不返回|
|floor|string|楼层索引，一般会用数字表示，例如8；indoor\_map 为0时不返回|
|truefloor|string|所在楼层，一般会带有字母，例如F8；indoor\_map 为0时不返回|
|navi|object|设置后返回导航位置相关信息|
|navi\_poiid|string|poi 对应的导航引导点坐标。大型面状 POI 的导航引导点，一般为各类出入口，方便结合导航、路线规划等服务使用|
|entr\_location|string|poi 的入口经纬度坐标|
|exit\_location|string|poi 的出口经纬度坐标|
|gridcode|string|poi 的地理格 id|
|photos|object|设置后返回 poi 图片相关信息|
|title|string|poi 的图片介绍|
|url|string|poi 图片的下载链接|

## ID搜索

#### ID搜索 API 服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v5/place/detail?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|高德Key|用户在高德地图官网 [申请 Web 服务 API 类型 Key](https://lbs.amap.com/dev/)|必填|无|
|id|poi唯一标识|最多可以传入10个 id，多个 id 之间用“|”分隔。|必填|
|show\_fields|返回结果控制|show\_fields 用来筛选 response 结果中可选字段。show\_fields 的使用需要遵循如下规则：
1、具体可指定返回的字段类请见下方返回结果说明中的“show\_fields”内字段类型；
2、多个字段间采用“,”进行分割；
3、show\_fields未设置时，只返回基础信息类内字段。|可选|空|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|output|返回结果格式类型|默认格式为 json，目前只支持 json 格式；|可选|json|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output 参数设置为 JSON 时有效。|可选|无|

#### 服务示例

```
https://restapi.amap.com/v5/place/detail?id=B000A7BM4H|B0FFKEPXS2&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|id|poi 唯一标识,最多可以传入10个 id，多个 id 之间用“|”分隔。|

是查询的城市范围，offset(20)为每

#### 返回结果

|名称|类型|说明|
|---|---|---|
|status|string|本次 API 访问状态，如果成功返回1，如果失败返回0。|
|info|string|访问状态值的说明，如果成功返回"ok"，失败返回错误原因，具体见 [错误码说明](https://lbs.amap.com/api/webservice/guide/tools/info)。|
|infocode|string|返回状态说明,10000代表正确,详情参阅 info 状态表|
|pois|object|完整的 POI 列表|
|poi|object|单个 POI 返回的数据字段|
|name|string|poi 名称|
|id|string|poi 唯一标识|
|parent|string|父 POI 的 ID，当前 POI 如果有父 POI，则返回父 POI 的 ID。可能为空|
|distance|string|离中心点距离，单位米；仅在周边搜索的时候有值返回|
|location|string|poi 经纬度|
|type|string|poi 所属类型|
|typecode|string|poi 分类编码|
|pname|string|poi 所属省份|
|cityname|string|poi 所属城市|
|adname|string|poi 所属区县|
|address|string|poi 详细地址|
|pcode|string|poi 所属省份编码|
|adcode|string|poi 所属区域编码|
|citycode|string|poi 所属城市编码|
|atag|string|poi 类目，例如：985大学/粤菜|
|注意以下字段如需返回需要通过“show\_fields”进行参数类设置。|
|children|object|设置后返回子 POI 信息|
|id|string|子 poi唯一标识|
|name|string|子 poi 名称|
|location|string|子 poi 经纬度|
|address|string|子 poi 详细地址|
|subtype|string|子 poi 所属类型|
|typecode|string|子 poi 分类编码|
|business|object|设置后返回子 POI 信息|
|business\_area|string|poi 所属商圈|
|tel|string|poi 的联系电话|
|tag|string|poi 特色内容，目前仅在美食 poi 下返回|
|rating|string|poi 评分，目前仅在餐饮、酒店、景点、影院类 POI 下返回|
|cost|string|poi 人均消费，目前仅在餐饮、酒店、景点、影院类 POI 下返回|
|parking\_type|string|停车场类型（地下、地面、路边），目前仅在停车场类 POI 下返回|
|alias|string|poi 的别名，无别名时不返回|
|indoor|object|设置后返回室内相关信息|
|indoor\_map|string|是否有室内地图标志，1为有，0为没有|
|cpid|string|如果当前 POI 为建筑物类 POI，则 cpid 为自身 POI ID；如果当前 POI 为商铺类 POI，则 cpid 为其所在建筑物的 POI ID。
indoor\_map 为0时不返回|
|floor|string|楼层索引，一般会用数字表示，例如8；indoor\_map 为0时不返回|
|truefloor|string|所在楼层，一般会带有字母，例如F8；indoor\_map 为0时不返回|
|navi|object|设置后返回导航位置相关信息|
|navi\_poiid|string|poi 对应的导航引导点坐标。大型面状 POI 的导航引导点，一般为各类出入口，方便结合导航、路线规划等服务使用|
|entr\_location|string|poi 的入口经纬度坐标|
|exit\_location|string|poi 的出口经纬度坐标|
|gridcode|string|poi 的地理格 id|
|photos|object|设置后返回 poi 图片相关信息|
|title|string|poi 的图片介绍|
|url|string|poi 图片的下载链接|
