"""
地址类型 → 图标映射工具

按地址类型关键词返回对应 emoji 图标，用于搜索历史/搜索结果/收藏夹
列表条目的左侧图标（同一地址在三处显示一致的图标）。

类型缺失时（如旧版收藏数据无 type 字段），从地址名称推断类型，
保证历史数据也能按类型显示图标。
"""


def get_type_emoji(type_text: str, name: str = '') -> str:
    """根据地址类型（及名称兜底）返回对应 emoji 图标

    Args:
        type_text: 地址类型文本（高德 type/type_info，可为空）
        name: 地址名称（type 缺失/未匹配时用于推断，可为空）

    Returns:
        str: emoji 图标
    """
    # 类型文本 + 名称拼接匹配（旧数据无 type 时名称兜底）
    t = (type_text or '') + ' ' + (name or '')
    if not t.strip():
        return '📍'

    # 餐饮美食
    if any(k in t for k in ('餐饮', '美食', '餐厅', '咖啡', '小吃', '快餐', '饭店', '酒楼', '食府', '烧烤')):
        return '🍜'
    # 购物消费
    if any(k in t for k in ('购物', '商场', '超市', '便利店', '市场', '商城')):
        return '🛍️'
    # 酒店住宿
    if any(k in t for k in ('酒店', '宾馆', '住宿', '旅馆', '民宿')):
        return '🏨'
    # 交通枢纽（含名称中的"站"字：北京西站/地铁站等）
    if any(k in t for k in ('车站', '地铁', '火车站', '机场', '公交', '交通', '高铁', '客运站', '站')):
        return '🚉'
    # 风景名胜（不含裸"园"字，避免误匹配花园/家园/科技园等）
    if any(k in t for k in ('风景', '景点', '公园', '广场', '名胜', '博物馆', '旅游', '景区')):
        return '🏞️'
    # 科教培训
    if any(k in t for k in ('学校', '大学', '教育', '科教', '培训', '学院')):
        return '🎓'
    # 医疗健康
    if any(k in t for k in ('医院', '诊所', '医疗', '药店', '健康')):
        return '🏥'
    # 金融保险
    if any(k in t for k in ('银行', '金融', '保险', '证券', '理财')):
        return '🏦'
    # 商务办公
    if any(k in t for k in ('公司', '企业', '写字楼', '办公', '科技园', '大厦', '商务', '中心')):
        return '🏢'
    # 住宅小区
    if any(k in t for k in ('住宅', '小区', '楼盘', '公寓', '别墅', '宿舍', '家园', '花园', '苑')):
        return '🏠'
    # 汽车交通附属
    if any(k in t for k in ('停车场', '加油站', '汽车', '充电')):
        return '🅿️'

    # 默认：定位图标
    return '📍'
