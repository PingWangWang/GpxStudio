---
created: 2026-04-20T13:04:26 (UTC +08:00)
tags: [错误码说明-实用工具-开发指南-Web服务 API]
source: https://lbs.amap.com/api/webservice/guide/tools/info
author: 
---

# 错误码说明-实用工具-开发指南-Web服务 API

> ## Excerpt
> 序号infocodeinfo返回值状态描述问题排查策略110000OK请求正常请求正常210001INVALID_USE

---
|infocode|info返回值|状态描述|问题排查策略|
|---|---|---|---|
|10000|OK|请求正常|请求正常|
|10001|INVALID\_USER\_KEY|key不正确或过期|开发者发起请求时，传入的key不正确或者过期|
|10002|SERVICE\_NOT\_AVAILABLE|没有权限使用相应的服务或者请求接口的路径拼写错误|1.开发者没有权限使用相应的服务，例如：开发者申请了WEB定位功能的key，却使用该key访问逆地理编码功能时，就会返回该错误。反之亦然。
2.开发者请求接口的路径拼写错误。例如：正确的https://restapi.amap.com/**v3**/ip在程序中被拼装写了https://restapi.amap.com/**vv3**/ip"|
|10003|DAILY\_QUERY\_OVER\_LIMIT|访问已超出日访问量|开发者的日访问量超限，被系统自动封停，第二天0:00会自动解封。|
|10004|ACCESS\_TOO\_FREQUENT|单位时间内访问过于频繁|开发者的单位时间内（1分钟）访问量超限，被系统自动封停，下一分钟自动解封。|
|10005|INVALID\_USER\_IP|IP白名单出错，发送请求的服务器IP不在IP白名单内|开发者在LBS官网控制台设置的IP白名单不正确。白名单中未添加对应服务器的出口IP。可到["控制台>配置"](https://lbs.amap.com/dev/)  中设定IP白名单。|
|10006|INVALID\_USER\_DOMAIN|绑定域名无效|开发者绑定的域名无效，需要在官网控制台重新设置|
|10007|INVALID\_USER\_SIGNATURE|数字签名未通过验证|开发者签名未通过开发者在key控制台中，开启了“数字签名”功能，但没有按照指定算法生成“数字签名”。|
|10008|INVALID\_USER\_SCODE|MD5安全码未通过验证|需要开发者判定key绑定的SHA1,package是否与sdk包里的一致|
|10009|USERKEY\_PLAT\_NOMATCH|请求key与绑定平台不符|请求中使用的key与绑定平台不符，例如：开发者申请的是js api的key，却用来调web服务接口|
|10010|IP\_QUERY\_OVER\_LIMIT|IP访问超限|未设定IP白名单的开发者使用key发起请求，从单个IP向服务器发送的请求次数超出限制，被系统自动封停。封停后无法自动恢复，需要提交[工单](https://lbs.amap.com/dev/ticket/create/24)联系我们。|
|10011|NOT\_SUPPORT\_HTTPS|服务不支持https请求|服务不支持https请求，如果需要申请支持，请提交[工单](https://lbs.amap.com/dev/ticket/create/24)联系我们|
|10012|INSUFFICIENT\_PRIVILEGES|权限不足，服务请求被拒绝|由于不具备请求该服务的权限，所以服务被拒绝。|
|10013|USER\_KEY\_RECYCLED|Key被删除|开发者删除了key，key被删除后无法正常使用|
|10014|QPS\_HAS\_EXCEEDED\_THE\_LIMIT|云图服务QPS超限|QPS超出限制，超出部分的请求被拒绝。限流阈值内的请求依旧会正常返回|
|10015|GATEWAY\_TIMEOUT|受单机QPS限流限制|受单机QPS限流限制时出现该问题，建议降低请求的QPS或在控制台提工单联系我们|
|10016|SERVER\_IS\_BUSY|服务器负载过高|服务器负载过高，请稍后再试|
|10017|RESOURCE\_UNAVAILABLE|所请求的资源不可用|所请求的资源不可用|
|10019|CQPS\_HAS\_EXCEEDED\_THE\_LIMIT|使用的某个服务总QPS超限|QPS超出限制，超出部分的请求被拒绝。限流阈值内的请求依旧会正常返回|
|10020|CKQPS\_HAS\_EXCEEDED\_THE\_LIMIT|某个Key使用某个服务接口QPS超出限制|QPS超出限制，超出部分的请求被拒绝。限流阈值内的请求依旧会正常返回|
|10021|CUQPS\_HAS\_EXCEEDED\_THE\_LIMIT|账号使用某个服务接口QPS超出限制|QPS超出限制，超出部分的请求被拒绝。限流阈值内的请求依旧会正常返回|
|10026|INVALID\_REQUEST|账号处于被封禁状态|由于违规行为账号被封禁不可用，如有异议请登录[控制台](https://console.amap.com/dev/index)提交工单进行申诉|
|10029|ABROAD\_DAILY\_QUERY\_OVER\_LIMIT|某个Key的QPS超出限制|QPS超出限制，超出部分的请求被拒绝。限流阈值内的请求依旧会正常返回|
|10041|NO\_EFFECTIVE\_INTERFACE|请求的接口权限过期|开发者发起请求时，请求的接口权限过期。请提交[工单](https://lbs.amap.com/dev/ticket/create/24)联系我们|
|10044|USER\_DAILY\_QUERY\_OVER\_LIMIT|账号维度日调用量超出限制|账号维度日调用量超出限制，超出部分的请求被拒绝。限流阈值内的请求依旧会正常返回|
|10045|USER\_ABROAD\_DAILY\_QUERY\_OVER\_LIMIT|账号维度海外服务日调用量超出限制|账号维度海外服务接口日调用量超出限制，超出部分的请求被拒绝。限流阈值内的请求依旧会正常返回|
|20000|INVALID\_PARAMS|请求参数非法|请求参数的值没有按照规范要求填写。例如，某参数值域范围为\[1,3\],开发者误填了’4’|
|20001|MISSING\_REQUIRED\_PARAMS|缺少必填参数|缺少接口中要求的必填参数|
|20002|ILLEGAL\_REQUEST|请求协议非法|请求协议非法
比如某接口仅支持get请求，结果用了POST方式|
|20003|UNKNOWN\_ERROR|其他未知错误|其他未知错误|
|20011|INSUFFICIENT\_ABROAD\_PRIVILEGES|查询坐标或规划点（包括起点、终点、途经点）在海外，但没有海外地图权限|使用逆地理编码接口、输入提示接口、周边搜索接口、路径规划接口时可能出现该问题，规划点（包括起点、终点、途经点）不在中国陆地范围内|
|20012|ILLEGAL\_CONTENT|查询信息存在非法内容|使用搜索接口时可能出现该问题，通常是由于查询内容非法导致|
|20800|OUT\_OF\_SERVICE|规划点（包括起点、终点、途经点）不在中国陆地范围内|使用路径规划服务接口时可能出现该问题，规划点（包括起点、终点、途经点）不在中国大陆陆地范围内|
|20801|NO\_ROADS\_NEARBY|划点（起点、终点、途经点）附近搜不到路|使用路径规划服务接口时可能出现该问题，划点（起点、终点、途经点）附近搜不到路|
|20802|ROUTE\_FAIL|路线计算失败，通常是由于道路连通关系导致|使用路径规划服务接口时可能出现该问题，路线计算失败，通常是由于道路连通关系导致|
|20803|OVER\_DIRECTION\_RANGE|起点终点距离过长。|使用路径规划服务接口时可能出现该问题，路线计算失败，通常是由于道路起点和终点距离过长导致。|
|300\*\*|ENGINE\_RESPONSE\_DATA\_ERROR|服务响应失败。|出现3开头的错误码，建议先检查传入参数是否正确，若无法解决，请详细描述错误复现信息，提[`工单`](https://lbs.amap.com/dev/ticket/create/24)给我们。（大数据接口请直接跟负责商务反馈）
如，30001、30002、30003、32000、32001、32002、32003、32200、32201、32202、32203。|
|40000|QUOTA\_PLAN\_RUN\_OUT|余额耗尽|所购买服务的余额耗尽，无法继续使用服务|
|40001|GEOFENCE\_MAX\_COUNT\_REACHED|围栏个数达到上限|Key可创建的地理围栏的数量，已达上限。|
|40002|SERVICE\_EXPIRED|购买服务到期|所购买的服务期限已到，无法继续使用|
|40003|ABROAD\_QUOTA\_PLAN\_RUN\_OUT|海外服务余额耗尽|所购买服务的海外余额耗尽，无法继续使用服务|
