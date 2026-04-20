---
created: 2026-04-20T13:01:44 (UTC +08:00)
tags: [搜索POI-高级 API 文档-开发指南-Web服务 API]
source: https://lbs.amap.com/api/webservice/guide/api-advanced/search
author: 
---

# 搜索POI-高级 API 文档-开发指南-Web服务 API

> ## Excerpt
> 搜索POI-高级 API 文档-开发指南-Web服务 API

---
## 产品介绍

搜索服务 API 是一类简单的 HTTP 接口，提供多种查询 POI 信息的能力，其中包括关键字搜索、周边搜索、多边形搜索、ID 查询四种筛选机制。

目前搜索是不支持返回全量数据的，同请求参数翻页查询最多支持获取200条数据

注意

在此接口之中，您可以通过 city&citylimit 参数指定希望搜索的城市或区县。而 city 参数能够接收 citycode 和 adcode，citycode 仅能精确到城市，而 adcode 却能够精确到区县。

例如：北京，citycode：010，adcode：110000

北京-海淀区，citycode：010，adcode：110108

故使用 citycode 仅能在北京范围内搜索，而 adcode 能够指定在海淀区搜索。

综上所述，为了您查询的精确，我们强烈建议您使用 adcode。

## 适用场景    

-   关键字搜索：通过用 POI 的关键字进行条件搜索，例如：肯德基、朝阳公园等；同时支持设置 POI 类型搜索，例如：银行
    
-   周边搜索：在用户传入经纬度坐标点附近，在设定的范围内，按照关键字或 POI 类型搜索；
    
-   多边形搜索：在多边形区域内进行搜索
    
-   ID 查询：通过 POI ID，查询某个 POI 详情，建议可同输入提示 API 配合使用
    

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

## 关键字搜索

#### 关键字搜索 API 服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/place/text?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网 [申请 Web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|keywords|查询关键字|规则：  只支持一个关键字 
若不指定 city，并且搜索的为泛词（例如“美食”）的情况下，返回的内容为城市列表以及此城市内有多少结果符合要求。|必填（keyword 或者 types 二选一必填）|无|
|types|查询 POI 类型|可选值：分类代码 或 汉字（若用汉字，请严格按照附件之中的汉字填写）
规则： 多个关键字用“|”分割
分类代码由六位数字组成，一共分为三个部分，前两个数字代表大类；中间两个数字代表中类；最后两个数字代表小类。
若指定了某个大类，则所属的中类、小类都会被显示。
例如：010000为汽车服务（大类）
          010100为加油站（中类）
          010101为中国石化（小类）
          010900为汽车租赁（中类）
          010901为汽车租赁还车（小类）
当指定010000，则010100等中类、010101等小类会被包含，当指定010900，则010901等小类会被包含。
注意：返回结果可能会包含中小类POI，但不保证包含所有，如需更精确的信息，推荐输入小类或缩小范围查询
下载 [POI 分类编码和城市编码表](https://lbs.amap.com/api/webservice/download)
若不指定 city，返回的内容为城市列表以及此城市内有多少结果符合要求。|必填（keyword 或者 types 二选一必填）|
|city|查询城市|可选值：城市中文、citycode、adcode
如：北京/010/110000
填入此参数后，会尽量优先返回此城市数据，但是不一定仅局限此城市结果，若仅需要某个城市数据请调用 citylimit 参数。
如：在深圳市搜天安门，返回北京天安门结果。|可选|无（全国范围内搜索）|
|citylimit|仅返回指定城市数据|可选值：true/false|可选|false|
|children|是否按照层级展示子 POI 数据|可选值：children=1
当为0的时候，子 POI 都会显示。
当为1的时候，子 POI 会归类到父 POI 之中。
在 extensions=all 或者为空时生效|可选|0|
|offset|每页记录数据|强烈建议不超过25，若超过25可能造成访问报错|可选|20|
|page|当前页数|当前页数|可选|1|
|extensions|返回结果控制|此项默认返回基本地址信息；取值为 all 返回地址信息、附近 POI、道路以及道路交叉口信息。|可选|base|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output=JSON 时有效|可选|无|

#### 返回结果参数说明

关键字搜索的响应结果的格式由请求参数 output 指定。

|名称|含义|规则说明|
|---|---|---|
|status|结果状态值，值为0或1|0：请求失败；1：请求成功|
|info|返回状态说明|status 为0时，info 返回错误原因，否则返回“OK”。详情参阅 [info状态表](https://lbs.amap.com/api/webservice/info/)|
|count|搜索方案数目|
|suggestion|城市建议列表|当搜索的文本关键字在限定城市中没有返回时会返回建议城市列表；|
|keywords|关键字|
|cities|城市列表|
|name|名称|
|num|该城市包含此关键字的个数|
|citycode|该城市的 citycode|
|adcode|该城市的 adcode|
|pois|搜索 POI 信息列表|
|poi|POI 信息|
|id|唯一 ID|
|parent|父 POI 的 ID|当前 POI 如果有父 POI，则返回父 POI 的 ID。可能为空|
|name|名称|
|type|兴趣点类型|顺序为大类、中类、小类
例如：餐饮服务;中餐厅;特色/地方风味餐厅|
|typecode|兴趣点类型编码|例如：050118|
|biz\_type|行业类型|
|address|地址|东四环中路189号百盛北门|
|location|经纬度|格式：X,Y|
|distance|离中心点距离|单位：米；仅在周边搜索的时候有值返回|
|tel|POI的电话|
|postcode|邮编|extensions=all时返回|
|website|POI 的网址|extensions=all时返回|
|email|POI 的电子邮箱|extensions=all时返回|
|pcode|POI 所在省份编码|extensions=all时返回|
|pname|POI 所在省份名称|若是直辖市的时候，此处直接显示市名，例如北京市|
|citycode|城市编码|extensions=all 时返回|
|cityname|城市名|若是直辖市的时候，此处直接显示市名，例如北京市|
|adcode|区域编码|extensions=all 时返回|
|adname|区域名称|区县级别的返回，例如朝阳区|
|entr\_location|POI 的入口经纬度|extensions=all 时返回，也可用作于 POI 的到达点；|
|exit\_location|POI 的出口经纬度|目前不会返回内容；|
|navi\_poiid|POI 导航 id|extensions=all 时返回|
|gridcode|地理格ID|extensions=all 时返回|
|alias|别名|extensions=all 时返回|
|parking\_type|停车场类型|仅在停车场类型 POI 的时候显示该字段
展示停车场类型，包括：地下、地面、路边
 extensions=all的时候显示|
|tag|该 POI 的特色内容|主要出现在美食类 POI 中，代表特色菜
例如“烤鱼,麻辣香锅,老干妈回锅肉”
extensions=all 时返回|
|indoor\_map|是否有室内地图标志|1，表示有室内相关数据
0，代表没有室内相关数据
 extensions=all 时返回|
|indoor\_data|室内地图相关数据|当 indoor\_map=0时，字段为空
 extensions=all 时返回|
|cpid|当前 POI 的父级 POI|如果当前 POI 为建筑物类 POI，则 cpid 为自身 POI ID；如果当前 POI 为商铺类 POI，则 cpid 为其所在建筑物的 POI ID|
|floor|楼层索引|一般会用数字表示，例如8|
|truefloor|所在楼层|一般会带有字母，例如F8|
|groupbuy\_num|团购数据|此字段逐渐废弃|
|business\_area|所属商圈|extensions=all 时返回|
|atag|类目|例如：985大学/粤菜。现状仅ID查询返回|
|discount\_num|优惠信息数目|此字段逐渐废弃|
|biz\_ext|深度信息|extensions=all 时返回|
|rating|评分|仅存在于餐饮、酒店、景点、影院类 POI 之下|
|cost|人均消费|仅存在于餐饮、酒店、景点、影院类 POI 之下|
|meal\_ordering|是否可订餐|仅存在于餐饮相关 POI 之下（此字段逐渐废弃）|
|seat\_ordering|是否可选座|仅存在于影院相关 POI 之下（此字段逐渐废弃）|
|ticket\_ordering|是否可订票|仅存在于景点相关 POI 之下（此字段逐渐废弃）|
|hotel\_ordering|是否可以订房|仅存在于酒店相关 POI 之下（此字段逐渐废弃）|
|photos|照片相关信息|extensions=all 时返回|
|title|图片介绍|
|url|具体链接|

提示

部分返回值当返回值存在时，将以字符串类型返回；当返回值不存在时，则以数组类型返回。

#### 服务示例

```
https://restapi.amap.com/v3/place/text?keywords=北京大学&city=beijing&offset=20&page=1&key=<用户的key>&extensions=all 
```

|参数|值|备注|必选|
|---|---|---|---|
|keywords|查询关键词|是|
|types|查询 POI 类型|否|
|city|城市名，可填：城市中文、中文全拼、citycode 或 adcode|否|
|children|按照层级展示子 POI 数据|否|
|offset|每页记录数据|否|
|page|当前页数|否|
|extensions|base 返回基本地址信息；取值为 all 返回地址信息、附近 POI、道路以及道路交叉口信息|否|

是查询的城市范围，offset(20)为每

说明：keywords(北京大学)是需要查询的关键词，city(北京)是查询的城市范围，offset(20)为每页返回的 POI 数量，page(1)为当前页数，extensions(all)为返回信息控制参数，key 是用户请求数据的身份标识。

## 周边搜索

#### 周边搜索API服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/place/around?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网 [申请 Web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|location|中心点坐标|规则： 经度和纬度用","分割，经度在前，纬度在后，经纬度小数点后不得超过6位|必填|无|
|keywords|查询关键字|规则：  只支持一个关键字|可选|无|
|types|查询POI类型|多个类型用“|”分割；
可选值：分类代码 或 汉字 （若用汉字，请严格按照附件之中的汉字填写） 
分类代码由六位数字组成，一共分为三个部分，前两个数字代表大类；中间两个数字代表中类；最后两个数字代表小类。
若指定了某个大类，则所属的中类、小类都会被显示。
例如：010000为汽车服务（大类）
          010100为加油站（中类）
          010101为中国石化（小类）
          010900为汽车租赁（中类）
          010901为汽车租赁还车（小类）
当指定010000，则010100等中类、010101等小类会被包含。
当指定010900，则010901等小类会被包含
注意：返回结果可能会包含中小类POI，但不保证包含所有，如需更精确的信息，推荐输入小类或缩小范围查询
[下载 POI 分类编码和城市编码表](https://lbs.amap.com/api/webservice/download)        
当 keywords 和 types 均为空的时候，默认指定 types 为050000（餐饮服务）、070000（生活服务）、120000（商务住宅）|
|city|查询城市|可选值：城市中文、中文全拼、citycode、adcode
如：北京/beijing/010/110000
当用户指定的经纬度和 city 出现冲突，若范围内有用户指定 city 的数据，则返回相关数据，否则返回为空。
如：经纬度指定石家庄，而 city 却指定天津，若搜索范围内有天津的数据则返回相关数据，否则返回为空。|可选|无（全国范围内搜索）|
|radius|查询半径|取值范围:0-50000。规则：大于50000按默认值，单位：米|可选|5000|
|sortrule|排序规则|规定返回结果的排序规则。
按距离排序：distance；综合排序：weight
sortrule参数设置距离排序在只传keywords参数的情况下不生效。|可选|distance|
|offset|每页记录数据|强烈建议不超过25，若超过25可能造成访问报错|可选|20|
|page|当前页数|当前页数|可选|1|
|extensions|返回结果控制|此项默认返回基本地址信息；取值为all返回地址信息、附近 POI、道路以及道路交叉口信息。|可选|base|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output=JSON 时有效|可选|无|

#### 返回结果参数说明

周边搜索搜索的响应结果的格式由请求参数 output 指定，返回结果见 [关键字搜索](https://lbs.amap.com/api/webservice/guide/api-advanced/search#limit)

#### 服务示例

```
https://restapi.amap.com/v3/place/around?key=<用户的key>&location=116.473168,39.993015&radius=10000&types=011100  
```

|参数|值|备注|必选|
|---|---|---|---|
|location|中心点坐标|是|
|keywords|查询关键词|否|
|types|查询 POI 类型|否|
|radius|查询半径|否|
|offset|每页记录数据|否|
|page|当前页数|否|
|extensions|返回结果控制|否|

是查询的城市范围，offset(20)为每

说明：location(116.481488,39.990464)是需要查询的中心点，types(050301)为搜索的返回 POI 数据类型，extensions(all)为返回的数据内容，key 是用户请求数据的身份标识。

## 多边形搜索

#### 多边形搜索API服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/place/polygon?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网 [申请 Web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|polygon|经纬度坐标对|规则：经度和纬度用","分割，经度在前，纬度在后，坐标对用"|"分割。经纬度小数点后不得超过6位。         多边形为矩形时，可传入左上右下两顶点坐标对；其他情况下首尾坐标对需相同。|必填|
|keywords|查询关键字|规则：  只支持一个关键字|可选|无|
|types|查询 POI 类型|多个类型用“|”分割；
可选值：分类代码 或 汉字 （若用汉字，请严格按照附件之中的汉字填写） 
分类代码由六位数字组成，一共分为三个部分，前两个数字代表大类；中间两个数字代表中类；最后两个数字代表小类。
若指定了某个大类，则所属的中类、小类都会被显示。
例如：010000为汽车服务（大类）
          010100为加油站（中类）
          010101为中国石化（小类）
          010900为汽车租赁（中类）
          010901为汽车租赁还车（小类）
当指定010000，则010100等中类、010101等小类会被包含。
当指定010900，则010901等小类会被包含
注意：返回结果可能会包含中小类POI，但不保证包含所有，如需更精确的信息，推荐输入小类或缩小范围查询
[下载 POI 分类编码和城市编码表](https://lbs.amap.com/api/webservice/download)   
当 keywords 和 types 为空的时候， 我们会默认指定 types 为120000（商务住宅）&150000（交通设施服务）|
|offset|每页记录数据|强烈建议不超过25，若超过25可能造成访问报错|可选|20|
|page|当前页数|当前页数|可选|1|
|extensions|返回结果控制|此项默认返回基本地址信息；取值为all返回地址信息、附近 POI、道路以及道路交叉口信息。|可选|base|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output=JSON 时有效|可选|无|

#### 返回结果参数说明

多边形搜索搜索的响应结果的格式由请求参数 output 指定，返回结果见 [关键字搜索](https://lbs.amap.com/api/webservice/guide/api-advanced/search#limit)

#### 服务示例

```
https://restapi.amap.com/v3/place/polygon?polygon=116.460988,40.006919|116.48231,40.007381|116.47516,39.99713|116.472596,39.985227|116.45669,39.984989|116.460988,40.006919&keywords=kfc&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|polygon|经纬度坐标对，矩形时可传入左上右下两顶点坐标对；其他情况首尾坐标对需相同。|是|
|keywords|查询关键词|否|
|types|查询 POI 类型|否|
|offset|每页记录数据|否|
|page|当前页数|否|
|extensions|返回结果控制|否|

是查询的城市范围，offset(20)为每

说明：polygon(116.460988,40.006919;116.48231,40.007381;116.47516,39.99713;116.472596,39.985227;116.45669,39.984989;116.460988,40.006919)是查询的区域范围，keywords(kfc)为查询的关键字，extensions(all)为返回的数据内容，key 是用户请求数据的身份标识。

## ID查询

#### ID查询搜索API服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v3/place/detail?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网 [申请 Web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|id|AOI 唯一标识|最多可以传入1个 id，传入目标区域的poiid即可|必填|无|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在 output=JSON 时有效|可选|无|

#### 返回结果参数说明

说明

如果未能获取到POI详情，请联系商务并提交[工单](https://console.amap.com/dev/ticket/create/66)申请高级权限

ID 查询搜索的响应结果的格式由请求参数 output 指定，返回结果见 [关键字搜索](https://lbs.amap.com/api/webservice/guide/api-advanced/search#limit)

#### 服务示例

```
https://restapi.amap.com/v3/place/detail?id=B0FFFAB6J2&key=<用户的key>
```

|参数|值|备注|必选|
|---|---|---|---|
|id|兴趣点 ID|是|

是查询的城市范围，offset(20)为每

说明：

ID(B0FFFAB6J2)是查询 POI ID，extensions(all)为返回的数据内容，key 是用户请求数据的身份标识。

## AOI 边界查询

说明

该服务属于高德开放平台高阶服务，您在正式使用前需要通过 [工单](https://console.amap.com/dev/ticket/create/66) 等形式联系我们开通权限。

#### AOI 边界查询 API 服务地址

|URL|请求方式|
|---|---|
|https://restapi.amap.com/v5/aoi/polyline?parameters|GET|

parameters 代表的参数包括必填参数和可选参数。所有参数均使用和号字符(&)进行分隔。下面的列表枚举了这些参数及其使用规则。

#### 请求参数

|参数名|含义|规则说明|是否必须|缺省值|
|---|---|---|---|---|
|key|请求服务权限标识|用户在高德地图官网[申请 Web 服务 API 类型 KEY](https://lbs.amap.com/dev/)|必填|无|
|id|唯一标识|最多可以传入1个 id，传入目标区域的 poiid 即可|必填|无|
|sig|数字签名|请参考 [数字签名获取和使用方法](https://lbs.amap.com/faq/quota-key/key/41181/)|可选|无|
|callback|回调函数|callback 值是用户定义的函数名称，此参数只在output=JSON时有效|可选|无|

#### 返回结果参数说明

注意：返回结果参数仅支持 json。

|参数名|含义|
|---|---|
|status|本次 API 访问状态，如果成功返回0，如果失败返回其他数字。|
|info|访问状态值的说明，如果成功返回"ok"，失败返回错误原因，具体见 [错误码说明](https://lbs.amap.com/api/webservice/guide/tools/info)。|
|aois|aoi 返回的详细数据字段|
|name|aoi 名称，同 poi|
|id|aoi 唯一标识|
|location|aoi 中心点经纬度|
|polyline|边界经纬度坐标串，以“\_”分隔。|
|type|aoi 所属分类|
|typecode|aoi 分类编码|
|pname|aoi 所属省份|
|cityname|aoi 所属城市|
|adname|aoi 所属区域|
|address|aoi 详细地址|
|pcode|aoi 所属省份编码|
|citycode|aoi 所属城市编码|
|adcode|aoi 所属区域编码|

提示

AOI 是指具有面状、区域状特点的 POI，包括但不限于工业园区、学校校区、商圈、住宅小区、景区、火车站、机场等类型的 POI。开发者可以通过结合此数据以及猎鹰轨迹服务中的 [多边形围栏](https://lbs.amap.com/api/track/lieying-kaifa/api/track_fence#t3) 等能力，基于真实地理区域数据对业务进行管理。
