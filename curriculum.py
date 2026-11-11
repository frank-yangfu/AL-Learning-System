# -*- coding: utf-8 -*-
"""
AL 自学系统 —— 内置 K12 课程大纲（小学 / 初中 / 高中）

数据结构：
  CURRICULUM : 树形结构，[ 学段 -> 学科 -> 年级 -> 知识点 ]
  每个知识点 topic 含：id / title / goals(学习目标) / sub(核心内容列表)

course_context(course_id) 供 server 注入大模型 prompt，让导师针对具体知识点引导。

说明：知识点按 人教版 / 统编版 教材主要单元（上册、下册）详尽列出，
覆盖 K12 主干学科，供青海西宁学生自主选择、按教材进度自学。
"""
from __future__ import annotations
try:
    from extra_curriculum import EXTRA_CURRICULUM
except Exception:
    EXTRA_CURRICULUM = []

# ----------------------------- 地区与教材说明 -----------------------------
# 适配青海省西宁市中小学：课程依据国家义务教育/高中课程方案设置，
# 教材版本与西宁地区现行使用的 人教版 / 统编版 一致；青海高考使用全国卷。
REGION = "青海省西宁市"
TEXTBOOK = "人教版 / 统编版"
STANDARD = (
    "依据《义务教育课程方案（2022年版）》与《普通高中课程方案》设置；"
    "教材版本与西宁地区中小学现行使用的 人教版/统编版 一致，"
    "覆盖语文、数学、英语、物理、化学、生物、历史、地理、道德与法治/思想政治等主干学科；"
    "青海高考采用全国卷。"
)

# ----------------------------- 课程树 -----------------------------
# 说明：按教材主要单元（上、下册）详尽列出知识点，覆盖各年级主干学科。
CURRICULUM = [
    # ============================== 小学 ==============================
    {
        "stage": "小学",
        "subjects": [
            # ---------------- 小学语文（统编版） ----------------
            {
                "name": "语文",
                "grades": [
                    {"grade": "一年级", "topics": [
                        {"id": "pe-lang-g1-u1", "title": "我上学了·基础识字", "goals": "认识校园与同伴，学习基本礼仪，认识最常用汉字。",
                         "sub": ["上学歌", "天地人你我他", "口耳目手足", "日月水火", "对韵歌"]},
                        {"id": "pe-lang-g1-u2", "title": "汉语拼音（一）", "goals": "学会单韵母与声母，掌握正确拼读方法。",
                         "sub": ["单韵母 a o e i u ü", "声母 b p m f d t n l", "声母 g k h j q x", "四声与标调", "拼读练习"]},
                        {"id": "pe-lang-g1-u3", "title": "汉语拼音（二）", "goals": "学会复韵母、鼻韵母与整体认读音节。",
                         "sub": ["复韵母 ai ei ui", "鼻韵母 an en in", "整体认读音节", "轻声与儿化", "拼音阅读"]},
                        {"id": "pe-lang-g1-u4", "title": "识字（一）", "goals": "在语境中识字，初步感受汉字构字规律。",
                         "sub": ["金木水火土", "口耳目", "日月明", "小书包", "日月水火"]},
                        {"id": "pe-lang-g1-u5", "title": "课文（一）·自然之趣", "goals": "朗读儿歌，积累词语，感受秋天与四季。",
                         "sub": ["秋天", "小小的船", "江南", "四季", "口语交际：自我介绍"]},
                        {"id": "pe-lang-g1-u6", "title": "识字（二）", "goals": "继续在韵文中识字，体会汉字趣味。",
                         "sub": ["画", "大小多少", "小书包", "日月明", "升国旗"]},
                        {"id": "pe-lang-g1-u7", "title": "课文（二）·想象世界", "goals": "借助图画阅读，激发想象与表达。",
                         "sub": ["影子", "比尾巴", "青蛙写诗", "雨点儿", "口语交际：用多大的声音"]},
                        {"id": "pe-lang-g1-u8", "title": "和大人一起读·快乐读书吧", "goals": "培养阅读兴趣，学习和大人共读。",
                         "sub": ["读书真快乐", "诵读童谣", "听故事讲故事", "剪窗花", "春节童谣"]},
                    ]},
                    {"grade": "二年级", "topics": [
                        {"id": "pe-lang-g2-u1", "title": "课文（一）·童话与科普", "goals": "读通童话与科普短文，学习提取信息。",
                         "sub": ["小蝌蚪找妈妈", "我是什么", "植物妈妈有办法", "口语交际：有趣的动物", "梅花"]},
                        {"id": "pe-lang-g2-u2", "title": "识字（一）", "goals": "在场景与儿歌中识字，感受语言节奏。",
                         "sub": ["场景歌", "树之歌", "拍手歌", "田家四季歌", "十二月花名歌"]},
                        {"id": "pe-lang-g2-u3", "title": "课文（二）·爱与陪伴", "goals": "体会人物情感，学习默读。",
                         "sub": ["曹冲称象", "玲玲的画", "一封信", "妈妈睡了", "口语交际：做手工"]},
                        {"id": "pe-lang-g2-u4", "title": "课文（三）·家乡与风景", "goals": "感受祖国山河，积累优美词句。",
                         "sub": ["古诗二首（登鹳雀楼/望庐山瀑布）", "黄山奇石", "日月潭", "葡萄沟", "口语交际：商量"]},
                        {"id": "pe-lang-g2-u5", "title": "课文（四）·智慧故事", "goals": "读寓言与成语故事，明白道理。",
                         "sub": ["坐井观天", "寒号鸟", "我要的是葫芦", "口语交际：看图讲故事", "江雪"]},
                        {"id": "pe-lang-g2-u6", "title": "课文（五）·伟人情怀", "goals": "了解伟人故事，学习按事情顺序表达。",
                         "sub": ["大禹治水", "朱德的扁担", "难忘的泼水节", "口语交际：看图讲故事", "识字加油站"]},
                        {"id": "pe-lang-g2-u7", "title": "课文（六）·自然奥秘", "goals": "探索自然现象，激发好奇心。",
                         "sub": ["古诗二首（夜宿山寺/敕勒歌）", "雾在哪里", "雪孩子", "口语交际：看图讲故事", "分不清的鸭和霞"]},
                        {"id": "pe-lang-g2-u8", "title": "课文（七）·相处与关爱", "goals": "学习与人相处，写话练习。",
                         "sub": ["狐假虎威", "狐狸分奶酪", "纸船和风筝", "风娃娃", "看图写话：猫和老鼠"]},
                    ]},
                    {"grade": "三年级", "topics": [
                        {"id": "pe-lang-g3-u1", "title": "课文（一）·校园生活", "goals": "感受多彩校园，学习结合上下文理解词句。",
                         "sub": ["大青树下的小学", "花的学校", "不懂就要问", "口语交际：我的暑假生活", "语文园地一"]},
                        {"id": "pe-lang-g3-u2", "title": "课文（二）·金秋时节", "goals": "积累描写秋天的词句，学习写日记。",
                         "sub": ["古诗三首（山行/赠刘景文/夜书所见）", "铺满金色巴掌的水泥道", "秋天的雨", "听听，秋的声音", "写日记"]},
                        {"id": "pe-lang-g3-u3", "title": "课文（三）·童话世界", "goals": "感受童话想象，学习续编故事。",
                         "sub": ["去年的树", "那一定会很好", "在牛肚子里旅行", "一块奶酪", "习作：我来编童话"]},
                        {"id": "pe-lang-g3-u4", "title": "课文（四）·预测阅读", "goals": "学习边读边预测，提升阅读策略。",
                         "sub": ["总也倒不了的老屋", "胡萝卜先生的长胡子", "不会叫的狗", "口语交际：名字里的故事", "习作：续写故事"]},
                        {"id": "pe-lang-g3-u5", "title": "课文（五）·观察与发现", "goals": "学习细致观察，把观察写清楚。",
                         "sub": ["搭船的鸟", "金色的草地", "习作：我们眼中的缤纷世界", "古诗三首（望天门山等）", "富饶的西沙群岛"]},
                        {"id": "pe-lang-g3-u6", "title": "课文（六）·祖国河山", "goals": "领略山河壮美，积累写景词句。",
                         "sub": ["海滨小城", "美丽的小兴安岭", "习作：这儿真美", "古诗三首（采莲曲等）", "语文园地六"]},
                        {"id": "pe-lang-g3-u7", "title": "课文（七）·我与自然", "goals": "体会人与自然关系，学习默读。",
                         "sub": ["大自然的声音", "父亲、树林和鸟", "带刺的朋友", "口语交际：身边的‘小事’", "习作：我有一个想法"]},
                        {"id": "pe-lang-g3-u8", "title": "课文（八）·美好品质", "goals": "感受人物美好品质，学习简要复述。",
                         "sub": ["司马光", "掌声", "灰雀", "口语交际：请教", "习作：那次玩得真高兴"]},
                    ]},
                    {"grade": "四年级", "topics": [
                        {"id": "pe-lang-g4-u1", "title": "课文（一）·自然奇观", "goals": "边读边想象画面，感受自然奇观。",
                         "sub": ["观潮", "走月亮", "现代诗二首", "繁星", "习作：推荐一个好地方"]},
                        {"id": "pe-lang-g4-u2", "title": "课文（二）·学贵有疑", "goals": "学习提出问题、解决问题。",
                         "sub": ["一个豆荚里的五粒豆", "蝙蝠和雷达", "呼风唤雨的世纪", "蝴蝶的家", "习作：我的家人"]},
                        {"id": "pe-lang-g4-u3", "title": "课文（三）·留心观察", "goals": "体会连续观察，学写观察日记。",
                         "sub": ["古诗三首（暮江吟等）", "爬山虎的脚", "蟋蟀的住宅", "口语交际：爱护眼睛", "习作：写观察日记"]},
                        {"id": "pe-lang-g4-u4", "title": "课文（四）·神话故事", "goals": "感受神话想象，学习简要复述。",
                         "sub": ["盘古开天地", "精卫填海", "普罗米修斯", "女娲补天", "习作：我和__过一天"]},
                        {"id": "pe-lang-g4-u5", "title": "课文（五）·童年往事", "goals": "体会童年情感，学习批注阅读。",
                         "sub": ["麻雀", "爬天都峰", "习作：生活万花筒", "牛和鹅", "一只窝囊的大老虎"]},
                        {"id": "pe-lang-g4-u6", "title": "课文（六）·家国情怀", "goals": "感受人物志向与家国情怀。",
                         "sub": ["古诗三首（出塞等）", "为中华之崛起而读书", "梅兰芳蓄须", "延安，我把你追寻", "习作：写信"]},
                        {"id": "pe-lang-g4-u7", "title": "课文（七）·世间万物", "goals": "把握文章主要内容，体会表达。",
                         "sub": ["西门豹治邺", "故事二则", "口语交际：讲历史人物故事", "习作：我的心儿怦怦跳", "语文园地七"]},
                        {"id": "pe-lang-g4-u8", "title": "课文（八）·俊杰与科学", "goals": "感受智慧与科学精神。",
                         "sub": ["王戎不取道旁李", "古诗三首", "文言文二则", "口语交际：讲历史人物故事", "习作：记一次游戏"]},
                    ]},
                    {"grade": "五年级", "topics": [
                        {"id": "pe-lang-g5-u1", "title": "课文（一）·万物有灵", "goals": "初步了解借物抒情，体会作者情感。",
                         "sub": ["白鹭", "落花生", "桂花雨", "珍珠鸟", "习作：我的心爱之物"]},
                        {"id": "pe-lang-g5-u2", "title": "课文（二）·阅读策略", "goals": "学习提高阅读速度的方法。",
                         "sub": ["搭石", "将相和", "什么比猎豹的速度更快", "冀中的地道战", "习作：‘漫画’老师"]},
                        {"id": "pe-lang-g5-u3", "title": "课文（三）·民间故事", "goals": "感受民间故事魅力，学习创造性复述。",
                         "sub": ["猎人海力布", "牛郎织女", "口语交际：讲民间故事", "习作：缩写故事", "乞巧"]},
                        {"id": "pe-lang-g5-u4", "title": "课文（四）·家国之殇", "goals": "体会家国情感，学习结合资料理解。",
                         "sub": ["古诗三首（示儿等）", "少年中国说", "圆明园的毁灭", "小岛", "习作：二十年后的家乡"]},
                        {"id": "pe-lang-g5-u5", "title": "课文（五）·说明性文章", "goals": "了解说明方法，学习写说明文。",
                         "sub": ["太阳", "松鼠", "习作例文", "习作：介绍一种事物", "语文园地五"]},
                        {"id": "pe-lang-g5-u6", "title": "课文（六）·父母之爱", "goals": "体会细节中的爱，学习场景描写。",
                         "sub": ["慈母情深", "父爱之舟", "精彩极了和糟糕透了", "口语交际：父母之爱", "习作：我想对您说"]},
                        {"id": "pe-lang-g5-u7", "title": "课文（七）·四季之美", "goals": "感受写景文章的动静结合。",
                         "sub": ["古诗词三首（山居秋暝等）", "四季之美", "鸟的天堂", "月迹", "习作：__即景"]},
                        {"id": "pe-lang-g5-u8", "title": "课文（八）·读书明智", "goals": "交流读书体会，学习列提纲。",
                         "sub": ["古人谈读书", "忆读书", "我的‘长生果’", "口语交际：我最喜欢的人物形象", "习作：推荐一本书"]},
                    ]},
                    {"grade": "六年级", "topics": [
                        {"id": "pe-lang-g6-u1", "title": "课文（一）·走进自然", "goals": "感受自然之美，学习联想与想象。",
                         "sub": ["草原", "丁香结", "古诗词三首", "花之歌", "习作：变形记"]},
                        {"id": "pe-lang-g6-u2", "title": "课文（二）·革命岁月", "goals": "了解革命历史，体会人物品质。",
                         "sub": ["七律·长征", "狼牙山五壮士", "开国大典", "灯光", "口语交际：演讲"]},
                        {"id": "pe-lang-g6-u3", "title": "课文（三）·有目的地阅读", "goals": "学习根据目的选择阅读方法。",
                         "sub": ["竹节人", "宇宙生命之谜", "故宫博物院", "习作：__让生活更美好", "语文园地三"]},
                        {"id": "pe-lang-g6-u4", "title": "课文（四）·小说之美", "goals": "感受小说情节与环境描写。",
                         "sub": ["桥", "穷人", "在柏林", "口语交际：请你支持我", "习作：笔尖流出的故事"]},
                        {"id": "pe-lang-g6-u5", "title": "课文（五）·习作单元", "goals": "学习围绕中心意思写。",
                         "sub": ["夏天里的成长", "盼", "习作例文", "习作：围绕中心意思写", "语文园地五"]},
                        {"id": "pe-lang-g6-u6", "title": "课文（六）·保护环境", "goals": "树立环保意识，学习倡议书。",
                         "sub": ["古诗三首（浪淘沙等）", "只有一个地球", "青山不老", "三黑和土地", "习作：学写倡议书"]},
                        {"id": "pe-lang-g6-u7", "title": "课文（七）·艺术之美", "goals": "感受艺术魅力，学习写感受。",
                         "sub": ["文言文二则（伯牙鼓琴等）", "月光曲", "京剧趣谈", "口语交际：聊聊书法", "习作：我的拿手好戏"]},
                        {"id": "pe-lang-g6-u8", "title": "课文（八）·美好回忆与复习", "goals": "回顾小学生活，综合复习。",
                         "sub": ["少年闰土", "好的故事", "我的伯父鲁迅先生", "有的人", "古诗词诵读与综合复习"]},
                    ]},
                ]
            },
            # ---------------- 小学数学（人教版） ----------------
            {
                "name": "数学",
                "grades": [
                    {"grade": "一年级", "topics": [
                        {"id": "pe-math-g1-u1", "title": "准备课·数一数、比多少", "goals": "建立数感，会比较多少。",
                         "sub": ["数数", "同样多", "多些少些", "一一对应", "观察与表达"]},
                        {"id": "pe-math-g1-u2", "title": "位置", "goals": "认识上下、前后、左右等位置关系。",
                         "sub": ["上和下", "前和后", "左和右", "位置描述", "排队问题"]},
                        {"id": "pe-math-g1-u3", "title": "1～5 的认识和加减法", "goals": "理解 1～5 的意义，掌握加减法。",
                         "sub": ["1～5 的认识", "比大小", "第几", "分与合", "加减法"]},
                        {"id": "pe-math-g1-u4", "title": "认识图形（一）", "goals": "辨认长方体、正方体、圆柱、球。",
                         "sub": ["长方体", "正方体", "圆柱", "球", "立体图形拼搭"]},
                        {"id": "pe-math-g1-u5", "title": "6～10 的认识和加减法", "goals": "理解 6～10，熟练相关加减法。",
                         "sub": ["6～10 认识", "加减法", "连加连减", "加减混合", "解决问题"]},
                        {"id": "pe-math-g1-u6", "title": "11～20 各数的认识", "goals": "认识数位，理解十进位值。",
                         "sub": ["数数", "读数写数", "十加几", "十几加几", "数位概念"]},
                        {"id": "pe-math-g1-u7", "title": "认识钟表", "goals": "认识整时与大约几时。",
                         "sub": ["钟面认识", "整时", "大约几时", "时间安排", "惜时教育"]},
                        {"id": "pe-math-g1-u8", "title": "20 以内的进位加法", "goals": "掌握凑十法，熟练进位加法。",
                         "sub": ["9 加几", "8/7/6 加几", "5/4/3/2 加几", "凑十法", "解决问题"]},
                    ]},
                    {"grade": "二年级", "topics": [
                        {"id": "pe-math-g2-u1", "title": "长度单位", "goals": "认识厘米和米，建立长度观念。",
                         "sub": ["统一长度单位", "厘米", "米", "线段", "解决问题"]},
                        {"id": "pe-math-g2-u2", "title": "100 以内的加法和减法（二）", "goals": "掌握两位数加减法笔算。",
                         "sub": ["不进位加", "进位加", "不退位减", "退位减", "连加连减和加减混合"]},
                        {"id": "pe-math-g2-u3", "title": "角的初步认识", "goals": "认识角，区分直角、锐角、钝角。",
                         "sub": ["角的各部分", "直角", "画直角", "锐角和钝角", "角在生活中的应用"]},
                        {"id": "pe-math-g2-u4", "title": "表内乘法（一）", "goals": "理解乘法意义，熟记 1～6 口诀。",
                         "sub": ["乘法的初步认识", "5 的乘法口诀", "2/3/4 口诀", "6 的乘法口诀", "乘加乘减"]},
                        {"id": "pe-math-g2-u5", "title": "观察物体（一）", "goals": "从不同方向观察简单物体。",
                         "sub": ["正面侧面上面", "立体图形的视图", "观察长方体", "观察球与圆柱", "空间想象"]},
                        {"id": "pe-math-g2-u6", "title": "表内乘法（二）", "goals": "熟记 7～9 乘法口诀并应用。",
                         "sub": ["7 的口诀", "8 的口诀", "9 的口诀", "解决问题", "口诀表"]},
                        {"id": "pe-math-g2-u7", "title": "认识时间", "goals": "认识几时几分，会推算时间。",
                         "sub": ["钟面复习", "几时几分", "时间的推算", "时间表", "珍惜时间"]},
                        {"id": "pe-math-g2-u8", "title": "数学广角·搭配（一）", "goals": "学习简单排列与组合。",
                         "sub": ["两件物品搭配", "三个数排列", "组合问题", "有序思考", "生活应用"]},
                    ]},
                    {"grade": "三年级", "topics": [
                        {"id": "pe-math-g3-u1", "title": "测量", "goals": "认识毫米、分米、千米和吨。",
                         "sub": ["毫米分米", "千米", "吨", "单位换算", "估测"]},
                        {"id": "pe-math-g3-u2", "title": "万以内的加法和减法", "goals": "掌握万以内加减法笔算与验算。",
                         "sub": ["加法", "减法", "验算", "解决问题", "估算"]},
                        {"id": "pe-math-g3-u3", "title": "倍的认识", "goals": "理解倍的意义，解决倍数问题。",
                         "sub": ["倍的概念", "求一个数是几倍", "求一个数的几倍", "画图解题", "应用"]},
                        {"id": "pe-math-g3-u4", "title": "多位数乘一位数", "goals": "掌握多位数乘一位数笔算。",
                         "sub": ["口算乘法", "笔算乘法", "进位乘法", "中间末尾有0", "解决问题"]},
                        {"id": "pe-math-g3-u5", "title": "长方形和正方形", "goals": "认识特征，理解周长并会计算。",
                         "sub": ["四边形", "长方形正方形特征", "周长", "周长计算", "拼图求周长"]},
                        {"id": "pe-math-g3-u6", "title": "分数的初步认识", "goals": "理解分数意义，会比较与简单加减。",
                         "sub": ["分数的意义", "几分之一", "几分之几", "大小比较", "简单加减"]},
                        {"id": "pe-math-g3-u7", "title": "数学广角·集合", "goals": "用集合思想解决重叠问题。",
                         "sub": ["韦恩图", "重叠问题", "只A", "只B", "应用"]},
                    ]},
                    {"grade": "四年级", "topics": [
                        {"id": "pe-math-g4-u1", "title": "大数的认识", "goals": "认识亿以内及亿以上数。",
                         "sub": ["计数单位", "数位顺序表", "读法和写法", "改写与求近似数", "计算器"]},
                        {"id": "pe-math-g4-u2", "title": "公顷和平方千米", "goals": "认识较大面积单位。",
                         "sub": ["公顷", "平方千米", "单位换算", "面积大小比较", "实际应用"]},
                        {"id": "pe-math-g4-u3", "title": "角的度量", "goals": "会用量角器度量与画角。",
                         "sub": ["线段射线直线", "角的定义", "量角器", "角的分类", "画角"]},
                        {"id": "pe-math-g4-u4", "title": "三位数乘两位数", "goals": "掌握笔算，理解数量关系。",
                         "sub": ["口算笔算", "因数与积变化", "常见数量关系", "估算", "解决问题"]},
                        {"id": "pe-math-g4-u5", "title": "平行四边形和梯形", "goals": "认识平行四边形与梯形。",
                         "sub": ["平行与垂直", "平行四边形", "梯形", "画高", "图形的关系"]},
                        {"id": "pe-math-g4-u6", "title": "除数是两位数的除法", "goals": "掌握笔算除法与试商。",
                         "sub": ["口算除法", "商是一位数的笔算", "商是两位数的笔算", "商的变化规律", "解决问题"]},
                        {"id": "pe-math-g4-u7", "title": "条形统计图", "goals": "认识条形统计图，能读图分析。",
                         "sub": ["单式条形图", "复式条形图", "数据收集", "读图分析", "提出问题"]},
                        {"id": "pe-math-g4-u8", "title": "数学广角·优化", "goals": "学习统筹安排与优化。",
                         "sub": ["沏茶问题", "烙饼问题", "田忌赛马", "策略选择", "生活应用"]},
                    ]},
                    {"grade": "五年级", "topics": [
                        {"id": "pe-math-g5-u1", "title": "小数乘法", "goals": "掌握小数乘法的算理与算法。",
                         "sub": ["小数乘整数", "小数乘小数", "积的近似数", "整数运算律推广", "解决问题"]},
                        {"id": "pe-math-g5-u2", "title": "位置", "goals": "用数对表示位置。",
                         "sub": ["列与行", "数对表示", "方格纸上的位置", "路线描述", "坐标思想"]},
                        {"id": "pe-math-g5-u3", "title": "小数除法", "goals": "掌握小数除法及循环小数。",
                         "sub": ["除数是整数", "除数是小数", "商的近似数", "循环小数", "解决问题"]},
                        {"id": "pe-math-g5-u4", "title": "可能性", "goals": "理解事件发生的可能性。",
                         "sub": ["一定、可能、不可能", "可能性大小", "游戏公平性", "概率初步", "实验估计"]},
                        {"id": "pe-math-g5-u5", "title": "简易方程", "goals": "理解用字母表示数，解简易方程。",
                         "sub": ["用字母表示数", "等式性质", "解方程", "列方程解应用题", "ax±b=c"]},
                        {"id": "pe-math-g5-u6", "title": "多边形的面积", "goals": "掌握多边形面积公式及推导。",
                         "sub": ["平行四边形面积", "三角形面积", "梯形面积", "组合图形", "估算不规则图形"]},
                        {"id": "pe-math-g5-u7", "title": "数学广角·植树问题", "goals": "掌握植树问题的模型。",
                         "sub": ["两端都栽", "两端不栽", "封闭图形", "模型应用", "化归思想"]},
                    ]},
                    {"grade": "六年级", "topics": [
                        {"id": "pe-math-g6-u1", "title": "分数乘法", "goals": "掌握分数乘法的意义与计算。",
                         "sub": ["分数乘整数", "分数乘分数", "小数乘分数", "整数乘法运算律", "解决问题"]},
                        {"id": "pe-math-g6-u2", "title": "分数除法", "goals": "掌握分数除法及比的应用。",
                         "sub": ["倒数", "分数除法计算", "分数混合运算", "解决问题", "比的意义和性质"]},
                        {"id": "pe-math-g6-u3", "title": "比", "goals": "理解比，能按比例分配。",
                         "sub": ["比的意义", "比的基本性质", "化简比", "按比例分配", "比的应用"]},
                        {"id": "pe-math-g6-u4", "title": "圆", "goals": "认识圆，掌握周长与面积。",
                         "sub": ["圆的认识", "圆的周长", "圆的面积", "扇形", "组合图形"]},
                        {"id": "pe-math-g6-u5", "title": "百分数", "goals": "理解百分数意义并会应用。",
                         "sub": ["百分数的意义", "百分数小数分数互化", "百分率", "百分数应用题", "折扣成数"]},
                        {"id": "pe-math-g6-u6", "title": "圆柱与圆锥", "goals": "掌握圆柱圆锥的表面积与体积。",
                         "sub": ["圆柱的认识", "圆柱的表面积", "圆柱的体积", "圆锥的认识", "圆锥的体积"]},
                        {"id": "pe-math-g6-u7", "title": "比例", "goals": "理解比例，能解比例与应用。",
                         "sub": ["比例的意义", "比例的基本性质", "解比例", "正比例反比例", "比例尺"]},
                        {"id": "pe-math-g6-u8", "title": "数学广角·鸽巢问题", "goals": "初步体会抽屉原理。",
                         "sub": ["抽屉原理", "最不利原则", "模型识别", "简单推理", "生活应用"]},
                        {"id": "pe-math-g6-u9", "title": "整理与复习", "goals": "系统复习小学数与代数、图形与统计。",
                         "sub": ["数与代数", "图形与几何", "统计与概率", "综合与实践", "小升初衔接"]},
                    ]},
                ]
            },
            # ---------------- 小学英语（人教版 PEP） ----------------
            {
                "name": "英语",
                "lang": "en",
                "grades": [
                    {"grade": "三年级", "topics": [
                        {"id": "pe-eng-g3-u1", "title": "Unit 1 Hello!", "goals": "Greet people and introduce yourself.",
                         "sub": ["Greetings", "School things", "I have a ...", "Open/show/close", "Letters A-D"]},
                        {"id": "pe-eng-g3-u2", "title": "Unit 2 Colours", "goals": "Talk about colours and introduce people.",
                         "sub": ["Colours", "This is ...", "Good morning/afternoon", "Introduce friends", "Letters E-H"]},
                        {"id": "pe-eng-g3-u3", "title": "Unit 3 Look at me", "goals": "Name body parts and show care.",
                         "sub": ["Body parts", "How are you?", "Touch your ...", "Clap/Stamp/Wave", "Letters I-L"]},
                        {"id": "pe-eng-g3-u4", "title": "Unit 4 We love animals", "goals": "Name animals and act like them.",
                         "sub": ["Animals", "What's this/that?", "It's a ...", "Act like a ...", "Letters M-P"]},
                        {"id": "pe-eng-g3-u5", "title": "Unit 5 Let's eat", "goals": "Talk about food and drinks.",
                         "sub": ["Food and drink", "I'd like some ...", "Have some ...", "Can I have ...?", "Letters Q-T"]},
                        {"id": "pe-eng-g3-u6", "title": "Unit 6 Happy birthday", "goals": "Talk about age and numbers.",
                         "sub": ["Numbers 1-10", "How old are you?", "How many?", "Happy birthday!", "Letters U-Z"]},
                    ]},
                    {"grade": "四年级", "topics": [
                        {"id": "pe-eng-g4-u1", "title": "Unit 1 My classroom", "goals": "Describe the classroom and objects.",
                         "sub": ["Classroom things", "Where is ...?", "Let me ...", "Clean the ...", "Let's spell a-e"]},
                        {"id": "pe-eng-g4-u2", "title": "Unit 2 My schoolbag", "goals": "Talk about school things and colours.",
                         "sub": ["School things", "What's in ...?", "What colour?", "Lost and found", "Spelling i-e"]},
                        {"id": "pe-eng-g4-u3", "title": "Unit 3 My friends", "goals": "Describe friends' appearance.",
                         "sub": ["Appearance words", "He/She is ...", "His/Her ...", "Friendship", "Spelling o-e"]},
                        {"id": "pe-eng-g4-u4", "title": "Unit 4 My home", "goals": "Name rooms and furniture.",
                         "sub": ["Rooms", "Where are ...?", "Is she in ...?", "Home activities", "Spelling u-e"]},
                        {"id": "pe-eng-g4-u5", "title": "Unit 5 Dinner's ready", "goals": "Order food and use chopsticks.",
                         "sub": ["Food", "What would you like?", "I can use ...", "Table manners", "Spelling e"]},
                        {"id": "pe-eng-g4-u6", "title": "Unit 6 Meet my family", "goals": "Talk about family members' jobs.",
                         "sub": ["Family members", "Jobs", "How many people?", "Parents' jobs", "Spelling a/ile"]},
                    ]},
                    {"grade": "五年级", "topics": [
                        {"id": "pe-eng-g5-u1", "title": "Unit 1 What's he like?", "goals": "Describe teachers' character.",
                         "sub": ["Character adjectives", "Who's your ...?", "Is he ...?", "Be + adjective", "Spelling y"]},
                        {"id": "pe-eng-g5-u2", "title": "Unit 2 My week", "goals": "Talk about days and activities.",
                         "sub": ["Days of week", "What do you have?", "Do you ...?", "Weekend activities", "Spelling ee/ea"]},
                        {"id": "pe-eng-g5-u3", "title": "Unit 3 What would you like?", "goals": "Order food and drinks.",
                         "sub": ["Food words", "What would you like?", "My favourite food", "Healthy food", "Spelling ow"]},
                        {"id": "pe-eng-g5-u4", "title": "Unit 4 What can you do?", "goals": "Talk about abilities.",
                         "sub": ["Ability verbs", "What can you do?", "Can you ...?", "Party activities", "Spelling oo"]},
                        {"id": "pe-eng-g5-u5", "title": "Unit 5 There is a big bed", "goals": "Describe a room with there be.",
                         "sub": ["Furniture words", "There is/are ...", "Where is ...?", "In/on/under", "Spelling ai/ay"]},
                        {"id": "pe-eng-g5-u6", "title": "Unit 6 In a nature park", "goals": "Describe nature with there be.",
                         "sub": ["Nature words", "Is there ...?", "Are there ...?", "Yes/No questions", "Spelling ou/ow"]},
                    ]},
                    {"grade": "六年级", "topics": [
                        {"id": "pe-eng-g6-u1", "title": "Unit 1 How can I get there?", "goals": "Ask for and give directions.",
                         "sub": ["Places", "Where is ...?", "How can I get ...?", "Turn left/right", "Spelling ei/ie"]},
                        {"id": "pe-eng-g6-u2", "title": "Unit 2 Ways to go to school", "goals": "Talk about transport and rules.",
                         "sub": ["Transport", "How do you come ...?", "Traffic lights", "Must/Don't", "Spelling oo/ou"]},
                        {"id": "pe-eng-g6-u3", "title": "Unit 3 My weekend plan", "goals": "Talk about future plans.",
                         "sub": ["Activities", "What are you going to do?", "be going to", "Time expressions", "Spelling ar/al"]},
                        {"id": "pe-eng-g6-u4", "title": "Unit 4 I have a pen pal", "goals": "Talk about hobbies and habits.",
                         "sub": ["Hobbies", "What are your hobbies?", "He/She likes ...", "Third-person -s", "Spelling le"]},
                        {"id": "pe-eng-g6-u5", "title": "Unit 5 What does he do?", "goals": "Talk about jobs and workplaces.",
                         "sub": ["Jobs", "What does he do?", "Where does he work?", "How does he go?", "Spelling er/or"]},
                        {"id": "pe-eng-g6-u6", "title": "Unit 6 How do you feel?", "goals": "Talk about feelings and advice.",
                         "sub": ["Feelings", "How do you feel?", "Should/shouldn't", "Give advice", "Spelling ou/ow"]},
                    ]},
                ]
            },
            # ---------------- 小学科学（教科版/人教版） ----------------
            {
                "name": "科学",
                "grades": [
                    {"grade": "三年级", "topics": [
                        {"id": "pe-sci-g3-u1", "title": "植物的一生", "goals": "观察植物生长，了解生命周期。",
                         "sub": ["种子萌发", "根和茎", "叶的作用", "开花结果", "生命周期"]},
                        {"id": "pe-sci-g3-u2", "title": "动物的生命周期", "goals": "了解动物出生、成长与繁殖。",
                         "sub": ["蚕的一生", "其他昆虫", "两栖动物", "哺乳动物", "生命周期比较"]},
                        {"id": "pe-sci-g3-u3", "title": "温度与水的变化", "goals": "认识温度与水的三态变化。",
                         "sub": ["温度与温度计", "融化与凝固", "蒸发", "凝结", "水的循环"]},
                        {"id": "pe-sci-g3-u4", "title": "磁铁", "goals": "认识磁铁的性质与应用。",
                         "sub": ["磁铁吸铁", "磁极", "同极相斥异极相吸", "指南针", "磁的应用"]},
                        {"id": "pe-sci-g3-u5", "title": "材料的性质", "goals": "区分常见材料并比较性质。",
                         "sub": ["木头塑料金属", "硬度比较", "沉浮", "溶解", "材料用途"]},
                    ]},
                    {"grade": "四年级", "topics": [
                        {"id": "pe-sci-g4-u1", "title": "溶解", "goals": "探究溶解现象与影响因素。",
                         "sub": ["溶解现象", "加快溶解", "过滤", "蒸发结晶", "溶液应用"]},
                        {"id": "pe-sci-g4-u2", "title": "声音", "goals": "认识声音的产生、传播与高低。",
                         "sub": ["声音的产生", "声音的传播", "音调高低", "音量大小", "噪声控制"]},
                        {"id": "pe-sci-g4-u3", "title": "天气", "goals": "观察与记录天气现象。",
                         "sub": ["云量风向", "降水量", "气温", "天气预报", "气候"]},
                        {"id": "pe-sci-g4-u4", "title": "我们的身体", "goals": "了解身体结构与健康。",
                         "sub": ["骨骼肌肉", "消化", "呼吸", "循环", "健康生活"]},
                        {"id": "pe-sci-g4-u5", "title": "岩石与矿物", "goals": "观察岩石与矿物的特征。",
                         "sub": ["常见岩石", "岩石硬度", "矿物特征", "用途", "保护资源"]},
                    ]},
                    {"grade": "五年级", "topics": [
                        {"id": "pe-sci-g5-u1", "title": "光", "goals": "探究光的传播、反射与折射。",
                         "sub": ["光源", "光的直线传播", "反射", "折射", "彩虹"]},
                        {"id": "pe-sci-g5-u2", "title": "地球表面及其变化", "goals": "了解地形与地表变化。",
                         "sub": ["地形", "侵蚀", "沉积", "地震火山", "岩石循环"]},
                        {"id": "pe-sci-g5-u3", "title": "生物与环境", "goals": "理解生物与环境的依存关系。",
                         "sub": ["种子发芽", "蚯蚓环境", "食物链", "生态瓶", "平衡"]},
                        {"id": "pe-sci-g5-u4", "title": "运动与力", "goals": "认识力与运动的关系。",
                         "sub": ["重力", "弹力", "摩擦力", "浮力", "运动改变"]},
                        {"id": "pe-sci-g5-u5", "title": "时间的变化", "goals": "了解计时工具与机械。",
                         "sub": ["日晷", "水钟", "摆", "机械钟", "精确计时"]},
                    ]},
                    {"grade": "六年级", "topics": [
                        {"id": "pe-sci-g6-u1", "title": "工具和机械", "goals": "认识简单机械的原理。",
                         "sub": ["杠杆", "轮轴", "滑轮", "斜面", "机械组合"]},
                        {"id": "pe-sci-g6-u2", "title": "形状与结构", "goals": "探究物体形状与承重。",
                         "sub": ["抗弯曲", "形状与抗弯", "拱形", "框架结构", "桥"]},
                        {"id": "pe-sci-g6-u3", "title": "能量", "goals": "认识各种能量及其转化。",
                         "sub": ["电与磁", "电磁铁", "能量形式", "能量转化", "节约能源"]},
                        {"id": "pe-sci-g6-u4", "title": "生物的多样性", "goals": "了解生物分类与保护。",
                         "sub": ["校园生物", "分类", "相貌特征", "生物多样性", "保护"]},
                        {"id": "pe-sci-g6-u5", "title": "宇宙", "goals": "了解地球、月球与太阳系。",
                         "sub": ["地球的卫星——月球", "月相", "太阳系", "星座", "探索宇宙"]},
                    ]},
                ]
            },
        ]
    },
    # ============================== 初中 ==============================
    {
        "stage": "初中",
        "subjects": [
            # ---------------- 初中语文 ----------------
            {
                "name": "语文",
                "grades": [
                    {"grade": "七年级", "topics": [
                        {"id": "ju-lang-g7-u1", "title": "第一单元·四季美景", "goals": "朗读体会景物情感，积累写景词句。",
                         "sub": ["春", "济南的冬天", "雨的四季", "古代诗歌四首", "热爱生活热爱写作"]},
                        {"id": "ju-lang-g7-u2", "title": "第二单元·至爱亲情", "goals": "感受亲情，学习细节描写。",
                         "sub": ["秋天的怀念", "散步", "散文诗二首", "世说新语二则", "学会记事"]},
                        {"id": "ju-lang-g7-u3", "title": "第三单元·学习生活", "goals": "默读把握大意，积累文言文。",
                         "sub": ["从百草园到三味书屋", "再塑生命的人", "窃读记", "《论语》十二章", "写人要抓住特点"]},
                        {"id": "ju-lang-g7-u4", "title": "第四单元·人生之舟", "goals": "体会人生哲理，学习默读勾画。",
                         "sub": ["纪念白求恩", "植树的牧羊人", "走一步再走一步", "诫子书", "思路要清晰"]},
                        {"id": "ju-lang-g7-u5", "title": "第五单元·动物与人", "goals": "体会作者情感，学习托物言志。",
                         "sub": ["猫", "动物笑谈", "狼", "如何突出中心", "记叙与描写"]},
                        {"id": "ju-lang-g7-u6", "title": "第六单元·想象之翼", "goals": "感受想象，学习编童话寓言。",
                         "sub": ["皇帝的新装", "天上的街市", "女娲造人", "寓言四则", "发挥联想和想象"]},
                    ]},
                    {"grade": "八年级", "topics": [
                        {"id": "ju-lang-g8-u1", "title": "第一单元·新闻活动", "goals": "了解新闻体裁，学写消息。",
                         "sub": ["消息二则", "首届诺贝尔奖颁发", "‘飞天’凌空", "一着惊海天", "新闻采访与写作"]},
                        {"id": "ju-lang-g8-u2", "title": "第二单元·人物传记", "goals": "感受人物品格，学习刻画。",
                         "sub": ["藤野先生", "回忆我的母亲", "列夫·托尔斯泰", "美丽的颜色", "学写传记"]},
                        {"id": "ju-lang-g8-u3", "title": "第三单元·山水古文", "goals": "借助注释读文言文，体会情志。",
                         "sub": ["三峡", "短文二篇", "与朱元思书", "唐诗五首", "学习描写景物"]},
                        {"id": "ju-lang-g8-u4", "title": "第四单元·情感哲思", "goals": "体会散文情感，学习不同类型。",
                         "sub": ["背影", "白杨礼赞", "散文二篇", "昆明的雨", "语言要连贯"]},
                        {"id": "ju-lang-g8-u5", "title": "第五单元·说明事物", "goals": "掌握说明文特征与顺序。",
                         "sub": ["中国石拱桥", "苏州园林", "人民英雄永垂不朽", "蝉", "说明事物要抓住特征"]},
                        {"id": "ju-lang-g8-u6", "title": "第六单元·情操志趣", "goals": "诵读古诗文，理解主旨。",
                         "sub": ["《孟子》二章", "愚公移山", "周亚夫军细柳", "诗词五首", "表达要得体"]},
                    ]},
                    {"grade": "九年级", "topics": [
                        {"id": "ju-lang-g9-u1", "title": "第一单元·诗歌吟咏", "goals": "朗读现代诗，体会意象情感。",
                         "sub": ["沁园春·雪", "我爱这土地", "乡愁", "你是人间的四月天", "尝试写诗"]},
                        {"id": "ju-lang-g9-u2", "title": "第二单元·议论纵横", "goals": "了解议论文，学写观点文。",
                         "sub": ["敬业与乐业", "就英法联军远征中国致巴特勒上尉的信", "论教养", "精神的三间小屋", "观点要明确"]},
                        {"id": "ju-lang-g9-u3", "title": "第三单元·山水忧乐", "goals": "诵读古诗文，理解作者情怀。",
                         "sub": ["岳阳楼记", "醉翁亭记", "湖心亭看雪", "诗词三首", "议论要言之有据"]},
                        {"id": "ju-lang-g9-u4", "title": "第四单元·少年成长", "goals": "梳理小说情节，体会主旨。",
                         "sub": ["故乡", "我的叔叔于勒", "孤独之旅", "学习缩写", "小说阅读策略"]},
                        {"id": "ju-lang-g9-u5", "title": "第五单元·戏剧舞台", "goals": "了解戏剧，学写剧本片段。",
                         "sub": ["屈原", "天下第一楼", "枣儿", "准备与排练", "戏剧阅读"]},
                        {"id": "ju-lang-g9-u6", "title": "第六单元·世态人情", "goals": "深读小说，学习改写扩写。",
                         "sub": ["智取生辰纲", "范进中举", "三顾茅庐", "刘姥姥进大观园", "谈创造性思维"]},
                    ]},
                ]
            },
            # ---------------- 初中数学 ----------------
            {
                "name": "数学",
                "grades": [
                    {"grade": "七年级", "topics": [
                        {"id": "ju-math-g7-u1", "title": "有理数", "goals": "理解有理数及运算。",
                         "sub": ["正数负数", "有理数", "数轴", "相反数绝对值", "有理数加减"]},
                        {"id": "ju-math-g7-u2", "title": "有理数的乘除法", "goals": "掌握乘除与乘方运算。",
                         "sub": ["乘法", "除法", "乘方", "科学记数法", "混合运算"]},
                        {"id": "ju-math-g7-u3", "title": "整式加减", "goals": "理解代数式与整式运算。",
                         "sub": ["代数式", "单项式多项式", "合并同类项", "去括号", "化简求值"]},
                        {"id": "ju-math-g7-u4", "title": "一元一次方程", "goals": "会列方程解应用题。",
                         "sub": ["等式性质", "解方程", "含参方程", "实际问题", "方案问题"]},
                        {"id": "ju-math-g7-u5", "title": "几何图形初步", "goals": "认识基本图形与角度。",
                         "sub": ["立体图形平面图形", "直线射线线段", "角", "余角补角", "方位角"]},
                        {"id": "ju-math-g7-u6", "title": "二元一次方程组", "goals": "会解二元一次方程组。",
                         "sub": ["代入消元", "加减消元", "实际问题", "三元一次", "图像法"]},
                    ]},
                    {"grade": "八年级", "topics": [
                        {"id": "ju-math-g8-u1", "title": "三角形", "goals": "掌握三角形性质与全等。",
                         "sub": ["三边关系", "内角外角", "多边形", "全等判定", "角平分线"]},
                        {"id": "ju-math-g8-u2", "title": "轴对称", "goals": "认识轴对称与等腰三角形。",
                         "sub": ["轴对称", "垂直平分线", "等腰三角形", "等边三角形", "最短路径"]},
                        {"id": "ju-math-g8-u3", "title": "整式乘法与因式分解", "goals": "掌握乘法公式与因式分解。",
                         "sub": ["同底数幂", "乘法公式", "因式分解", "提公因式", "公式法"]},
                        {"id": "ju-math-g8-u4", "title": "分式", "goals": "理解分式及运算。",
                         "sub": ["分式意义", "乘除", "加减", "分式方程", "实际应用"]},
                        {"id": "ju-math-g8-u5", "title": "一次函数", "goals": "理解函数与一次函数。",
                         "sub": ["变量与函数", "正比例函数", "一次函数图像", "待定系数法", "应用"]},
                        {"id": "ju-math-g8-u6", "title": "勾股定理", "goals": "掌握勾股定理及逆定理。",
                         "sub": ["勾股定理", "逆定理", "勾股数", "距离", "应用"]},
                    ]},
                    {"grade": "九年级", "topics": [
                        {"id": "ju-math-g9-u1", "title": "一元二次方程", "goals": "会解一元二次方程。",
                         "sub": ["配方法", "公式法", "因式分解法", "根与系数", "实际问题"]},
                        {"id": "ju-math-g9-u2", "title": "二次函数", "goals": "掌握二次函数图像与应用。",
                         "sub": ["图像性质", "顶点式", "与方程不等式", "最值", "实际应用"]},
                        {"id": "ju-math-g9-u3", "title": "旋转", "goals": "理解旋转与中心对称。",
                         "sub": ["旋转", "中心对称", "图案设计", "圆中的对称", "坐标变换"]},
                        {"id": "ju-math-g9-u4", "title": "圆", "goals": "理解圆的基本性质与计算。",
                         "sub": ["垂径定理", "圆周角", "切线", "弧长扇形", "圆与三角形"]},
                        {"id": "ju-math-g9-u5", "title": "概率初步", "goals": "理解概率与列举法。",
                         "sub": ["随机事件", "概率", "列举法", "树状图", "频率估计"]},
                        {"id": "ju-math-g9-u6", "title": "锐角三角函数", "goals": "理解三角函数与解直角三角。",
                         "sub": ["正弦余弦", "正切", "特殊角", "解直角三角形", "实际应用"]},
                    ]},
                ]
            },
            # ---------------- 初中英语 ----------------
            {
                "name": "英语",
                "lang": "en",
                "grades": [
                    {"grade": "七年级", "topics": [
                        {"id": "ju-eng-g7-u1", "title": "Unit 1 My name's Gina", "goals": "Ask and tell names and numbers.",
                         "sub": ["Names", "Nice to meet you", "What's your ...?", "Telephone numbers", "Be verbs review"]},
                        {"id": "ju-eng-g7-u2", "title": "Unit 2 This is my sister", "goals": "Introduce family members.",
                         "sub": ["Family tree", "This/That is ...", "These/Those", "Who's ...?", "Possessive 's"]},
                        {"id": "ju-eng-g7-u3", "title": "Unit 3 Is this your pencil?", "goals": "Talk about possessions.",
                         "sub": ["School things", "Is this ...?", "Yes/No answers", "Excuse me", "Lost and found"]},
                        {"id": "ju-eng-g7-u4", "title": "Unit 4 Where's my schoolbag?", "goals": "Describe positions with prepositions.",
                         "sub": ["Furniture", "Where is ...?", "On/in/under", "Prepositions", "Plural nouns"]},
                        {"id": "ju-eng-g7-u5", "title": "Unit 5 Do you have a soccer ball?", "goals": "Talk about sports and possession.",
                         "sub": ["Sports", "Do you have ...?", "Let's ...", "Like/dislike", "Sound adjectives"]},
                        {"id": "ju-eng-g7-u6", "title": "Unit 6 Do you like bananas?", "goals": "Talk about food and count/non-count.",
                         "sub": ["Food", "Do you like ...?", "Count/non-count", "Eating habits", "Third person"]},
                        {"id": "ju-eng-g7-u7", "title": "Unit 7 How much are these socks?", "goals": "Ask about prices and shop.",
                         "sub": ["Clothes", "How much?", "Numbers 10-31", "Shopping talk", "Color words"]},
                        {"id": "ju-eng-g7-u8", "title": "Unit 8 When is your birthday?", "goals": "Talk about dates and months.",
                         "sub": ["Months", "Ordinal numbers", "When is ...?", "Dates", "School events"]},
                        {"id": "ju-eng-g7-u9", "title": "Unit 9 My favorite subject is science", "goals": "Talk about subjects and reasons.",
                         "sub": ["Subjects", "What's your favorite ...?", "Why do you like ...?", "Days", "Because"]},
                    ]},
                    {"grade": "八年级", "topics": [
                        {"id": "ju-eng-g8-u1", "title": "Unit 1 Where did you go on vacation?", "goals": "Talk about past holidays.",
                         "sub": ["Places", "Where did ...?", "Indefinite pronouns", "Regular past", "Irregular past"]},
                        {"id": "ju-eng-g8-u2", "title": "Unit 2 How often do you exercise?", "goals": "Talk about frequency.",
                         "sub": ["Activities", "How often?", "Adverbs of frequency", "Healthy habits", "Surveys"]},
                        {"id": "ju-eng-g8-u3", "title": "Unit 3 I'm more outgoing than my sister", "goals": "Make comparisons.",
                         "sub": ["Adjective comparison", "Comparative forms", "Both/Either/Neither", "Describe friends", "Than"]},
                        {"id": "ju-eng-g8-u4", "title": "Unit 4 What's the best movie theater?", "goals": "Use superlatives.",
                         "sub": ["Superlative forms", "The best ...", "Closest/most", "Movie theaters", "Choices"]},
                        {"id": "ju-eng-g8-u5", "title": "Unit 5 Do you want to watch a game show?", "goals": "Talk about plans and shows.",
                         "sub": ["TV shows", "What do you think of ...?", "Mind/love/can't stand", "Future with want", "Plans"]},
                        {"id": "ju-eng-g8-u6", "title": "Unit 6 I'm going to study computer science", "goals": "Talk about future intentions.",
                         "sub": ["Jobs", "be going to", "New Year's resolutions", "How to achieve", "Future plans"]},
                        {"id": "ju-eng-g8-u7", "title": "Unit 7 Will people have robots?", "goals": "Use future with will.",
                         "sub": ["Will", "Predictions", "There will be", "More/less/fewer", "Future world"]},
                        {"id": "ju-eng-g8-u8", "title": "Unit 8 How do you make a banana milk shake?", "goals": "Describe a process.",
                         "sub": ["Food/recipe", "Imperatives", "How many/much", "Sequence words", "Cooking"]},
                        {"id": "ju-eng-g8-u9", "title": "Unit 9 Can you come to my party?", "goals": "Make and respond to invitations.",
                         "sub": ["Invitations", "Sure/I'd love to", "Must/might/have to", "Refusals", "Calendar"]},
                        {"id": "ju-eng-g8-u10", "title": "Unit 10 If you go to the party, you'll have a good time", "goals": "Use first conditional.",
                         "sub": ["If clause", "Will result", "Advice", "Consequences", "Real situations"]},
                    ]},
                    {"grade": "九年级", "topics": [
                        {"id": "ju-eng-g9-u1", "title": "Unit 1 How can we become good learners?", "goals": "Talk about learning methods.",
                         "sub": ["Learning ways", "by + doing", "How do you study?", "Reading habits", "Advice"]},
                        {"id": "ju-eng-g9-u2", "title": "Unit 2 I think that mooncakes are delicious", "goals": "Talk about festivals.",
                         "sub": ["Festivals", "that/if clauses", "The Spring Festival", "Customs", "Stories"]},
                        {"id": "ju-eng-g9-u3", "title": "Unit 3 Could you please tell me where the restrooms are?", "goals": "Ask for information politely.",
                         "sub": ["Directions", "Could you ...?", "Wh- questions", "Polite requests", "Prepositions"]},
                        {"id": "ju-eng-g9-u4", "title": "Unit 4 I used to be afraid of the dark", "goals": "Talk about past habits.",
                         "sub": ["used to", "Past vs now", "Appearance change", "Personality", "Glad/afraid"]},
                        {"id": "ju-eng-g9-u5", "title": "Unit 5 What are the shirts made of?", "goals": "Use passive voice (present).",
                         "sub": ["Materials", "be made of/from", "Passive present", "Products", "China brand"]},
                        {"id": "ju-eng-g9-u6", "title": "Unit 6 When was it invented?", "goals": "Use passive voice (past).",
                         "sub": ["Inventions", "be + past participle", "When was ...?", "By whom", "History"]},
                        {"id": "ju-eng-g9-u7", "title": "Unit 7 Teenagers should be allowed to choose", "goals": "Use passive with modal.",
                         "sub": ["should be allowed", "Agree/disagree", "Rules", "Teen life", "Permission"]},
                        {"id": "ju-eng-g9-u8", "title": "Unit 8 It must belong to Carla", "goals": "Make guesses with modals.",
                         "sub": ["must/could/can't", "Whose ...?", "Mysteries", "Guessing", "Evidence"]},
                        {"id": "ju-eng-g9-u9", "title": "Unit 9 I like music that I can dance to", "goals": "Use attributive clauses.",
                         "sub": ["that/which/who", "Preferences", "Music/movies", "Relative clauses", "Describe taste"]},
                        {"id": "ju-eng-g9-u10", "title": "Unit 10 You're supposed to shake hands", "goals": "Talk about customs and manners.",
                         "sub": ["Customs", "be supposed to", "Greeting", "Table manners", "Culture"]},
                    ]},
                ]
            },
            # ---------------- 初中物理（八年级起） ----------------
            {
                "name": "物理",
                "grades": [
                    {"grade": "八年级", "topics": [
                        {"id": "ju-phy-g8-u1", "title": "机械运动", "goals": "理解运动、速度与测量。",
                         "sub": ["长度时间测量", "参照物", "速度", "匀速直线", "平均速度"]},
                        {"id": "ju-phy-g8-u2", "title": "声现象", "goals": "认识声音的产生与传播。",
                         "sub": ["声音产生", "传播", "音调音色", "噪声", "超声波"]},
                        {"id": "ju-phy-g8-u3", "title": "物态变化", "goals": "理解温度与三态变化。",
                         "sub": ["温度温度计", "熔化凝固", "汽化液化", "升华凝华", "水循环"]},
                        {"id": "ju-phy-g8-u4", "title": "光现象", "goals": "认识光的直线传播、反射与折射。",
                         "sub": ["直线传播", "反射定律", "平面镜", "折射", "色散"]},
                        {"id": "ju-phy-g8-u5", "title": "透镜及其应用", "goals": "理解透镜成像规律。",
                         "sub": ["透镜", "凸透镜成像", "眼睛眼镜", "显微镜望远镜", "应用"]},
                        {"id": "ju-phy-g8-u6", "title": "质量与密度", "goals": "理解质量密度及测量。",
                         "sub": ["质量天平", "密度", "测量密度", "密度应用", "鉴别物质"]},
                        {"id": "ju-phy-g8-u7", "title": "力", "goals": "认识力的概念与作图。",
                         "sub": ["力的概念", "弹力", "重力", "力的合成", "力的图示"]},
                        {"id": "ju-phy-g8-u8", "title": "运动和力", "goals": "理解牛顿第一定律与平衡。",
                         "sub": ["牛顿第一定律", "惯性", "二力平衡", "摩擦力", "应用"]},
                        {"id": "ju-phy-g8-u9", "title": "压强", "goals": "理解压强与流体压强。",
                         "sub": ["压强", "液体压强", "大气压强", "流体压强", "升力"]},
                        {"id": "ju-phy-g8-u10", "title": "浮力", "goals": "理解浮力与阿基米德原理。",
                         "sub": ["浮力", "阿基米德原理", "浮沉条件", "密度计", "应用"]},
                        {"id": "ju-phy-g8-u11", "title": "功和机械能", "goals": "理解功、功率与机械能。",
                         "sub": ["功", "功率", "动能", "势能", "机械能守恒"]},
                        {"id": "ju-phy-g8-u12", "title": "简单机械", "goals": "认识杠杆与滑轮。",
                         "sub": ["杠杆", "杠杆平衡", "滑轮", "斜面", "机械效率"]},
                    ]},
                    {"grade": "九年级", "topics": [
                        {"id": "ju-phy-g9-u1", "title": "内能", "goals": "理解分子动理论与内能。",
                         "sub": ["分子动理论", "内能", "比热容", "热机", "能量转化"]},
                        {"id": "ju-phy-g9-u2", "title": "内能的利用", "goals": "理解热机效率与能量守恒。",
                         "sub": ["热值", "热机效率", "能量守恒", "能源", "可持续发展"]},
                        {"id": "ju-phy-g9-u3", "title": "电流和电路", "goals": "认识电路与电流。",
                         "sub": ["电荷", "电流电路", "串联并联", "电流", "练习使用电流表"]},
                        {"id": "ju-phy-g9-u4", "title": "电压 电阻", "goals": "理解电压与电阻。",
                         "sub": ["电压", "串联并联电压", "电阻", "变阻器", "应用"]},
                        {"id": "ju-phy-g9-u5", "title": "欧姆定律", "goals": "掌握欧姆定律及应用。",
                         "sub": ["电流与电压电阻", "电阻测量", "欧姆定律应用", "安全用电", "电路设计"]},
                        {"id": "ju-phy-g9-u6", "title": "电功率", "goals": "理解电功与电功率。",
                         "sub": ["电功", "电功率", "额定功率", "测量电功率", "焦耳定律"]},
                        {"id": "ju-phy-g9-u7", "title": "生活用电", "goals": "了解家庭电路与安全。",
                         "sub": ["家庭电路", "火线零线", "漏电保护", "安全用电", "触电急救"]},
                        {"id": "ju-phy-g9-u8", "title": "电与磁", "goals": "理解磁现象与电磁感应。",
                         "sub": ["磁场", "电生磁", "电磁铁", "电动机", "电磁感应"]},
                        {"id": "ju-phy-g9-u9", "title": "信息与能源", "goals": "了解现代通信与能源。",
                         "sub": ["电磁波", "广播通信", "信息时代", "能源分类", "核能"]},
                    ]},
                ]
            },
            # ---------------- 初中化学（九年级） ----------------
            {
                "name": "化学",
                "grades": [
                    {"grade": "九年级", "topics": [
                        {"id": "ju-chem-g9-u1", "title": "走进化学世界", "goals": "认识化学与实验基本操作。",
                         "sub": ["物质变化", "性质", "药品取用", "加热与仪器", "观察与记录"]},
                        {"id": "ju-chem-g9-u2", "title": "我们周围的空气", "goals": "理解空气组成与氧气性质。",
                         "sub": ["空气成分", "氧气性质", "制取氧气", "催化剂", "混合物纯净物"]},
                        {"id": "ju-chem-g9-u3", "title": "物质构成的奥秘", "goals": "理解微观粒子与元素。",
                         "sub": ["分子原子", "原子结构", "元素", "离子", "元素周期表"]},
                        {"id": "ju-chem-g9-u4", "title": "自然界的水", "goals": "理解水的组成与净化。",
                         "sub": ["水的组成", "化学式", "化合价", "水的净化", "爱护水资源"]},
                        {"id": "ju-chem-g9-u5", "title": "化学方程式", "goals": "会书写与配平方程式。",
                         "sub": ["质量守恒", "方程式书写", "配平", "计算", "依据"]},
                        {"id": "ju-chem-g9-u6", "title": "碳和碳的氧化物", "goals": "掌握碳及其化合物。",
                         "sub": ["碳单质", "二氧化碳", "一氧化碳", "制取CO2", "温室效应"]},
                        {"id": "ju-chem-g9-u7", "title": "燃料及其利用", "goals": "理解燃烧与能源。",
                         "sub": ["燃烧条件", "灭火", "燃料", "热量", "新能源"]},
                        {"id": "ju-chem-g9-u8", "title": "金属和金属材料", "goals": "认识金属性质与冶炼。",
                         "sub": ["金属物理性", "金属化学性", "金属活动性", "铁的冶炼", "锈蚀与防护"]},
                        {"id": "ju-chem-g9-u9", "title": "溶液", "goals": "理解溶液与溶解度。",
                         "sub": ["溶液组成", "溶解度", "溶质质量分数", "配制溶液", "结晶"]},
                        {"id": "ju-chem-g9-u10", "title": "酸和碱", "goals": "掌握酸碱性质。",
                         "sub": ["酸碱指示剂", "常见酸", "常见碱", "中和反应", "pH"]},
                        {"id": "ju-chem-g9-u11", "title": "盐 化肥", "goals": "认识盐与化肥。",
                         "sub": ["生活中盐", "复分解", "化肥种类", "粗盐提纯", "离子检验"]},
                        {"id": "ju-chem-g9-u12", "title": "化学与生活", "goals": "了解化学与人体健康。",
                         "sub": ["营养物质", "元素与健康", "有机合成材料", "白色污染", "安全常识"]},
                    ]},
                ]
            },
            # ---------------- 初中生物（七、八年级） ----------------
            {
                "name": "生物",
                "grades": [
                    {"grade": "七年级", "topics": [
                        {"id": "ju-bio-g7-u1", "title": "认识生物", "goals": "区分生物与非生物。",
                         "sub": ["生物特征", "调查周边", "观察方法", "归类", "生物与环境"]},
                        {"id": "ju-bio-g7-u2", "title": "了解生物圈", "goals": "认识生物圈与环境。",
                         "sub": ["生物圈", "环境关系", "生态系统", "食物链", "保护"]},
                        {"id": "ju-bio-g7-u3", "title": "细胞是基本单位", "goals": "认识细胞结构与功能。",
                         "sub": ["显微镜", "植物细胞", "动物细胞", "细胞结构", "单细胞生物"]},
                        {"id": "ju-bio-g7-u4", "title": "细胞怎样构成生物体", "goals": "理解组织器官系统。",
                         "sub": ["细胞分裂", "组织", "器官", "系统", "多细胞"]},
                        {"id": "ju-bio-g7-u5", "title": "绿色植物", "goals": "理解植物类群与生理。",
                         "sub": ["藻类苔藓蕨类", "种子植物", "蒸腾作用", "光合作用", "呼吸作用"]},
                        {"id": "ju-bio-g7-u6", "title": "绿色植物与生物圈", "goals": "认识植物在生物圈作用。",
                         "sub": ["水循环", "碳氧平衡", "绿化", "爱护植被", "环保"]},
                    ]},
                    {"grade": "八年级", "topics": [
                        {"id": "ju-bio-g8-u1", "title": "动物的主要类群", "goals": "了解无脊椎与脊椎动物。",
                         "sub": ["腔肠扁形", "线形环节", "软体节肢", "鱼", "鸟和哺乳动物"]},
                        {"id": "ju-bio-g8-u2", "title": "动物的运动和行为", "goals": "理解运动与行为。",
                         "sub": ["运动系统", "骨连结", "先天性行为", "学习行为", "社会行为"]},
                        {"id": "ju-bio-g8-u3", "title": "动物在生物圈作用", "goals": "认识动物生态作用。",
                         "sub": ["生态平衡", "物质循环", "植物传粉", "仿生", "保护"]},
                        {"id": "ju-bio-g8-u4", "title": "细菌和真菌", "goals": "认识微生物。",
                         "sub": ["细菌", "真菌", "病毒", "发酵", "食品保存"]},
                        {"id": "ju-bio-g8-u5", "title": "病毒", "goals": "了解病毒结构与生活。",
                         "sub": ["病毒形态", "结构", "生活方式", "与人类关系", "疫苗"]},
                        {"id": "ju-bio-g8-u6", "title": "生物的多样性", "goals": "理解分类与保护。",
                         "sub": ["分类依据", "生物多样性", "基因多样性", "保护", "自然保护区"]},
                        {"id": "ju-bio-g8-u7", "title": "生物的生殖和发育", "goals": "了解生殖发育。",
                         "sub": ["植物的生殖", "昆虫生殖", "两栖生殖", "鸟的生殖", "嫁接扦插"]},
                        {"id": "ju-bio-g8-u8", "title": "生物的遗传与变异", "goals": "理解遗传变异。",
                         "sub": ["基因DNA", "染色体", "性状遗传", "变异", "禁止近亲"]},
                        {"id": "ju-bio-g8-u9", "title": "生命的起源和进化", "goals": "了解进化理论。",
                         "sub": ["起源", "化石", "进化历程", "自然选择", "人类起源"]},
                    ]},
                ]
            },
            # ---------------- 初中历史 ----------------
            {
                "name": "历史",
                "grades": [
                    {"grade": "七年级", "topics": [
                        {"id": "ju-his-g7-u1", "title": "史前时期与早期国家", "goals": "了解远古人类与夏商周。",
                         "sub": ["元谋人北京人", "原始农耕", "炎黄", "夏朝", "商周"]},
                        {"id": "ju-his-g7-u2", "title": "夏商周时期", "goals": "理解早期国家与青铜文明。",
                         "sub": ["青铜器", "甲骨文", "分封制", "春秋战国", "社会变革"]},
                        {"id": "ju-his-g7-u3", "title": "秦汉时期", "goals": "统一多民族国家建立。",
                         "sub": ["秦统一", "中央集权", "汉武帝", "丝绸之路", "秦汉文化"]},
                        {"id": "ju-his-g7-u4", "title": "三国两晋南北朝", "goals": "了解政权分立与民族交融。",
                         "sub": ["三国鼎立", "西晋", "北方民族", "江南开发", "北魏孝文帝"]},
                        {"id": "ju-his-g7-u5", "title": "隋唐时期", "goals": "繁荣与开放的时代。",
                         "sub": ["隋朝", "贞观之治", "开元盛世", "唐朝民族", "隋唐文化"]},
                        {"id": "ju-his-g7-u6", "title": "宋元时期", "goals": "民族关系与社会变化。",
                         "sub": ["北宋", "辽西夏金", "元朝", "经济重心南移", "宋元文化"]},
                        {"id": "ju-his-g7-u7", "title": "明清时期", "goals": "统一多民族国家巩固。",
                         "sub": ["明朝", "清朝", "郑和下西洋", "边疆治理", "明清文化"]},
                    ]},
                    {"grade": "八年级", "topics": [
                        {"id": "ju-his-g8-u1", "title": "中国开始沦为半殖民地", "goals": "理解近代变局开端。",
                         "sub": ["鸦片战争", "南京条约", "第二次鸦片", "沙俄侵略", "太平天国"]},
                        {"id": "ju-his-g8-u2", "title": "近代化早期探索", "goals": "了解洋务与维新。",
                         "sub": ["洋务运动", "甲午战争", "戊戌变法", "边疆危机", "实业救国"]},
                        {"id": "ju-his-g8-u3", "title": "辛亥革命与民国", "goals": "理解辛亥革命意义。",
                         "sub": ["孙中山", "辛亥革命", "中华民国", "北洋军阀", "社会习俗"]},
                        {"id": "ju-his-g8-u4", "title": "新民主主义革命的开始", "goals": "了解五四运动与中共诞生。",
                         "sub": ["新文化运动", "五四运动", "中共一大", "工人运动", "黄埔军校"]},
                        {"id": "ju-his-g8-u5", "title": "从国共合作到抗战", "goals": "理解国民革命与抗战。",
                         "sub": ["北伐", "南昌起义", "长征", "九一八", "西安事变"]},
                        {"id": "ju-his-g8-u6", "title": "抗日战争", "goals": "了解全民族抗战。",
                         "sub": ["七七事变", "正面战场", "敌后战场", "重要战役", "胜利意义"]},
                        {"id": "ju-his-g8-u7", "title": "解放战争", "goals": "理解解放战争进程。",
                         "sub": ["重庆谈判", "内战爆发", "战略反攻", "三大战役", "新中国成立"]},
                        {"id": "ju-his-g8-u8", "title": "近代经济与社会生活", "goals": "了解近代社会变迁。",
                         "sub": ["民族工业", "社会生活", "教育文化", "交通通讯", "变迁原因"]},
                    ]},
                    {"grade": "九年级", "topics": [
                        {"id": "ju-his-g9-u1", "title": "古代亚非欧文明", "goals": "了解大河与海洋文明。",
                         "sub": ["古代埃及", "两河流域", "古代印度", "希腊", "罗马"]},
                        {"id": "ju-his-g9-u2", "title": "中古世界", "goals": "理解封建与宗教。",
                         "sub": ["法兰克", "庄园", "城市", "阿拉伯", "日本大化改新"]},
                        {"id": "ju-his-g9-u3", "title": "走向近代", "goals": "了解资本主义萌芽。",
                         "sub": ["文艺复兴", "新航路", "早期殖民", "三角贸易", "资本原始积累"]},
                        {"id": "ju-his-g9-u4", "title": "资本主义制度确立", "goals": "理解革命与改革。",
                         "sub": ["英国革命", "美国独立", "法国大革命", "拿破仑", "资产阶级革命"]},
                        {"id": "ju-his-g9-u5", "title": "工业革命与殖民", "goals": "了解工业革命影响。",
                         "sub": ["第一次工业", "第二次工业", "殖民扩张", "马克思主义", "工人运动"]},
                        {"id": "ju-his-g9-u6", "title": "战争与格局", "goals": "理解两次世界大战。",
                         "sub": ["一战", "凡尔赛华盛顿", "二战", "联合国", "冷战"]},
                        {"id": "ju-his-g9-u7", "title": "战后世界发展", "goals": "了解现代世界格局。",
                         "sub": ["冷战对峙", "多极化", "经济全球化", "科技革命", "当代问题"]},
                    ]},
                ]
            },
            # ---------------- 初中地理 ----------------
            {
                "name": "地理",
                "grades": [
                    {"grade": "七年级", "topics": [
                        {"id": "ju-geo-g7-u1", "title": "地球和地图", "goals": "认识地球与地图阅读。",
                         "sub": ["地球形状大小", "经纬网", "地球运动", "地图三要素", "等高线"]},
                        {"id": "ju-geo-g7-u2", "title": "陆地和海洋", "goals": "了解海陆分布与变迁。",
                         "sub": ["七大洲", "四大洋", "板块运动", "海陆变迁", "火山地震"]},
                        {"id": "ju-geo-g7-u3", "title": "天气与气候", "goals": "理解气候类型与分布。",
                         "sub": ["天气", "气温", "降水", "气候类型", "影响气候因素"]},
                        {"id": "ju-geo-g7-u4", "title": "居民与聚落", "goals": "了解人口与聚落。",
                         "sub": ["人口与人种", "语言宗教", "聚落", "发展差异", "地域联系"]},
                        {"id": "ju-geo-g7-u5", "title": "亚洲", "goals": "认识亚洲自然人文。",
                         "sub": ["位置范围", "地形河流", "气候", "人文", "分区"]},
                        {"id": "ju-geo-g7-u6", "title": "我们邻近的地区和国家", "goals": "了解日本、东南亚等。",
                         "sub": ["日本", "东南亚", "印度", "俄罗斯", "区域特征"]},
                        {"id": "ju-geo-g7-u7", "title": "东半球其他国家和地区", "goals": "认识中东、欧洲等。",
                         "sub": ["中东", "欧洲西部", "撒哈拉以南非洲", "澳大利亚", "区域比较"]},
                        {"id": "ju-geo-g7-u8", "title": "西半球的国家", "goals": "了解美国、巴西。",
                         "sub": ["美国", "巴西", "南北差异", "自然环境", "经济发展"]},
                        {"id": "ju-geo-g7-u9", "title": "极地地区", "goals": "了解两极地区。",
                         "sub": ["南极", "北极", "科考", "环境", "保护"]},
                    ]},
                    {"grade": "八年级", "topics": [
                        {"id": "ju-geo-g8-u1", "title": "从世界看中国", "goals": "认识位置与行政区划。",
                         "sub": ["位置优越", "疆域", "行政区划", "人口", "民族"]},
                        {"id": "ju-geo-g8-u2", "title": "中国的自然环境", "goals": "理解地形气候河流。",
                         "sub": ["地形地势", "气候", "河流", "长江", "黄河"]},
                        {"id": "ju-geo-g8-u3", "title": "中国的自然资源", "goals": "了解资源分布与保护。",
                         "sub": ["土地资源", "水资源", "自然资源", "短缺原因", "保护措施"]},
                        {"id": "ju-geo-g8-u4", "title": "中国的经济发展", "goals": "理解交通与产业。",
                         "sub": ["交通运输", "农业", "工业", "分布", "因地制宜"]},
                        {"id": "ju-geo-g8-u5", "title": "中国的地理差异", "goals": "认识四大地理区域。",
                         "sub": ["南北差异", "秦岭淮河", "四大区域", "各区域特征", "界线"]},
                        {"id": "ju-geo-g8-u6", "title": "北方地区", "goals": "了解北方地区特征。",
                         "sub": ["自然特征", "东北", "华北", "黄土高原", "京津"]},
                        {"id": "ju-geo-g8-u7", "title": "南方地区", "goals": "了解南方地区特征。",
                         "sub": ["自然特征", "长江三角洲", "港澳", "台湾", "西南"]},
                        {"id": "ju-geo-g8-u8", "title": "西北与青藏地区", "goals": "了解西北青藏特征。",
                         "sub": ["西北地区", "塔里木", "青藏地区", "三江源", "生态保护"]},
                    ]},
                ]
            },
            # ---------------- 初中道德与法治 ----------------
            {
                "name": "道德与法治",
                "grades": [
                    {"grade": "七年级", "topics": [
                        {"id": "ju-moral-g7-u1", "title": "成长的节拍", "goals": "认识自我，学会学习。",
                         "sub": ["中学时代", "认识自己", "做更好的自己", "学习伴成长", "享受学习"]},
                        {"id": "ju-moral-g7-u2", "title": "友谊与成长同行", "goals": "理解友谊与交往。",
                         "sub": ["和朋友一起", "深深浅浅话友谊", "交友的智慧", "网络交往", "呵护友谊"]},
                        {"id": "ju-moral-g7-u3", "title": "师长情谊", "goals": "学会与师长和家人相处。",
                         "sub": ["师生交往", "家的意味", "爱在家人间", "沟通传递爱", "孝亲敬长"]},
                        {"id": "ju-moral-g7-u4", "title": "生命的思考", "goals": "理解生命价值。",
                         "sub": ["生命至上", "敬畏生命", "守护生命", "绽放生命", "人生意义"]},
                        {"id": "ju-moral-g7-u5", "title": "在集体中成长", "goals": "理解个人与集体的关系。",
                         "sub": ["集体生活", "个人的力量", "集体的力量", "共建集体", "角色与责任"]},
                        {"id": "ju-moral-g7-u6", "title": "走进法治天地", "goals": "初步认识法律与自我保护。",
                         "sub": ["法律特征", "法律作用", "特殊保护", "学会依法办事", "树立法治意识"]},
                    ]},
                    {"grade": "八年级", "topics": [
                        {"id": "ju-moral-g8-u1", "title": "走进社会生活", "goals": "理解个人与社会关系。",
                         "sub": ["丰富的社会", "社会化", "网络生活", "合理利用网络", "媒介素养"]},
                        {"id": "ju-moral-g8-u2", "title": "遵守社会规则", "goals": "理解规则与秩序。",
                         "sub": ["社会秩序", "社会规则", "尊重他人", "以礼待人", "诚实守信"]},
                        {"id": "ju-moral-g8-u3", "title": "勇担社会责任", "goals": "树立责任与奉献意识。",
                         "sub": ["责任与角色", "责任选择", "关爱他人", "服务社会", "奉献"]},
                        {"id": "ju-moral-g8-u4", "title": "维护国家利益", "goals": "理解国家利益与安全。",
                         "sub": ["国家利益", "国家安全", "人民军队", "建设祖国", "少年担当"]},
                        {"id": "ju-moral-g8-u5", "title": "理解权利义务", "goals": "认识公民权利与义务。",
                         "sub": ["公民权利", "依法行使权利", "公民义务", "权利义务统一", "依法维权"]},
                        {"id": "ju-moral-g8-u6", "title": "人民当家作主", "goals": "理解国家制度与法治精神。",
                         "sub": ["政治制度", "国家机构", "崇尚法治", "尊重自由", "平等公正"]},
                    ]},
                    {"grade": "九年级", "topics": [
                        {"id": "ju-moral-g9-u1", "title": "富强与创新", "goals": "理解改革开放与创新。",
                         "sub": ["改革开放", "走向共同富裕", "创新强国", "万众创新", "高质量发展"]},
                        {"id": "ju-moral-g9-u2", "title": "民主与法治", "goals": "理解社会主义民主与法治。",
                         "sub": ["新型民主", "参与民主生活", "法治中国", "厉行法治", "依法行政"]},
                        {"id": "ju-moral-g9-u3", "title": "文明与家园", "goals": "理解文化与生态文明。",
                         "sub": ["中华文化", "美德精神", "社会主义核心价值观", "生态文明", "绿色发展"]},
                        {"id": "ju-moral-g9-u4", "title": "和谐与梦想", "goals": "理解民族、统一与梦想。",
                         "sub": ["民族团结", "祖国统一", "中国梦", "少年当自强", "人类命运共同体"]},
                        {"id": "ju-moral-g9-u5", "title": "我们共同的世界", "goals": "理解世界趋势与全球责任。",
                         "sub": ["世界多极化", "经济全球化", "文化多样性", "构建人类命运共同体", "中国担当"]},
                        {"id": "ju-moral-g9-u6", "title": "走向未来的少年", "goals": "做好升学与职业准备。",
                         "sub": ["走向世界", "少年担当", "学习与选择", "职业规划", "畅想未来"]},
                    ]},
                ]
            },
        ]
    },
    # ============================== 高中 ==============================
    {
        "stage": "高中",
        "subjects": [
            # ---------------- 高中语文 ----------------
            {
                "name": "语文",
                "grades": [
                    {"grade": "高一", "topics": [
                        {"id": "se-lang-g10-u1", "title": "必修上·青春激扬", "goals": "感受青春情怀，学习诗歌与小说。",
                         "sub": ["沁园春·长沙", "立在地球边上放号", "红烛", "百合花", "如何写诗歌评论"]},
                        {"id": "se-lang-g10-u2", "title": "必修上·劳动光荣", "goals": "体会劳动价值，学习通讯与文言。",
                         "sub": ["喜看稻菽千重浪", "心有一团火", "‘探界者’钟扬", "《诗经·芣苢》", "文言短文"]},
                        {"id": "se-lang-g10-u3", "title": "必修上·诗意人生", "goals": "诵读古诗词，理解情志。",
                         "sub": ["短歌行", "归园田居", "梦游天姥吟留别", "登高", "琵琶行"]},
                        {"id": "se-lang-g10-u4", "title": "必修上·自然情怀", "goals": "学习写景抒情散文。",
                         "sub": ["故都的秋", "荷塘月色", "我与地坛", "赤壁赋", "情景交融"]},
                        {"id": "se-lang-g10-u5", "title": "必修上·乡土文化", "goals": "理解乡土社会与节俗。",
                         "sub": ["乡土中国（整本书）", "节俗文化", "家乡文化生活", "调查报告", "参与家乡"]},
                        {"id": "se-lang-g10-u6", "title": "必修下·文明对话", "goals": "了解中外文化，学习说理。",
                         "sub": ["论语", "孟子", "庄子", "谏逐客书", "议论文基础"]},
                        {"id": "se-lang-g10-u7", "title": "必修下·探索与发现", "goals": "学习科普与科学精神。",
                         "sub": ["青蒿素", "一名物理学家的教育历程", "中国建筑的特征", "说‘木叶’", "说明与阐释"]},
                        {"id": "se-lang-g10-u8", "title": "必修下·小说与戏剧", "goals": "鉴赏小说戏剧，学习形象。",
                         "sub": ["林黛玉进贾府", "祝福", "雷雨", "哈姆莱特", "文学短评"]},
                    ]},
                    {"grade": "高二", "topics": [
                        {"id": "se-lang-g11-u1", "title": "选必上·革命文化", "goals": "理解革命精神与家国之思。",
                         "sub": ["中国人民站起来了", "长征胜利", "别了，不列颠尼亚", "县委书记的榜样", "红色文化"]},
                        {"id": "se-lang-g11-u2", "title": "选必上·百家争鸣", "goals": "研读诸子散文，体会思想。",
                         "sub": ["论语十二章", "大学之道", "人皆有不忍人之心", "老子四章", "庄子"]},
                        {"id": "se-lang-g11-u3", "title": "选必中·理论思考", "goals": "学习论证与思辨。",
                         "sub": ["社会历史的决定性基础", "改造我们的学习", "人的正确思想", "论证方法"]},
                        {"id": "se-lang-g11-u4", "title": "选必中·红色经典", "goals": "研读革命文学。",
                         "sub": ["包身工", "记念刘和珍君", "为了忘却的纪念", "小二黑结婚", "报告文学"]},
                        {"id": "se-lang-g11-u5", "title": "选必下·诗意栖居", "goals": "深入鉴赏古典诗词。",
                         "sub": ["氓", "离骚", "孔雀东南飞", "蜀道难", "诗词鉴赏方法"]},
                        {"id": "se-lang-g11-u6", "title": "选必下·文苑漫步", "goals": "研读散文与文言。",
                         "sub": ["陈情表", "项脊轩志", "兰亭集序", "归去来兮辞", "文言虚词"]},
                    ]},
                    {"grade": "高三", "topics": [
                        {"id": "se-lang-g12-u1", "title": "高考古诗文默写与鉴赏", "goals": "强化背诵与鉴赏。",
                         "sub": ["必背篇目", "默写易错", "诗歌鉴赏", "文言文翻译", "文化常识"]},
                        {"id": "se-lang-g12-u2", "title": "高考现代文阅读", "goals": "掌握各类文本答题策略。",
                         "sub": ["论述类", "实用类", "文学类", "信息性阅读", "答题模板"]},
                        {"id": "se-lang-g12-u3", "title": "高考作文升格", "goals": "提升立意、结构与语言。",
                         "sub": ["审题立意", "结构布局", "素材运用", "语言升格", "卷面书写"]},
                        {"id": "se-lang-g12-u4", "title": "高考语言运用", "goals": "强化语用题训练。",
                         "sub": ["成语病句", "连贯得体", "语段压缩", "图文转换", "逻辑补写"]},
                        {"id": "se-lang-g12-u5", "title": "高考综合模拟", "goals": "综合套卷与查漏补缺。",
                         "sub": ["套卷训练", "时间分配", "易错梳理", "心态调整", "考前策略"]},
                    ]},
                ]
            },
            # ---------------- 高中数学 ----------------
            {
                "name": "数学",
                "grades": [
                    {"grade": "高一", "topics": [
                        {"id": "se-math-g10-u1", "title": "必修一·集合与常用逻辑", "goals": "理解集合与充要条件。",
                         "sub": ["集合概念", "集合运算", "充要条件", "全称量词", "命题"]},
                        {"id": "se-math-g10-u2", "title": "必修一·一元二次函数与不等式", "goals": "掌握不等式与函数。",
                         "sub": ["不等式性质", "一元二次", "基本不等式", "二次函数", "应用"]},
                        {"id": "se-math-g10-u3", "title": "必修一·函数概念与性质", "goals": "理解函数本质。",
                         "sub": ["函数概念", "单调性", "奇偶性", "值域", "函数图像"]},
                        {"id": "se-math-g10-u4", "title": "必修一·基本初等函数", "goals": "掌握指数对数幂函数。",
                         "sub": ["指数", "指数函数", "对数", "对数函数", "幂函数"]},
                        {"id": "se-math-g10-u5", "title": "必修二·立体几何初步", "goals": "认识空间几何体。",
                         "sub": ["空间点线面", "平行", "垂直", "表面积体积", "三视图"]},
                        {"id": "se-math-g10-u6", "title": "必修二·统计", "goals": "理解统计基本方法。",
                         "sub": ["抽样", "统计图表", "数字特征", "百分位数", "数据分析"]},
                        {"id": "se-math-g10-u7", "title": "必修二·概率", "goals": "理解事件与概率。",
                         "sub": ["随机事件", "古典概型", "频率", "对立互斥", "概率应用"]},
                        {"id": "se-math-g10-u8", "title": "必修二·平面向量及其应用", "goals": "掌握向量运算。",
                         "sub": ["向量概念", "线性运算", "数量积", "坐标表示", "解三角形"]},
                    ]},
                    {"grade": "高二", "topics": [
                        {"id": "se-math-g11-u1", "title": "选择性必修一·空间向量", "goals": "用向量法解立体几何。",
                         "sub": ["空间向量", "运算", "法向量", "夹角距离", "坐标法"]},
                        {"id": "se-math-g11-u2", "title": "选择性必修一·直线与圆", "goals": "掌握解析几何基础。",
                         "sub": ["直线与方程", "圆与方程", "位置关系", "距离公式", "应用"]},
                        {"id": "se-math-g11-u3", "title": "选择性必修一·圆锥曲线", "goals": "理解椭圆抛物线双曲线。",
                         "sub": ["椭圆", "双曲线", "抛物线", "离心率", "标准方程"]},
                        {"id": "se-math-g11-u4", "title": "选择性必修二·数列", "goals": "掌握等差等比数列。",
                         "sub": ["数列概念", "等差数列", "等比数列", "求和", "数学归纳法"]},
                        {"id": "se-math-g11-u5", "title": "选择性必修二·导数及其应用", "goals": "掌握导数与单调性。",
                         "sub": ["导数概念", "求导公式", "单调性", "极值最值", "实际优化"]},
                        {"id": "se-math-g11-u6", "title": "选择性必修三·计数原理", "goals": "理解排列组合与二项式。",
                         "sub": ["分类加法", "排列", "组合", "二项式定理", "应用"]},
                        {"id": "se-math-g11-u7", "title": "选择性必修三·随机变量", "goals": "理解随机变量与分布。",
                         "sub": ["随机变量", "分布列", "期望方差", "二项分布", "正态分布"]},
                    ]},
                    {"grade": "高三", "topics": [
                        {"id": "se-math-g12-u1", "title": "高考函数与导数综合", "goals": "整合函数导数大题。",
                         "sub": ["函数性质", "导数应用", "不等式证明", "压轴策略", "分类讨论"]},
                        {"id": "se-math-g12-u2", "title": "高考解析几何综合", "goals": "强化圆锥曲线大题。",
                         "sub": ["联立方程", "弦长面积", "定点定值", "最值", "运算技巧"]},
                        {"id": "se-math-g12-u3", "title": "高考立体几何综合", "goals": "空间向量与证明。",
                         "sub": ["平行垂直证明", "空间角", "空间距离", "建系方法", "规范表达"]},
                        {"id": "se-math-g12-u4", "title": "高考概率统计综合", "goals": "强化概率统计应用。",
                         "sub": ["分布列", "期望", "回归相关", "统计案例", "建模"]},
                        {"id": "se-math-g12-u5", "title": "高考数列与三角综合", "goals": "整合数列三角函数。",
                         "sub": ["数列求和", "解三角形", "三角变换", "综合题", "易错点"]},
                        {"id": "se-math-g12-u6", "title": "高考模拟与查漏", "goals": "套卷训练与查漏补缺。",
                         "sub": ["套卷", "时间分配", "易错梳理", "应试策略", "心态"]},
                    ]},
                ]
            },
            # ---------------- 高中英语 ----------------
            {
                "name": "英语",
                "lang": "en",
                "grades": [
                    {"grade": "高一", "topics": [
                        {"id": "se-eng-g10-u1", "title": "必修一·Welcome Unit", "goals": "Get ready for high school life.",
                         "sub": ["Register", "Classroom English", "Describe people", "Learning styles", "Be a freshman"]},
                        {"id": "se-eng-g10-u2", "title": "必修一·Teenage Life", "goals": "Talk about school life and clubs.",
                         "sub": ["School clubs", "Adolescence", "Preferences", "Advise a friend", "The -ing form"]},
                        {"id": "se-eng-g10-u3", "title": "必修一·Travelling", "goals": "Talk about travel experiences.",
                         "sub": ["Places of interest", "Travel plans", "Past experiences", "Narration", "The passive"]},
                        {"id": "se-eng-g10-u4", "title": "必修一·Natural Disasters", "goals": "Describe disasters and news.",
                         "sub": ["Disasters", "News report", "Past perfect", "First aid", "Narrative writing"]},
                        {"id": "se-eng-g10-u5", "title": "必修一·Languages Around the World", "goals": "Explore languages and culture.",
                         "sub": ["World languages", "Chinese characters", "Learning a language", "Relative clauses", "Poster"]},
                        {"id": "se-eng-g10-u6", "title": "必修二·Cultural Heritage", "goals": "Talk about protecting heritage.",
                         "sub": ["Heritage sites", "Preservation", "The passive", "News about culture", "Proposal"]},
                        {"id": "se-eng-g10-u7", "title": "必修二·Wildlife Protection", "goals": "Talk about wildlife and ecology.",
                         "sub": ["Endangered species", "To do / doing", "Report writing", "Ecosystem", "Poster"]},
                        {"id": "se-eng-g10-u8", "title": "必修二·Music & Festivals", "goals": "Talk about music and festivals.",
                         "sub": ["Music types", "Festivals", "Attributive clauses", "Preferences", "Speech"]},
                    ]},
                    {"grade": "高二", "topics": [
                        {"id": "se-eng-g11-u1", "title": "选择性必修一·Science", "goals": "Read and talk about science.",
                         "sub": ["Scientists", "The universe", "Infinitives", "Popular science", "Summary"]},
                        {"id": "se-eng-g11-u2", "title": "选择性必修一·Growing Up", "goals": "Reflect on growth and choices.",
                         "sub": ["Life choices", "Parent-child", "The -ing form", "Narrative", "Letter"]},
                        {"id": "se-eng-g11-u3", "title": "选择性必修二·Literature", "goals": "Appreciate literature and poetry.",
                         "sub": ["Short stories", "Poems", "Attributive clauses", "Appreciation", "Review"]},
                        {"id": "se-eng-g11-u4", "title": "选择性必修二·Conservation", "goals": "Discuss environmental protection.",
                         "sub": ["Habitat", "Climate", "The passive", "Argumentative", "Essay"]},
                        {"id": "se-eng-g11-u5", "title": "选择性必修三·Art & Culture", "goals": "Talk about art and traditions.",
                         "sub": ["Paintings", "Traditions", "Subjunctive mood", "Cultural essay", "Speech"]},
                        {"id": "se-eng-g11-u6", "title": "选择性必修三·Health & Life", "goals": "Discuss health and lifestyle.",
                         "sub": ["Healthy life", "Habits", "Adverbial clauses", "Advice writing", "Reflection"]},
                    ]},
                    {"grade": "高三", "topics": [
                        {"id": "se-eng-g12-u1", "title": "高考语法体系回顾", "goals": "Review all grammar systematically.",
                         "sub": ["Tenses", "Passive", "Non-finite", "Clauses", "Special patterns"]},
                        {"id": "se-eng-g12-u2", "title": "高考阅读与完形提速", "goals": "Improve reading speed and accuracy.",
                         "sub": ["Skimming scanning", "Inference", "Cloze skills", "Long sentences", "Timing"]},
                        {"id": "se-eng-g12-u3", "title": "高考书面表达模板", "goals": "Master applied and continued writing.",
                         "sub": ["Applied writing", "Narrative", "Argumentative", "Continuation", "Advanced words"]},
                        {"id": "se-eng-g12-u4", "title": "高考听力与词汇冲刺", "goals": "Boost listening and vocabulary.",
                         "sub": ["Listening drills", "High-frequency words", "Pronunciation", "Note-taking", "Mock tests"]},
                        {"id": "se-eng-g12-u5", "title": "高考综合模拟", "goals": "Full papers and strategy.",
                         "sub": ["Full papers", "Time control", "Error analysis", "Test skills", "Confidence"]},
                    ]},
                ]
            },
            # ---------------- 高中物理 ----------------
            {
                "name": "物理",
                "grades": [
                    {"grade": "高一", "topics": [
                        {"id": "se-phy-g10-u1", "title": "必修一·运动的描述", "goals": "理解运动学基本概念。",
                         "sub": ["质点参考系", "时间位移", "速度", "加速度", "图像"]},
                        {"id": "se-phy-g10-u2", "title": "必修一·匀变速直线运动", "goals": "掌握运动学公式。",
                         "sub": ["速度时间关系", "位移公式", "推论", "自由落体", "实验"]},
                        {"id": "se-phy-g10-u3", "title": "必修一·力与平衡", "goals": "理解力的合成与分解。",
                         "sub": ["重力弹力摩擦力", "合成分解", "共点力平衡", "受力分析", "应用"]},
                        {"id": "se-phy-g10-u4", "title": "必修一·牛顿运动定律", "goals": "掌握牛顿三定律应用。",
                         "sub": ["牛顿第一定律", "第二定律", "第三定律", "两类问题", "连接体"]},
                        {"id": "se-phy-g10-u5", "title": "必修二·曲线运动", "goals": "理解抛体与圆周运动。",
                         "sub": ["曲线条件", "平抛", "圆周运动", "向心加速度", "向心力"]},
                        {"id": "se-phy-g10-u6", "title": "必修二·万有引力", "goals": "理解天体运动。",
                         "sub": ["万有引力定律", "天体质量", "宇宙速度", "卫星", "时空观"]},
                        {"id": "se-phy-g10-u7", "title": "必修二·机械能守恒", "goals": "理解功与能量。",
                         "sub": ["功", "功率", "动能定理", "机械能守恒", "能量转化"]},
                        {"id": "se-phy-g10-u8", "title": "必修三·电场", "goals": "认识电场与电势。",
                         "sub": ["电荷库仑", "电场强度", "电势差", "电容", "带电粒子"]},
                        {"id": "se-phy-g10-u9", "title": "必修三·电路", "goals": "掌握直流电路。",
                         "sub": ["电流电阻", "欧姆定律", "串并联", "电功率", "闭合电路"]},
                        {"id": "se-phy-g10-u10", "title": "必修三·能源与电磁", "goals": "理解磁场与电磁感应初步。",
                         "sub": ["磁场", "磁感线", "电磁感应", "交变电流", "能源"]},
                    ]},
                    {"grade": "高二", "topics": [
                        {"id": "se-phy-g11-u1", "title": "选择性必修一·动量", "goals": "掌握动量守恒。",
                         "sub": ["动量", "冲量", "动量定理", "动量守恒", "碰撞"]},
                        {"id": "se-phy-g11-u2", "title": "选择性必修一·机械振动", "goals": "理解简谐运动。",
                         "sub": ["简谐运动", "弹簧振子", "单摆", "受迫振动", "共振"]},
                        {"id": "se-phy-g11-u3", "title": "选择性必修一·机械波", "goals": "理解波的传播。",
                         "sub": ["波的形成", "波长频率", "干涉", "衍射", "多普勒"]},
                        {"id": "se-phy-g11-u4", "title": "选择性必修一·光", "goals": "理解几何与物理光学。",
                         "sub": ["折射", "全反射", "干涉衍射", "光的本性", "色散"]},
                        {"id": "se-phy-g11-u5", "title": "选择性必修二·磁场", "goals": "深入磁场与电磁感应。",
                         "sub": ["安培力", "洛伦兹力", "带电粒子", "电磁感应", "自感"]},
                        {"id": "se-phy-g11-u6", "title": "选择性必修二·交变电流", "goals": "理解交流电路。",
                         "sub": ["正弦交流", "有效值", "变压器", "远距离输电", "应用"]},
                        {"id": "se-phy-g11-u7", "title": "选择性必修三·热学", "goals": "理解分子动理论与气体。",
                         "sub": ["分子动理论", "内能", "气体实验定律", "热力学定律", "熵"]},
                        {"id": "se-phy-g11-u8", "title": "选择性必修三·原子物理", "goals": "了解原子与原子核。",
                         "sub": ["原子结构", "玻尔模型", "放射性", "核反应", "核能"]},
                    ]},
                    {"grade": "高三", "topics": [
                        {"id": "se-phy-g12-u1", "title": "高考力学主干整合", "goals": "整合运动学与动力学。",
                         "sub": ["受力分析", "牛顿定律", "能量", "动量", "综合题"]},
                        {"id": "se-phy-g12-u2", "title": "高考电磁学主干整合", "goals": "整合电场磁场电路。",
                         "sub": ["电场", "电路", "磁场", "电磁感应", "综合计算"]},
                        {"id": "se-phy-g12-u3", "title": "高考实验专题", "goals": "突破力学电学实验。",
                         "sub": ["力学实验", "电学实验", "误差分析", "数据处理", "设计实验"]},
                        {"id": "se-phy-g12-u4", "title": "高考建模与综合计算", "goals": "提升建模能力。",
                         "sub": ["过程模型", "对象模型", "临界问题", "压轴题", "规范表达"]},
                        {"id": "se-phy-g12-u5", "title": "高考模拟与查漏", "goals": "套卷训练与查漏。",
                         "sub": ["套卷", "时间分配", "易错梳理", "应试策略", "心态"]},
                    ]},
                ]
            },
            # ---------------- 高中化学 ----------------
            {
                "name": "化学",
                "grades": [
                    {"grade": "高一", "topics": [
                        {"id": "se-chem-g10-u1", "title": "必修一·物质分类与转化", "goals": "理解物质分类与反应。",
                         "sub": ["物质分类", "胶体", "离子反应", "氧化还原反应", "转化"]},
                        {"id": "se-chem-g10-u2", "title": "必修一·钠和氯", "goals": "掌握钠、氯及其化合物。",
                         "sub": ["钠", "碳酸钠碳酸氢钠", "氯气", "次氯酸", "应用"]},
                        {"id": "se-chem-g10-u3", "title": "必修一·金属材料与海水资源", "goals": "认识铁、铝与资源。",
                         "sub": ["铁", "铝", "合金", "海水元素", "资源利用"]},
                        {"id": "se-chem-g10-u4", "title": "必修二·元素周期律", "goals": "理解周期律与结构。",
                         "sub": ["原子结构", "周期表", "周期律", "化学键", "分子结构"]},
                        {"id": "se-chem-g10-u5", "title": "必修二·化工生产", "goals": "了解重要化工原理。",
                         "sub": ["硫和氮", "硫酸硝酸", "氨", "纯碱工业", "绿色化学"]},
                        {"id": "se-chem-g10-u6", "title": "必修二·有机化合物", "goals": "认识常见有机物。",
                         "sub": ["甲烷", "乙烯", "乙醇乙酸", "基本营养", "高分子"]},
                        {"id": "se-chem-g10-u7", "title": "必修二·化学反应与能量", "goals": "理解速率、限度与能量。",
                         "sub": ["反应速率", "反应限度", "原电池", "化学能", "新能源"]},
                    ]},
                    {"grade": "高二", "topics": [
                        {"id": "se-chem-g11-u1", "title": "选择性必修一·反应原理", "goals": "掌握反应速率与平衡。",
                         "sub": ["速率因素", "化学平衡", "平衡移动", "平衡常数", "图像"]},
                        {"id": "se-chem-g11-u2", "title": "选择性必修一·电离与水解", "goals": "理解电解质溶液。",
                         "sub": ["电离平衡", "水的离子积", "盐类水解", "沉淀溶解", "pH"]},
                        {"id": "se-chem-g11-u3", "title": "选择性必修一·电化学", "goals": "掌握原电池与电解。",
                         "sub": ["原电池", "电解池", "金属腐蚀", "电化学应用", "新型电池"]},
                        {"id": "se-chem-g11-u4", "title": "选择性必修二·结构基础", "goals": "理解原子与分子结构。",
                         "sub": ["电子排布", "元素性质", "共价键", "分子空间", "晶体"]},
                        {"id": "se-chem-g11-u5", "title": "选择性必修三·烃", "goals": "掌握烃类。",
                         "sub": ["烷烃", "烯烃炔烃", "芳香烃", "石油煤", "结构与性质"]},
                        {"id": "se-chem-g11-u6", "title": "选择性必修三·烃的衍生物", "goals": "认识官能团与反应。",
                         "sub": ["卤代烃", "醇酚", "醛酮", "羧酸酯", "有机合成"]},
                        {"id": "se-chem-g11-u7", "title": "选择性必修三·高分子", "goals": "了解生物大分子与材料。",
                         "sub": ["糖", "蛋白质", "核酸", "合成材料", "高分子"]},
                    ]},
                    {"grade": "高三", "topics": [
                        {"id": "se-chem-g12-u1", "title": "高考元素化合物网络", "goals": "整合金属非金属知识。",
                         "sub": ["金属网络", "非金属网络", "方程式", "转化关系", "推断"]},
                        {"id": "se-chem-g12-u2", "title": "高考反应原理综合", "goals": "强化原理大题。",
                         "sub": ["平衡图像", "速率计算", "电化学", "溶液中的离子", "综合"]},
                        {"id": "se-chem-g12-u3", "title": "高考有机推断", "goals": "突破有机推断与合成。",
                         "sub": ["官能团转化", "同分异构", "合成路线", "信息迁移", "规范表达"]},
                        {"id": "se-chem-g12-u4", "title": "高考实验设计", "goals": "提升实验探究能力。",
                         "sub": ["制备实验", "性质实验", "定量实验", "方案评价", "误差"]},
                        {"id": "se-chem-g12-u5", "title": "高考模拟与查漏", "goals": "套卷训练与查漏。",
                         "sub": ["套卷", "时间分配", "易错梳理", "应试策略", "心态"]},
                    ]},
                ]
            },
            # ---------------- 高中生物 ----------------
            {
                "name": "生物",
                "grades": [
                    {"grade": "高一", "topics": [
                        {"id": "se-bio-g10-u1", "title": "必修一·细胞的分子组成", "goals": "理解组成细胞的分子。",
                         "sub": ["元素化合物", "蛋白质", "核酸", "糖脂", "无机物"]},
                        {"id": "se-bio-g10-u2", "title": "必修一·细胞的结构", "goals": "认识细胞结构与分工。",
                         "sub": ["细胞膜", "细胞器", "细胞核", "生物膜系统", "模型建构"]},
                        {"id": "se-bio-g10-u3", "title": "必修一·细胞的代谢", "goals": "理解酶、ATP与代谢。",
                         "sub": ["酶", "ATP", "光合作用", "细胞呼吸", "影响因素"]},
                        {"id": "se-bio-g10-u4", "title": "必修一·细胞的生命历程", "goals": "理解分裂与分化。",
                         "sub": ["有丝分裂", "分化", "衰老凋亡", "癌变", "观察实验"]},
                        {"id": "se-bio-g10-u5", "title": "必修二·遗传的细胞基础", "goals": "掌握减数分裂。",
                         "sub": ["减数分裂", "配子形成", "受精", "染色体行为", "图像"]},
                        {"id": "se-bio-g10-u6", "title": "必修二·遗传的分子基础", "goals": "理解DNA与遗传信息。",
                         "sub": ["DNA结构", "复制", "基因表达", "中心法则", "基因"]},
                        {"id": "se-bio-g10-u7", "title": "必修二·遗传规律", "goals": "掌握分离与自由组合。",
                         "sub": ["分离定律", "自由组合", "伴性遗传", "系谱", "杂交实验"]},
                        {"id": "se-bio-g10-u8", "title": "必修二·变异与进化", "goals": "理解变异与育种进化。",
                         "sub": ["基因突变", "染色体变异", "育种", "现代进化理论", "物种"]},
                    ]},
                    {"grade": "高二", "topics": [
                        {"id": "se-bio-g11-u1", "title": "选择性必修一·稳态与调节", "goals": "理解个体稳态。",
                         "sub": ["内环境", "神经调节", "体液调节", "免疫调节", "稳态"]},
                        {"id": "se-bio-g11-u2", "title": "选择性必修二·生物与环境", "goals": "理解种群与生态系统。",
                         "sub": ["种群", "群落", "生态系统", "稳定性", "环境保护"]},
                        {"id": "se-bio-g11-u3", "title": "选择性必修三·生物技术与工程", "goals": "了解现代生物技术。",
                         "sub": ["发酵", "细胞工程", "基因工程", "胚胎工程", "安全伦理"]},
                        {"id": "se-bio-g11-u4", "title": "必修三·植物生命活动的调节", "goals": "理解植物激素。",
                         "sub": ["生长素", "其他激素", "环境因素", "生长调节剂", "应用"]},
                        {"id": "se-bio-g11-u5", "title": "生物技术综合实验", "goals": "掌握微生物培养与工程基础。",
                         "sub": ["无菌技术", "接种与分离", "发酵工程", "产物提取", "安全规范"]},
                        {"id": "se-bio-g11-u6", "title": "实验与探究专题", "goals": "提升实验设计与分析能力。",
                         "sub": ["探究原则", "变量控制", "数据处理", "结果分析", "误差与结论"]},
                    ]},
                    {"grade": "高三", "topics": [
                        {"id": "se-bio-g12-u1", "title": "高考分子与细胞整合", "goals": "整合必修一主干。",
                         "sub": ["分子组成", "结构与代谢", "生命历程", "实验", "长句表述"]},
                        {"id": "se-bio-g12-u2", "title": "高考遗传与进化整合", "goals": "强化遗传大题。",
                         "sub": ["遗传规律", "伴性", "变异育种", "分子基础", "概率计算"]},
                        {"id": "se-bio-g12-u3", "title": "高考稳态与生态整合", "goals": "整合调节与生态。",
                         "sub": ["神经体液免疫", "种群群落", "生态系统", "实验设计", "综合"]},
                        {"id": "se-bio-g12-u4", "title": "高考实验与长句表述", "goals": "突破实验设计与表述。",
                         "sub": ["实验原则", "变量控制", "结果分析", "长句规范", "易错辨析"]},
                        {"id": "se-bio-g12-u5", "title": "高考模拟与查漏", "goals": "套卷训练与查漏。",
                         "sub": ["套卷", "时间分配", "易错梳理", "应试策略", "心态"]},
                    ]},
                ]
            },
            # ---------------- 高中历史 ----------------
            {
                "name": "历史",
                "grades": [
                    {"grade": "高一", "topics": [
                        {"id": "se-his-g10-u1", "title": "必修一·从中华文明的起源到秦统一", "goals": "贯通早期国家与秦汉。",
                         "sub": ["远古社会", "夏商周", "春秋战国", "秦统一", "中央集权"]},
                        {"id": "se-his-g10-u2", "title": "必修一·魏晋至隋唐", "goals": "理解分裂到盛唐。",
                         "sub": ["魏晋南北朝", "隋唐制度", "民族交融", "唐朝盛世", "文化交流"]},
                        {"id": "se-his-g10-u3", "title": "必修一·宋元明清", "goals": "理解专制强化与变局。",
                         "sub": ["两宋", "元朝", "明朝", "清朝前中期", "边疆治理"]},
                        {"id": "se-his-g10-u4", "title": "必修一·晚清内忧外患", "goals": "理解近代变局。",
                         "sub": ["鸦片战争", "太平天国", "洋务运动", "甲午战争", "瓜分危机"]},
                        {"id": "se-his-g10-u5", "title": "必修一·辛亥革命与民国", "goals": "理解民国建立与曲折。",
                         "sub": ["戊戌变法", "辛亥革命", "北洋时期", "新文化运动", "五四运动"]},
                        {"id": "se-his-g10-u6", "title": "必修一·中国共产党成立与新中国", "goals": "理解革命胜利。",
                         "sub": ["中共诞生", "国民革命", "土地革命", "抗日战争", "解放战争"]},
                        {"id": "se-his-g10-u7", "title": "必修二·世界古代与近代", "goals": "了解世界文明进程。",
                         "sub": ["古代文明", "中古世界", "文艺复兴", "新航路", "资产阶级革命"]},
                        {"id": "se-his-g10-u8", "title": "必修二·工业革命与当代世界", "goals": "理解现代化与格局。",
                         "sub": ["工业革命", "殖民体系", "一战二战", "冷战", "多极化"]},
                    ]},
                    {"grade": "高二", "topics": [
                        {"id": "se-his-g11-u1", "title": "选择性必修一·国家制度", "goals": "理解政治制度演进。",
                         "sub": ["中国古代政治", "西方民主", "民国政治", "新中国制度", "比较"]},
                        {"id": "se-his-g11-u2", "title": "选择性必修一·官员选拔与监察", "goals": "了解选官与监察。",
                         "sub": ["科举", "近代选官", "西方文官", "监察制度", "反腐"]},
                        {"id": "se-his-g11-u3", "title": "选择性必修一·法律与教化", "goals": "理解法律与道德教化。",
                         "sub": ["中华法系", "西方法律", "礼教", "宗教教化", "近代转型"]},
                        {"id": "se-his-g11-u4", "title": "选择性必修二·经济与社会生活", "goals": "理解经济发展变迁。",
                         "sub": ["食物生产", "商业贸易", "交通", "居住", "医疗"]},
                        {"id": "se-his-g11-u5", "title": "选择性必修三·文化交流与传播", "goals": "理解文明交流。",
                         "sub": ["中华文化", "世界文化", "人口迁徙", "商路", "文化遗产"]},
                        {"id": "se-his-g11-u6", "title": "选择性必修三·战争与文化", "goals": "了解战争与文化碰撞。",
                         "sub": ["古代战争", "近代殖民", "一战二战", "冷战文化", "和平"]},
                    ]},
                    {"grade": "高三", "topics": [
                        {"id": "se-his-g12-u1", "title": "高考中国史时序梳理", "goals": "贯通中国古今脉络。",
                         "sub": ["古代史", "近代史", "现代史", "阶段特征", "线索"]},
                        {"id": "se-his-g12-u2", "title": "高考世界史时序梳理", "goals": "贯通世界史脉络。",
                         "sub": ["古代文明", "近代转型", "现代格局", "阶段特征", "比较"]},
                        {"id": "se-his-g12-u3", "title": "高考主干专题", "goals": "制度、经济、文化专题。",
                         "sub": ["政治制度", "经济发展", "思想文化", "民族关系", "对外"]},
                        {"id": "se-his-g12-u4", "title": "高考材料题规范", "goals": "提升材料解析能力。",
                         "sub": ["提取信息", "分析因果", "论证评价", "答题规范", "术语"]},
                        {"id": "se-his-g12-u5", "title": "高考模拟与查漏", "goals": "套卷训练与查漏。",
                         "sub": ["套卷", "时间分配", "易错梳理", "热点关联", "心态"]},
                    ]},
                ]
            },
            # ---------------- 高中地理 ----------------
            {
                "name": "地理",
                "grades": [
                    {"grade": "高一", "topics": [
                        {"id": "se-geo-g10-u1", "title": "必修一·地球运动", "goals": "理解地球运动意义。",
                         "sub": ["自转", "公转", "昼夜长短", "正午太阳高度", "四季五带"]},
                        {"id": "se-geo-g10-u2", "title": "必修一·大气", "goals": "理解大气受热与运动。",
                         "sub": ["受热过程", "热力环流", "风", "气压带风带", "季风"]},
                        {"id": "se-geo-g10-u3", "title": "必修一·水圈", "goals": "理解水循环与海洋。",
                         "sub": ["水循环", "河流", "海水运动", "洋流", "水资源"]},
                        {"id": "se-geo-g10-u4", "title": "必修一·地表形态", "goals": "理解内外力塑造。",
                         "sub": ["内力", "外力", "地貌", "岩石圈", "人类活动"]},
                        {"id": "se-geo-g10-u5", "title": "必修一·植被土壤", "goals": "认识植被与土壤。",
                         "sub": ["植被", "土壤", "地域分异", "自然带", "人地关系"]},
                        {"id": "se-geo-g10-u6", "title": "必修一·灾害", "goals": "了解自然灾害。",
                         "sub": ["气象灾害", "地质灾害", "海洋灾害", "防治", "应急"]},
                        {"id": "se-geo-g10-u7", "title": "必修二·人口", "goals": "理解人口变化。",
                         "sub": ["分布", "迁移", "容量", "人口问题", "政策"]},
                        {"id": "se-geo-g10-u8", "title": "必修二·聚落与产业", "goals": "理解城乡与产业区位。",
                         "sub": ["城乡空间", "农业区位", "工业区位", "交通区位", "服务业"]},
                        {"id": "se-geo-g10-u9", "title": "必修二·环境与区域", "goals": "理解环境与可持续发展。",
                         "sub": ["生态环境", "资源", "区域发展", "全球化", "可持续发展"]},
                    ]},
                    {"grade": "高二", "topics": [
                        {"id": "se-geo-g11-u1", "title": "选择性必修一·自然地理基础", "goals": "深化自然地理。",
                         "sub": ["地球运动", "大气环流", "水体运动", "地壳物质", "自然地理整体"]},
                        {"id": "se-geo-g11-u2", "title": "选择性必修二·区域发展", "goals": "理解区域差异与协调。",
                         "sub": ["区域差异", "生态建设", "资源开发", "协调发展", "案例"]},
                        {"id": "se-geo-g11-u3", "title": "选择性必修三·资源环境", "goals": "理解资源与环境安全。",
                         "sub": ["资源安全", "能源", "环境安全", "生态修复", "全球治理"]},
                        {"id": "se-geo-g11-u4", "title": "区域发展案例", "goals": "结合真实区域分析。",
                         "sub": ["长江经济带", "雄安新区", "西部开发", "一带一路", "区域合作"]},
                        {"id": "se-geo-g11-u5", "title": "地理信息技术应用", "goals": "了解 RS/GPS/GIS 的应用。",
                         "sub": ["遥感RS", "全球定位GPS", "地理信息系统GIS", "数字地球", "综合应用"]},
                        {"id": "se-geo-g11-u6", "title": "世界地理与国情", "goals": "认识世界与中国地理概况。",
                         "sub": ["世界地理概况", "中国地理国情", "区域对比", "发展差异", "综合分析"]},
                    ]},
                    {"grade": "高三", "topics": [
                        {"id": "se-geo-g12-u1", "title": "高考自然地理整合", "goals": "整合自然地理主干。",
                         "sub": ["地球运动", "大气", "水", "地貌", "整体性与差异"]},
                        {"id": "se-geo-g12-u2", "title": "高考人文地理整合", "goals": "整合人文地理主干。",
                         "sub": ["人口", "城市", "农业", "工业", "交通"]},
                        {"id": "se-geo-g12-u3", "title": "高考区域分析与综合题", "goals": "提升区域分析能力。",
                         "sub": ["区域定位", "特征描述", "原因分析", "综合题套路", "规范"]},
                        {"id": "se-geo-g12-u4", "title": "高考图表判读", "goals": "强化图表技能。",
                         "sub": ["等值线", "统计图", "示意图", "区域图", "提取信息"]},
                        {"id": "se-geo-g12-u5", "title": "高考模拟与查漏", "goals": "套卷训练与查漏。",
                         "sub": ["套卷", "时间分配", "易错梳理", "应试策略", "心态"]},
                    ]},
                ]
            },
            # ---------------- 高中思想政治 ----------------
            {
                "name": "思想政治",
                "grades": [
                    {"grade": "高一", "topics": [
                        {"id": "se-pol-g10-u1", "title": "必修一·中国特色社会主义", "goals": "理解中国特色社会主义历程。",
                         "sub": ["人类社会发展", "近代中国探索", "站起来富起来强起来", "新时代", "青年使命"]},
                        {"id": "se-pol-g10-u2", "title": "必修二·经济与社会", "goals": "理解基本经济制度。",
                         "sub": ["生产资料所有制", "市场经济体制", "收入分配", "社会保障", "高质量发展"]},
                        {"id": "se-pol-g10-u3", "title": "必修三·政治与法治", "goals": "理解国家制度与法治。",
                         "sub": ["人民民主专政", "人民代表大会制度", "政党制度", "民族区域自治", "依法治国"]},
                        {"id": "se-pol-g10-u4", "title": "必修四·哲学与文化", "goals": "掌握辩证唯物主义。",
                         "sub": ["唯物论", "辩证法", "认识论", "历史唯物主义", "文化传承"]},
                        {"id": "se-pol-g10-u5", "title": "必修二·新发展理念", "goals": "理解新发展理念与建设。",
                         "sub": ["创新协调", "绿色", "开放共享", "现代化", "生态文明"]},
                    ]},
                    {"grade": "高二", "topics": [
                        {"id": "se-pol-g11-u1", "title": "选择性必修一·当代国际政治", "goals": "理解国际社会。",
                         "sub": ["主权国家", "国际组织", "世界多极化", "和平发展", "人类命运共同体"]},
                        {"id": "se-pol-g11-u2", "title": "选择性必修二·法律与生活", "goals": "了解民事法律。",
                         "sub": ["民事权利", "合同", "婚姻继承", "侵权责任", "仲裁诉讼"]},
                        {"id": "se-pol-g11-u3", "title": "选择性必修三·逻辑与思维", "goals": "掌握科学思维。",
                         "sub": ["概念判断推理", "逻辑思维", "辩证思维", "创新思维", "方法"]},
                        {"id": "se-pol-g11-u4", "title": "必修四·文化交融", "goals": "理解文化交流。",
                         "sub": ["民族文化", "文化传播", "文化创新", "文化自信", "交流互鉴"]},
                        {"id": "se-pol-g11-u5", "title": "选择性必修一·走进经济全球化", "goals": "理解经济全球化与中国。",
                         "sub": ["经济全球化", "多边贸易", "国际金融", "中国与世界", "风险应对"]},
                        {"id": "se-pol-g11-u6", "title": "选择性必修一·国家的结构形式", "goals": "理解国家形式与国际组织。",
                         "sub": ["国家形式", "单一制与复合制", "国家机构", "国际组织", "中国立场"]},
                    ]},
                    {"grade": "高三", "topics": [
                        {"id": "se-pol-g12-u1", "title": "高考经济模块整合", "goals": "整合经济主干。",
                         "sub": ["基本经济制度", "市场经济", "分配", "新发展理念", "开放"]},
                        {"id": "se-pol-g12-u2", "title": "高考政治模块整合", "goals": "整合政治主干。",
                         "sub": ["政治制度", "政党", "民族宗教", "国际社会", "法治"]},
                        {"id": "se-pol-g12-u3", "title": "高考哲学模块整合", "goals": "整合哲学主干。",
                         "sub": ["唯物论", "辩证法", "认识论", "历史观", "价值观"]},
                        {"id": "se-pol-g12-u4", "title": "高考文化与热点", "goals": "链接热点与术语。",
                         "sub": ["文化自信", "时政热点", "答题术语", "模块综合", "规范"]},
                        {"id": "se-pol-g12-u5", "title": "高考模拟与查漏", "goals": "套卷训练与查漏。",
                         "sub": ["套卷", "时间分配", "易错梳理", "应试策略", "心态"]},
                    ]},
                ]
            },
        ]
    },
]


# ----------------------------- 索引 -----------------------------
def _build_index():
    index = {}
    for st in CURRICULUM:
        stage = st["stage"]
        for subj in st["subjects"]:
            subject = subj["name"]
            for g in subj["grades"]:
                grade = g["grade"]
                for tp in g["topics"]:
                    topic = dict(tp)
                    topic["stage"] = stage
                    topic["subject"] = subject
                    topic["grade"] = grade
                    topic["lang"] = subj.get("lang", "zh")
                    index[topic["id"]] = topic
    return index


# 合并拓展与素养课程（中医学 / Python / 记忆方法 / 小学英语方法）
try:
    CURRICULUM = CURRICULUM + EXTRA_CURRICULUM
except Exception:
    pass
TOPIC_INDEX = _build_index()

# 系统默认导师（user_id=0），面向 K12 学生，无需自建角色即可学习
SYSTEM_MENTOR = {
    "name": "小艾老师",
    "persona": "一位耐心、亲切、循循善诱的中小学 AI 导师。善于用生活化的类比把抽象知识讲得通俗易懂，"
               "鼓励提问、允许犯错，始终用苏格拉底式提问引导学生自己得出结论。",
    "teaching_style": "先用类比降低陌生感，再用一连串小问题拆解难点，最后让学生用自己的话复述。",
    "course": "K12 全学段课程（可在「课程目录」中选择具体学科与知识点）",
    "world_setting": "",
    "lang": "zh",
}

# 系统默认英语外教（user_id=0），全程英文对话，适合语音口语练习
ENGLISH_MENTOR = {
    "name": "Emma 老师",
    "persona": "A warm, patient native-English-speaking tutor for K12 students. You speak ONLY in English, "
               "use simple and clear words, and guide the student with Socratic questions. You gently correct "
               "their spoken or written English (pronunciation, grammar, word choice) and explain the why in "
               "plain English so they improve while talking.",
    "teaching_style": "Speak English only. Ask one small question at a time. Warmly correct mistakes and encourage "
                      "the student to speak more and think aloud.",
    "course": "English (listening, speaking, reading, writing) — pick a topic from the course catalog",
    "world_setting": "",
    "lang": "en",
}


def course_context(course_id):
    """返回某知识点的学习目标与核心内容，供注入 prompt。"""
    t = TOPIC_INDEX.get(course_id)
    if not t:
        return ""
    lines = [
        f"本次具体学习主题：{t['title']}",
        f"所属：{t['stage']} · {t['subject']} · {t['grade']}",
    ]
    if t.get("goals"):
        lines.append("学习目标：" + t["goals"])
    if t.get("sub"):
        lines.append("应覆盖的核心内容：")
        lines += ["  - " + s for s in t["sub"]]
    return "\n".join(lines)


# ----------------------------- 详细讲义（离线生成） -----------------------------
# 把每个知识点的「学习目标 + 核心内容」展开成一段结构化的课程讲义，
# 学生选课前/选课后都能直接看到“这节课到底讲什么”，无需依赖大模型密钥。
_SUBJECT_OPEN = {
    "语文": "语文学习重在积累与语感，先读懂再学着表达。",
    "数学": "数学讲究严谨的逻辑与步骤，弄懂“为什么”比背结论更重要。",
    "英语": "英语学习要多听、多读、多说，把表达放进真实语境里。",
    "物理": "物理研究自然现象背后的规律，公式要先懂物理意义再计算。",
    "化学": "化学关注物质的组成、变化与反应，注意条件和配平。",
    "生物": "生物探究生命现象与规律，善用图表理解结构与功能。",
    "历史": "历史帮我们理解过去、照见当下，按时间线梳理因果最清楚。",
    "地理": "地理连接自然与人文，离不开地图和空间想象。",
    "道德与法治": "这一课帮我们学会与人相处、理解规则与责任。",
    "思想政治": "这一课帮我们形成正确的价值观念与看待问题的方法。",
    "科学": "科学来自观察、提问与实验，从现象中归纳规律。",
}
_SUBJECT_TIP = {
    "语文": "朗读、摘抄好词好句，并尝试用自己的话复述文意。",
    "数学": "注意书写规范与步骤完整，算完顺手验算一遍。",
    "英语": "多听多读，留意发音和例句，试着用这个表达造一个自己的句子。",
    "物理": "结合生活现象理解概念，先懂物理意义再代入公式计算。",
    "化学": "记住物质的性质和反应条件，动手写方程式并注意配平。",
    "生物": "借助插图和实物观察，理解“结构决定功能”。",
    "历史": "按时间线梳理事件的起因、经过、结果和影响。",
    "地理": "多看图（地图、示意图），把文字描述和空间位置对应起来。",
    "道德与法治": "联系身边的生活与新闻事例，理解规则与价值。",
    "思想政治": "用“是什么—为什么—怎么做”的框架梳理观点。",
    "科学": "动手做小实验、认真观察记录，从现象中找规律。",
}


# ========== 各学科子知识点的详细内容库 ==========
# 格式：{(topic标题, 子知识点名): {"body": 详细讲解文字, "example": 带步骤的例题}
# 每个子知识点都有独一无二的定义、关键概念、和完整例题

_SUBTOPIC_CONTENT = {
    # ===== 长方形和正方形·周长（三年级）=====
    ("长方形和正方形", "周长"): {
        "body": (
            "【周长的定义】\n"
            "封闭图形一周的长度，叫做它的**周长**。\n\n"
            "【长方形的周长公式】\n"
            "长方形周长 = (长 + 宽) × 2，即 $C = (a + b) \\times 2$。\n"
            "推导：长方形有 2 条长、2 条宽，所以周长 = 长+宽+长+宽 = (长+宽)×2。\n\n"
            "【正方形的周长公式】\n"
            "正方形周长 = 边长 × 4，即 $C = a \\times 4$（正方形四条边都相等）。\n\n"
            "⚠️ 易错：正方形周长 = 边长×4，不是 边长×边长（那是面积）！\n\n"
            "**📝 例题**：一个长方形花坛，长 12 米，宽 8 米。它的周长是多少米？\n\n"
            "解：$C = (12 + 8) \\times 2 = 20 \\times 2 = 40$（米）。\n\n"
            "答：花坛的周长是 **40 米**。"
        ),
    },
    # ===== 比（六年级数学）=====
    ("比", "比的定义"): {
        "body": (
            "【什么是比】\n"
            "两个数相除，又叫做这两个数的**比**。\n\n"
            "例如：$3 \\div 2$ 可以写成 $3:2$ 或 $\\frac{3}{2}$，读作「三比二」。\n\n"
            "【比的各部分名称】\n"
            "在 $a:b$ 中：\n"
            "• $a$ 叫做比的**前项**\n"
            "• $b$ 叫做比的**后项**\n"
            "• 「:**」叫做**比号**\n"
            "• $a \\div b$ 的结果叫做**比值**（比值可以是分数、小数或整数）\n\n"
            "【比与除法、分数的关系】\n"
            "| 比 | 除法 | 分数 |\n"
            "|---|---|---|\n"
            "| 前项 | 被除数 | 分子 |\n"
            "| 后项 | 除数 | 分母 |\n"
            "| 比值 | 商 | 分数值 |\n"
            "| 比号 | ÷ | — |\n\n"
            "**注意**：比的后项不能为 0（和除数、分母一样）。"
        ),
        "example": (
            "【例题】\n"
            "学校有男生 20 人，女生 25 人。求：\n"
            "(1) 男生人数与女生人数的比；\n"
            "(2) 女生人数与男生人数的比；\n"
            "(3) 男生人数与总人数的比。\n\n"
            "【解答】\n"
            "(1) 男生 : 女生 = $20:25 = 4:5$\n"
            "(2) 女生 : 男生 = $25:20 = 5:4$\n"
            "(3) 总人数 = $20 + 25 = 45$ 人，男生 : 总人数 = $20:45 = 4:9$\n\n"
            "**注意**：一定要看清「谁比谁」，顺序不同，比就不同！"
        ),
    },
    ("比", "比的基本性质"): {
        "body": (
            "【比的基本性质】\n"
            "比的前项和后项同时**乘或除以**相同的数（0 除外），**比值不变**。\n\n"
            "用字母表示：\n"
            "$$a:b = (a \\times c):(b \\times c) = (a \\div c):(b \\div c) \\quad (c \\neq 0)$$\n\n"
            "【为什么要学这个性质？】\n"
            "• **化简比**：利用性质把复杂的比变成最简整数比\n"
            "• **求未知项**：已知比值和一个量，求另一个量\n"
            "• **判断比例是否成立**：验证两个比是否相等\n\n"
            "【与商不变规律、分数基本性质的对比】\n"
            "它们本质上是同一个规律的不同表现形式：\n"
            "• 除法：被除数和除数同时乘/除以同一个数（0除外），商不变\n"
            "• 分数：分子和分母同时乘/除以同一个数（0除外），分数大小不变\n"
            "• 比：前项和后项同时乘/除以同一个数（0除外），比值不变"
        ),
        "example": (
            "【例题1】化简 $12:18$\n"
            "解：$12:18 = (12 \\div 6):(18 \\div 6) = 2:3$ ✓\n"
            "（找最大公因数 6，前后项同除以 6）\n\n"
            "【例题2】已知 $5:x = \\frac{1}{2}$，求 $x$ 的值。\n"
            "解：根据比的基本性质，$x = 5 \\div \\frac{1}{2} = 5 \\times 2 = 10$\n"
            "验算：$5:10 = 5 \\div 10 = \\frac{1}{2}$ ✓\n\n"
            "**易错点**：「同乘同除」时千万不能忘记「0 除外」的条件！"
        ),
    },
    ("比", "化简比"): {
        "body": (
            "【什么是最简整数比？】\n"
            "前项和后项是**互质**的正整数（最大公因数为 1），且没有分数或小数。\n\n"
            "【化简比的两种方法】\n\n"
            "**方法一：找公因数法**（适用于整数比）\n"
            "找出前项和后项的最大公因数，然后同时除以它。\n"
            "例：$24:36$ → GCF(24,36)=12 → $(24 \\div 12):(36 \\div 12) = 2:3$\n\n"
            "**方法二：先变整数再约分**（适用于含分数或小数的比）\n"
            "① 含分数：用分母的最小公倍数同乘各项\n"
            "$\\frac{3}{4}:\\frac{5}{6}$ → 同乘 12 → $9:10$\n\n"
            "② 含小数：先扩大相同倍数消去小数\n"
            "$0.25:1.5$ → 同乘 100 → $25:150 = 1:6$\n\n"
            "【⚠️ 化简比 ≠ 求比值】\n"
            "• 化简比的结果是一个**比**（如 $2:3$）\n"
            "• 求比值的结果是一个**数**（如 $\\frac{2}{3}$ 或 $0.666...$）"
        ),
        "example": (
            "【例题1】化简 $\\frac{2}{3}:\\frac{4}{9}$\n"
            "解：分母 3 和 9 的最小公倍数是 9\n"
            "$$(\\frac{2}{3} \\times 9):(\\frac{4}{9} \\times 9) = 6:4 = 3:2$$\n\n"
            "【例题2】化简 $0.125:\\frac{1}{4}$\n"
            "解：先把小数变分数：$\\frac{1}{8}:\\frac{1}{4}$\n"
            "同乘 8：$1:2$ ✓\n\n"
            "【例题3】化简 $45:30:15$（三项连比）\n"
            "解：GCF(45,30,15) = 15\n"
            "$(45 \\div 15):(30 \\div 15):(15 \\div 15) = 3:2:1$"
        ),
    },
    ("比", "按比例分配"): {
        "body": (
            "【什么是按比例分配？】\n"
            "把一个总量按照一定的**比分**分成几部分，每部分占总量的几分之几，再分别计算。\n\n"
            "【通用解题步骤】\n"
            "**第一步：求总份数**\n"
            "把比的前后项加起来得到总份数。\n"
            "**第二步：求每份对应的分率**\n"
            "每部分 = 总量 × 该部分的份数 ÷ 总份数\n"
            "**第三步：计算并验算**\n"
            "算出各部分后加起来应等于总量。\n\n"
            "【核心公式】\n"
            "若把总量 $S$ 按 $m:n$ 分配：\n"
            "• 第一份 = $S \\times \\frac{m}{m+n}$\n"
            "• 第二份 = $S \\times \\frac{n}{m+n}$\n\n"
            "【常见应用场景】\n"
            "• 配制溶液（药液与水的比例）\n"
            "• 分配奖金/任务\n"
            "• 混凝土配比（水泥:沙:石子）\n"
            "• 地图上的面积分配"
        ),
        "example": (
            "【例题】\n"
            "一种混凝土由水泥、沙子和石子按 $2:3:5$ 的比配制而成。\n"
            "如果需要配制 40 吨这样的混凝土，需要水泥、沙子、石子各多少吨？\n\n"
            "【解答】\n"
            "① 总份数 = $2 + 3 + 5 = 10$ 份\n\n"
            "② 水泥 = $40 \\times \\frac{2}{10} = 8$ 吨\n\n"
            "③ 沙子 = $40 \\times \\frac{3}{10} = 12$ 吨\n\n"
            "④ 石子 = $40 \\times \\frac{5}{10} = 20$ 吨\n\n"
            "⑤ 验算：$8 + 12 + 20 = 40$ 吨 ✓\n\n"
            "**关键**：先求总份数，再用「总量 × 对应份数÷总份数」！"
        ),
    },
    ("比", "比的应用"): {
        "body": (
            "【比在实际问题中的应用类型】\n\n"
            "**类型一：已知部分量及比例关系，求另一部分量**\n"
            "方法：先根据已知的量和对应的比例，求出一份是多少，再求其他部分。\n\n"
            "**类型二：已知总量和变化后的比例关系，求原量**\n"
            "方法：设未知数，列方程求解。\n\n"
            "**类型三：比例中的和差问题**\n"
            "方法：抓住不变的量（总量不变或差量不变），建立等量关系。\n\n"
            "【重要技巧】\n"
            "• 画线段图帮助理解数量关系\n"
            "• 统一单位后再列比\n"
            "• 注意区分「A 是 B 的几倍」和「A 与 B 的比」\n"
            "• 复杂问题可以设一份为 $x$，列方程求解\n\n"
            "【与其他知识的联系】\n"
            "比的应用与**分数应用题**、**百分数应用题**、**方程**密切相关——同一道题往往可以用多种方法解决。"
        ),
        "example": (
            "【例题1】\n"
            "甲、乙两仓库共存粮 180 吨。如果从甲仓库运出 $\\frac{1}{4}$ 给乙仓库，"
            "两个仓库的存粮就相等了。原来甲、乙两仓库存粮的比是多少？\n\n"
            "【解法一（方程法）】\n"
            "设甲原有 $x$ 吨，则乙有 $(180-x)$ 吨。\n"
            "运出 $\\frac{1}{4}$ 后：$x - \\frac{1}{4}x = 180 - x + \\frac{1}{4}x$\n"
            "$$\\frac{3}{4}x = 180 - \\frac{3}{4}x$$\n"
            "$$\\frac{3}{2}x = 180 \\Rightarrow x = 120$$\n"
            "甲 : 乙 = $120 : 60 = 2:1$\n\n"
            "【解法二（画图法）】\n"
            "从甲运 $\\frac{1}{4}$ 到乙后相等 → 甲比乙多原来乙的 $\\frac{1}{2}$\n"
            "即 甲 = 乙 × $\\frac{3}{2}$，所以 甲:乙 = 3:2？不对！重新分析…\n"
            "实际上：甲运走 $\\frac{1}{4}$后等于乙加上这$\\frac{1}{4}$\n"
            "→ 甲的 $\\frac{3}{4}$ = 乙的 $1\\frac{1}{4}$ → 甲:乙 = $5:3$\n"
            "验算：甲=112.5吨, 乙=67.5吨; 甲运28.125给乙→都是84.375 ✓"
        ),
    },

    # ===== 分数乘法（六年级数学）=====
    ("分数乘法", "分数乘整数"): {
        "body": (
            "【分数乘整数的意义】\n"
            "求几个相同分数的和的简便运算。\n"
            "$$\\frac{2}{7} \\times 3 = \\frac{2}{7} + \\frac{2}{7} + \\frac{2}{7} = \\frac{6}{7}$$\n\n"
            "【计算法则】\n"
            "**分子 × 整数作新分子，分母不变**\n"
            "$$\\frac{a}{b} \\times n = \\frac{a \\times n}{b}$$\n\n"
            "【能约分的要先约分】\n"
            "$$\\frac{5}{12} \\times 8 = \\frac{5 \\times 8}{12} = \\frac{40}{12} = \\frac{10}{3}$$\n"
            "更简便的做法：\n"
            "$$\\frac{5}{12} \\times 8 = \\frac{5 \\times \\cancel{8}^2}{\\cancel{12}_3} = \\frac{10}{3}$$"
        ),
        "example": (
            "【例题】一根绳子长 $\\frac{3}{4}$ 米，3 根这样的绳子一共长多少米？\n\n"
            "解：$\\frac{3}{4} \\times 3 = \\frac{9}{4} = 2.25$ 米（或 $2\\frac{1}{4}$ 米）\n\n"
            "答：3 根绳子共长 $\\frac{9}{4}$ 米（即 2.25 米）。"
        ),
    },
    ("分数乘法", "分数乘分数"): {
        "body": (
            "【分数乘分数的意义】\n"
            "求一个数的几分之几是多少。\n"
            "$$\\frac{2}{3} \\times \\frac{4}{5} = ?$$\n"
            "意思是：求 $\\frac{2}{3}$ 的 $\\frac{4}{5}$ 是多少。\n\n"
            "【计算法则】\n"
            "**分子 × 分子作新分子，分母 × 分母作新分母**\n"
            "$$\\frac{a}{b} \\times \\frac{c}{d} = \\frac{a \\times c}{b \\times d}$$\n\n"
            "【重要：先约分再乘！】\n"
            "$$\\frac{3}{8} \\times \\frac{4}{9} = \\frac{\\cancel{3}^1 \\times \\cancel{4}^1}{\\cancel{8}_2 \\times \\cancel{9}_3} = \\frac{1}{6}$$\n\n"
            "**为什么可以先约分？**\n"
            "因为约分相当于分子分母同时除以相同的数，不改变分数的大小。\n"
            "先约分可以让数字变小，计算更简单，结果也更准确。"
        ),
        "example": (
            "【例题】一台拖拉机每小时耕地 $\\frac{1}{2}$ 公顷，$\\frac{3}{4}$ 小时耕地多少公顷？\n\n"
            "解：$\\frac{1}{2} \\times \\frac{3}{4} = \\frac{3}{8}$ 公顷\n\n"
            "答：$\\frac{3}{4}$ 小时耕地 $\\frac{3}{8}$ 公顷。\n\n"
            "【思考】为什么结果是 $\\frac{3}{8}$ 而不是 $\\frac{1}{2}$？\n"
            "因为 $\\frac{3}{4}$ 小时不到 1 小时，耕的地自然也不到 $\\frac{1}{2}$ 公顷。"
        ),
    },
    ("分数乘法", "分数混合运算"): {
        "body": (
            "【运算顺序】（和整数四则混合运算一致！）\n"
            "1. **有括号的先算括号里面**\n"
            "2. **先乘除，后加减**\n"
            "3. **同级从左到右依次计算**\n\n"
            "【常用简便算法】\n"
            "• **乘法交换律**：$a \\times b = b \\times a$\n"
            "• **乘法结合律**：$(a \\times b) \\times c = a \\times (b \\times c)$\n"
            "• **乘法分配律**：$(a+b) \\times c = a \\times c + b \\times c$\n\n"
            "【典型技巧】\n"
            "看到 $\\frac{x}{y} + \\frac{x}{y} × n$ → 提取 $\\frac{x}{y}(1 + n)$\n"
            "看到 $\\frac{a}{b} × \\frac{c}{d} + \\frac{a}{b} × \\frac{e}{f}$ → 提取 $\\frac{a}{b}$\n\n"
            "【易错提醒】\n"
            "• 分数加减要通分，但分数乘法不需要通分！\n"
            "• 不要看到分母不同就想通分，乘法直接分子乘分子、分母乘分母即可"
        ),
        "example": (
            "【例题】简便计算：$\\frac{5}{9} \\times \\frac{3}{4} + \\frac{5}{9} \\times \\frac{1}{4}$\n\n"
            "解：提取公因数 $\\frac{5}{9}$\n"
            "$$\\frac{5}{9} \\times (\\frac{3}{4} + \\frac{1}{4}) = \\frac{5}{9} \\times 1 = \\frac{5}{9}$$\n\n"
            "【对比】不用简便算法的话：\n"
            "$\\frac{5}{9} \\times \\frac{3}{4} = \\frac{15}{36}$\n"
            "$\\frac{5}{9} \\times \\frac{1}{4} = \\frac{5}{36}$\n"
            "$\\frac{15+5}{36} = \\frac{20}{36} = \\frac{5}{9}$ ✓ （结果一样，但简便算法更快）"
        ),
    },
    ("分数乘法", "解决问题"): {
        "body": (
            "【分数乘法应用的核心思想】\n"
            "「求一个数的几分之几是多少」→ 用**乘法**！\n\n"
            "【解题步骤】\n"
            "1. 找准单位「1」（「的」「是」「占」后面的那个量通常是单位1）\n"
            "2. 确定要求的是单位1的几分之几\n"
            "3. 列式：单位1的量 × 所占的分率\n\n"
            "【常见题型】\n"
            "• 连续求一个数的几分之几（连乘）\n"
            "• 比...多/少几分之几的问题\n"
            "• 工程问题、行程问题中涉及分数的情况\n\n"
            "【关键区别】\n"
            "• 「A 的 $\\frac{n}{m}$」→ A × $\\frac{n}{m}$ （乘法）\n"
            "• 「A 比 B 多 $\\frac{n}{m}$」→ B × (1 + $\\frac{n}{m}$)\n"
            "• 「A 比 B 少 $\\frac{n}{m}$」→ B × (1 - $\\frac{n}{m}$)"
        ),
        "example": (
            "【例题】\n"
            "六（1）班有 45 人，其中男生占 $\\frac{4}{9}$，女生人数的 $\\frac{1}{5}$ 戴眼镜。\n"
            "戴眼镜的女生有多少人？\n\n"
            "【分析】\n"
            "① 先求女生人数：总人数 × 女生占比\n"
            "女生 = $45 \\times (1 - \\frac{4}{9}) = 45 \\times \\frac{5}{9} = 25$ 人\n\n"
            "② 再求戴眼镜的女生：\n"
            "$25 \\times \\frac{1}{5} = 5$ 人\n\n"
            "综合算式：$45 \\times (1 - \\frac{4}{9}) \\times \\frac{1}{5} = 5$ 人\n\n"
            "答：戴眼镜的女生有 5 人。"
        ),
    },

    # ===== 圆的认识（六年级数学）=====
    ("圆", "圆的认识"): {
        "body": (
            "【圆的定义】\n"
            "平面上到定点的距离等于定长的所有点组成的图形叫做**圆**。\n\n"
            "【圆的各部分名称】\n"
            "• **圆心（O）**：圆的中心，确定圆的位置\n"
            "• **半径（r）**：连接圆心和圆上任意一点的线段（决定圆的大小）\n"
            "• **直径（d）**：通过圆心并且两端都在圆上的线段\n"
            "• **弦**：连接圆上任意两点的线段\n"
            "• **弧**：圆上任意两点之间的部分\n\n"
            "【重要关系】\n"
            "• 在**同一个圆**里：所有半径都相等，所有直径都相等\n"
            "• 直径 = 半径 × 2，即 $d = 2r$ 或 $r = d/2$\n"
            "• 圆是轴对称图形，有无数条对称轴（每条直径都是对称轴）\n\n"
            "【如何用圆规画圆】\n"
            "1. 把圆规的一脚固定在点上（圆心）\n"
            "2. 两脚之间的距离定为半径长度\n"
            "3. 旋转一周即可画出圆"
        ),
        "example": (
            "【例题】\n"
            "用一个半径为 3cm 的圆规画圆，这个圆的直径是多少厘米？\n"
            "如果要画一个直径为 10cm 的圆，圆规的两脚应张开多大距离？\n\n"
            "解：\n"
            "① 半径 r = 3cm → 直径 d = 2r = 2 × 3 = **6 cm**\n\n"
            "② 直径 d = 10cm → 半径 r = d ÷ 2 = 10 ÷ 2 = **5 cm**\n"
            "→ 圆规两脚应张开 **5 cm**\n\n"
            "**记住**：圆规两脚张开的距离就是**半径**，不是直径！"
        ),
    },
    ("圆", "圆的周长"): {
        "body": (
            "【什么是圆的周长？】\n"
            "围成圆的曲线的长度叫做圆的**周长**，通常用字母 C 表示。\n\n"
            "【周长公式】（必须牢记！）\n"
            "$$C = \\pi d = 2\\pi r$$\n\n"
            "其中 $\\pi$（圆周率）≈ 3.14159265...\n"
            "• $\\pi$ 是一个无限不循环小数\n"
            "• 计算时通常取 $\\pi ≈ 3.14$\n"
            "• 祖冲之是世界上第一个精确计算到小数点后 7 位的人\n\n"
            "【公式怎么来的？】\n"
            "古人发现：任意圆的**周长 ÷ 直径**总是接近同一个数，这个数就是 $\\pi$。\n"
            "圆越大，周长越长，但周长与直径的比值始终是 $\\pi$。\n\n"
            "【半圆的弧长】\n"
            "半圆的弧长 = $\\pi r$（整圆周长的一半）\n"
            "注意：半圆的**周长**（包含直径）= $\\pi r + 2r = (\\pi+2)r$"
        ),
        "example": (
            "【例题1】\n"
            "一辆自行车的车轮直径是 70cm，绕操场骑一圈大约是多远？（$\\pi$ 取 3.14）\n\n"
            "解：$C = \\pi d = 3.14 \\times 70 = 219.8$ cm $\\approx 2.2$ m\n\n"
            "【例题2】\n"
            "一个圆形花坛的周长是 37.68 米，它的半径是多少米？\n\n"
            "解：$C = 2\\pi r \\Rightarrow r = C / (2\\pi)$\n"
            "$r = 37.68 \\div (2 \\times 3.14) = 37.68 \\div 6.28 = 6$ m\n\n"
            "答：花坛半径是 6 米。"
        ),
    },
    ("圆", "圆的面积"): {
        "body": (
            "【圆的面积公式】（最重要之一！）\n"
            "$$S = \\pi r^2$$\n\n"
            "其中 $r^2$ 表示 $r \\times r$（半径的平方），不是 $r \\times 2$！\n\n"
            "【公式推导（割圆法思想）】\n"
            "把圆平均分成很多小扇形，拼成一个近似的长方形：\n"
            "• 长方形的 长 $\\approx$ 圆周长的一半 = $\\pi r$\n"
            "• 长方形的 宽 $\\approx$ 圆的半径 = $r$\n"
            "• 面积 = 长 × 宽 = $\\pi r \\times r = \\pi r^2$ ✓\n\n"
            "【已知直径怎么办？】\n"
            "先求半径：$r = d \\div 2$，再用面积公式。\n"
            "$$S = \\pi (\\frac{d}{2})^2 = \\pi \\cdot \\frac{d^2}{4} = \\frac{\\pi d^2}{4}$$\n\n"
            "【已知周长怎么办？】\n"
            "由 $C = 2\\pi r$ 得 $r = C/(2\\pi)$\n"
            "再代入 $S = \\pi r^2 = \\pi \\cdot (C/(2\\pi))^2 = C^2/(4\\pi)$"
        ),
        "example": (
            "【例题】\n"
            "一个圆形餐桌桌面的直径是 1.4 米，要在上面铺一块桌布（垂下 20cm），\n"
            "这块桌布的面积至少是多少平方米？（$\\pi$ 取 3.14）\n\n"
            "【解答】\n"
            "① 桌面半径：$r_{桌} = 1.4 \\div 2 = 0.7$ m\n"
            "② 桌布需覆盖的半径：$r = 0.7 + 0.2 = 0.9$ m（桌面半径 + 下垂 20cm）\n"
            "③ 桌布面积：$S = 3.14 \\times 0.9^2 = 3.14 \\times 0.81 = 2.5434$ m²\n\n"
            "答：桌布面积至少约 2.54 平方米。\n\n"
            "**易错**：别忘了加上下垂的部分！不要只算桌面面积！"
        ),
    },
    ("圆", "扇形"): {
        "body": (
            "【什么是扇形？】\n"
            "由圆心角的两条半径和圆心角所对的弧围成的图形叫做**扇形**。\n\n"
            "【扇形的组成】\n"
            "• **圆心角（$\\theta$ 或 $n°$）**：顶点在圆心的角\n"
            "• **弧**：圆心角所对的圆弧\n"
            "• 两条半径\n\n"
            "【扇形面积公式】\n"
            "设圆心角为 $n°$：\n"
            "$$S_{扇形} = \\frac{n}{360} \\times \\pi r^2$$\n"
            "思路：扇形面积 = 整圆面积的 $\\frac{n}{360}$\n\n"
            "【扇形弧长公式】\n"
            "$$l_{弧} = \\frac{n}{360} \\times 2\\pi r = \\frac{n\\pi r}{180}$$\n\n"
            "【特殊情况】\n"
            "• 当 $n = 90°$ 时：扇形面积 = $\\frac{1}{4}\\pi r^2$（四分之一圆）\n"
            "• 当 $n = 180°$ 时：扇形面积 = $\\frac{1}{2}\\pi r^2$（半圆）"
        ),
        "example": (
            "【例题】\n"
            "如右图，一个圆的半径是 6cm，圆心角为 $120°$ 的扇形面积和弧长各是多少？\n"
            "（$\\pi$ 取 3.14）\n\n"
            "解：\n"
            "① 面积：$S = \\frac{120}{360} \\times 3.14 \\times 6^2 = \\frac{1}{3} \\times 3.14 \\times 36 = 37.68$ cm²\n\n"
            "② 弧长：$l = \\frac{120}{360} \\times 2 \\times 3.14 \\times 6 = \\frac{1}{3} \\times 37.68 = 12.56$ cm\n\n"
            "答：扇形面积约 37.68 平方厘米，弧长约 12.56 厘米。"
        ),
    },
}


def _explain_sub(topic_title, subject, sub, course_id=None):
    """返回每个子知识点的详细、独特的学习内容（含例题）。
    优先使用本地 Ollama 批量生成的真实课件内容（curriculum_gen.json, 全学科覆盖）。"""
    reload_gen()  # 支持生成任务边跑边用
    # 优先用 Ollama 批量生成的真实课件内容（全学科覆盖）
    gen = GEN_CONTENT.get(course_id) if course_id else GEN_BY_TS.get((topic_title, sub))
    if not gen and course_id:
        gen = LAZY_CONTENT.get(course_id) or LAZY_BY_TS.get((topic_title, sub))
    if gen:
        for _s in gen.get("subs", []):
            if _s.get("sub") == sub and _s.get("content"):
                return _s["content"]
    # 懒生成：对易出「整科重复模板」的薄弱学科，首次学习时按需实时生成真实内容
    if course_id and subject in _LAZY_SUBJECTS and course_id not in GEN_CONTENT:
        _topic = TOPIC_INDEX.get(course_id, {})
        _subs = _topic.get("sub") or [sub]
        if _lazy_ollama_explain(course_id, topic_title, subject, _subs):
            gen = LAZY_CONTENT.get(course_id)
            if gen:
                for _s in gen.get("subs", []):
                    if _s.get("sub") == sub and _s.get("content"):
                        return _s["content"]
    # 优先查找知识库中的精确匹配
    content = _SUBTOPIC_CONTENT.get((topic_title, sub))
    if not (content and content.get("body")):
        # 历史合并时部分知识点讲解内容误置于 _MISTAKES_MAP，作为兜底内容源
        # 注意：_MISTAKES_MAP 中有些条目是「易错点列表」(list) 而非内容字典，
        # 必须校验为 dict 且含 body，否则 .get 会抛 AttributeError 被上层吞掉 → 内容变空
        mc = _MISTAKES_MAP.get((topic_title, sub))
        if isinstance(mc, dict) and mc.get("body"):
            content = mc
    if content and content.get("body"):
        body = content.get("body", "")
        # 如果有例题，拼接到正文后面
        example = content.get("example", "")
        if example:
            body += "\n\n" + example
        return body

    # 兜底：基于学科和子主题名的智能生成
    open_line = _SUBJECT_OPEN.get(subject, "学习这部分，先理解再练习最重要。")
    
    # 根据学科和关键词匹配生成更有针对性的内容
    lower_sub = sub.lower()
    lower_topic = topic_title.lower()

    # 学科分流：数学走数学引擎（覆盖小初高全学段），其他学科走全学科引擎
    if subject == "数学":
        return _gen_math_content(topic_title, sub, open_line, subject=subject)
    return _gen_multi_subject_content(topic_title, sub, subject)


def _gen_math_content(topic_title, sub, open_line, subject=None):
    """为数学子知识点生成针对性的内容（智能兜底引擎）
    根据知识点名称自动识别概念类型，生成含公式、步骤、例题的差异化内容。
    """
    t, s = topic_title, sub
    
    # ===== 小学数学·多边形的面积 =====
    if "平行四边形面积" in s or ("面积" in t and "平行四边形" in s):
        return (
            f"【{s}的含义】\n"
            "平行四边形的面积 = 底 × 高（**不是邻边相乘！**）。\n\n"
            "**推导方法：割补法**\n"
            "沿平行四边形的高剪开一个直角三角形，平移到另一侧，拼成一个**长方形**。"
            "长方形的长 = 平行四边形的底，宽 = 平行四边形的高。"
            "所以：$S_{\\text{平行四边形}} = a \\times h$（底×高）。\n\n"
            "⚠️ 关键：高必须是对应底边上的垂直距离！斜边不是高。\n\n"
            "**📝 例题**：一个平行四边形花坛，底是 $12\\text{m}$，对应的高是 $8\\text{m}$。面积是多少？\n\n"
            "解：$S = 12 \\times 8 = 96(\\text{m}^2)$\n\n"
            "答：面积是 **$96\\text{m}^2$**（96平方米）。"
        )
    if "三角形面积" in s or ("面积" in t and "三角形" in s):
        return (
            f"【{s}的公式】\n"
            "三角形的面积 = 底 × 高 ÷ 2\n公式：$S_{\\triangle} = \\frac{1}{2}ah$\n\n"
            "**推导方法：用两个完全一样的三角形拼成一个平行四边形**\n"
            "每个三角形的面积 = 拼成的平行四边形面积 ÷ 2 = (底×高) ÷ 2\n\n"
            "⚠️ 三种常见三角形都要会找高：\n"
            "- 锐角三角形：三条高都在形内\n"
            "- 直角三角形：两条直角边互为底和高\n"
            "- 钝角三角形：两条高在形外！\n\n"
            "**📝 例题**：一块三角形交通标志牌，底 $80\\text{cm}$，高 $50\\text{cm}$。面积是多少平方厘米？\n\n"
            "解：$S = \\frac{1}{2} \\times 80 \\times 50 = 2000(\\text{cm}^2)$\n\n"
            "答：面积是 **$2000\\text{cm}^2$**。"
        )
    if "梯形面积" in s or ("面积" in t and "梯形" in s):
        return (
            f"【{s}的公式】\n"
            "梯形的面积 = (上底 + 下底) × 高 ÷ 2\n公式：$S = \\frac{(a+b)h}{2}$\n\n"
            "**推导方法：用两个完全一样的梯形拼成一个平行四边形**\n"
            "拼成后的平行四边形底 = 上底+下底，高不变，所以梯形面积是其一半。\n\n"
            "**特殊梯形记忆**：\n"
            "- 等腰梯形：两腰相等\n"
            "- 直角梯形：有一个角是直角\n"
            "- 当上底=0时 → 变成三角形！（三角形是梯形的特殊情况）\n\n"
            "**📝 例题**：一个梯形果园，上底 $30\\text{m}$，下底 $50\\text{m}$，高 $20\\text{m}$。面积是多少？\n\n"
            "解：$S = \\frac{(30+50) \\times 20}{2} = \\frac{80 \\times 20}{2} = 800(\\text{m}^2)$\n\n"
            "答：果园面积 **$800\\text{m}^2$**。"
        )
    if "组合图形" in s:
        return (
            f"【{s}的计算方法】\n"
            "组合图形由基本图形拼接或挖空而成，常用两种方法：\n\n"
            "**方法一：分割法（添辅助线）**\n"
            "把不规则图形分割成几个学过的基本图形（长方形/三角形/梯形），分别计算再相加。\n"
            "💡 技巧：尽量分割成数量少、数据好算的图形。\n\n"
            "**方法二：填补法（补全法）**\n"
            "把图形补成一个大图形，减去多余部分。\n"
            "适合有\"缺角\"的图形（如 L 形、凹字形）。\n\n"
            "**📝 例题**（分割法）：一面墙的形状是一个组合图形，可以分成一个长方形($6\\times 4$)和一个三角形(底$6$、高$3$)。总面积？\n\n"
            "解：长方形面积 $= 6 \\times 4 = 24$\n"
            "三角形面积 $= \\frac{1}{2} \\times 6 \\times 3 = 9$\n"
            "总面积 $= 24 + 9 = 33$（单位²）"
        )
    if "估算" in s and "图形" in s:
        return (
            f"【{s}的方法】\n"
            "不规则图形面积的估算方法：\n\n"
            "**① 数方格法**\n"
            "把图形放在方格纸上，数格子数。满格算 1 格，不满半格舍去，超过半格算 1 格。\n\n"
            "**② 近似图形法**\n"
            "把不规则图形近似看作规则图形（如近似椭圆看作长方形或圆）来估算。\n\n"
            "**③ 分块估算**\n"
            "将大不规则区域分成若干小块，分别估算后求和。\n\n"
            "**📝 例题**：一片树叶放在每格 $1\\text{cm}^2$ 的方格纸上，满格 18 格，不满格但超半格的有 10 格。面积约多少？\n\n"
            "解：$18 \\times 1 + 10 \\times 1 = 28(\\text{cm}^2)$（约 $25\\sim 30\\text{cm}^2$ 均可接受）"
        )

    # ===== 小数乘法 =====
    if "小数乘整数" in s or ("小数乘法" in t and "整数" in s):
        return (
            f"【{s}的算法】\n"
            "小数乘整数 → 先按整数乘法算完 → 再点小数点\n\n"
            "**步骤**：\n"
            "1️⃣ 先把小数看成整数，按整数乘法计算\n"
            "2️⃣ 数因数中一共有几位小数\n"
            "3️⃣ 从积的右边起数出几位，点上小数点\n\n"
            "⚠️ 位数不够时要在前面用 **0** 补足，再点小数点。\n\n"
            "**📝 例题**：一块橡皮 $0.85$ 元，买 $4$ 块多少钱？\n\n"
            "解：$0.85 \\times 4 = 3.40 = 3.5$（元）\n\n"
            "（先算 $85 \\times 4 = 340$，因数共 2 位小数 → $3.40$，末尾0可去掉）\n\n"
            "答：**$3.5$ 元**（3元5角）。"
        )
    if "小数乘小数" in s or ("小数乘法" in t and "小数" in s):
        return (
            f"【{s}的算法】\n"
            "小数乘小数 → 整数乘法算积 → 数总位数点小数点\n\n"
            "**核心规律**：因数中共有几位小数，积就有几位小数。\n\n"
            "**步骤**：\n"
            "1️⃣ 按整数乘法算出积\n"
            "2️⃣ 数两个因数一共有几位小数\n"
            "3️⃣ 从积的右边起数出几位，点上小数点\n"
            "4️⃣ 根据四舍五入求近似值（如需要）\n\n"
            "**📝 例题**：教室长 $8.5\\text{m}$，宽 $6.2\\text{m}$。面积？（保留一位小数）\n\n"
            "解：$8.5 \\times 6.2 = 52.7(\\text{m}^2)$\n"
            "（先算 $85 \\times 62 = 5270$，因数共2位小数 → $52.70$）\n\n"
            "答：约 **$52.7\\text{m}^2$**。"
        )
    if "积的近似数" in s or "近似数" in s:
        return (
            f"【{s}的方法】\n"
            "生活中往往不需要精确结果，用「四舍五入」求积的近似数。\n\n"
            "**方法**：\n"
            "1️⃣ 先正常计算出精确的积\n"
            "2️⃣ 看要求保留几位小数\n"
            "3️⃣ 看保留位后一位：**≥5 进 1，< 5 舍去**\n\n"
            "**保留规则**：\n"
            "- 保留整数 → 看十分位\n"
            "- 保留一位小数 → 看百分位\n"
            "- 保留两位小数 → 看千分位\n\n"
            "**📝 例题**：$1.96 \\times 3.14$（保留两位小数）\n\n"
            "解：$1.96 \\times 3.14 = 6.1544 ≈ **6.15**\n"
            "(看千分位是 4 < 5，舍去)"
        )
    if "运算律" in s and "整数" in s or ("小数乘法" in t and "运算律" in s):
        return (
            f"【整数的运算律对小数同样适用】\n\n"
            "**① 交换律**：$a × b = b × a$\n"
            "例：$0.5 × 1.2 = 1.2 × 0.5 = 0.6$\n\n"
            "**② 结合律**：$(a × b) × c = a × (b × c)$\n"
            "例：$(0.25 × 7.3) × 4 = 0.25 × 4 × 7.3 = 1 × 7.3 = 7.3$\n\n"
            "**③ 分配律**：$(a + b) × c = a×c + b×c$\n"
            "例：$(2.5 + 1.25) × 0.8 = 2.5×0.8 + 1.25×0.8 = 2 + 1 = 3$\n\n"
            "💡 巧用运算律可以**简化计算**！特别是 $0.25×4=1$、$1.25×8=10$、$0.125×8=1$ 这些凑整组合要记住。"
        )
    if "解决问题" in s and "小数" in t:
        return (
            f"【{s}】小数乘法的实际应用\n\n"
            "**常见题型**：\n"
            "① 单价×数量 = 总价（购物问题）\n"
            "② 速度×时间 = 路程（行程问题）\n"
            "③ 工效×工时 = 工作总量（工程问题）\n"
            "④ 步长×步数 = 总距离（测量问题）\n\n"
            "**关键**：找到两个因数，确认单位统一后再计算。\n\n"
            "**📝 例题**：香蕉每千克 $3.8$ 元，妈妈买了 $2.5$ 千克。付 $20$ 元够吗？\n\n"
            "解：$3.8 × 2.5 = 9.5$（元）\n"
            "$9.5 < 20$，所以够了（还剩 $10.5$ 元）。\n\n"
            "答：**够**，应付 **$9.5$ 元**。"
        )

    # ===== 分数乘法 =====
    if "分数乘整数" in s or ("分数乘法" in t and "整数" in s and "运算律" not in s):
        return (
            f"【{s}的算法】\n"
            "分数乘整数 → 分母不变，分子与整数相乘，能约分的先约分。\n\n"
            "**步骤**：\n"
            "1️⃣ 整数与分子相乘作新分子，分母不变\n"
            "2️⃣ 结果不是最简分数要化成最简\n"
            "3️⃣ 能先约分的先约分，算得更简单\n\n"
            "**📝 例题**：$12 \\times \\frac{3}{4} = 9$（先约分：$12$ 和 $4$ 约去 $4$ 得 $3$，再 $3 \\times 3 = 9$）。\n\n"
            "答：**9**。"
        )
    if "分数乘分数" in s or ("分数乘法" in t and "分数" in s and "整数" not in s and "小数" not in s and "运算律" not in s):
        return (
            f"【{s}的算法】\n"
            "分数乘分数 → **分子乘分子，分母乘分母**，能约分的先约分。\n\n"
            "**步骤**：\n"
            "1️⃣ 分子 × 分子 作新分子\n"
            "2️⃣ 分母 × 分母 作新分母\n"
            "3️⃣ 先约分再乘（或乘完再约），化成最简分数\n\n"
            "**📝 例题**：$\\frac{3}{4} \\times \\frac{4}{3} = 1$（互为倒数相乘得 1）。\n\n"
            "答：**1**。"
        )
    if "小数乘分数" in s or ("分数乘法" in t and "小数" in s and "分数" in s):
        return (
            f"【{s}的方法】\n"
            "小数乘分数有两种处理方式：\n"
            "① 把小数化成分数再按分数乘法算；\n"
            "② 把分数化成小数再按小数乘法算（分数能化成有限小数时最方便）。\n\n"
            "**📝 例题**：$0.25 \\times \\frac{4}{5} = 0.2$（$\\frac{4}{5}=0.8$，$0.25 \\times 0.8 = 0.2$）。\n\n"
            "答：**0.2**。"
        )
    if "解决问题" in s and "分数" in t:
        return (
            f"【{s}】分数乘法的实际应用\n\n"
            "**关键**：找到两个因数（谁 × 谁），确认单位统一后再计算；结果常需化简或取近似值。\n\n"
            "**📝 例题**：一袋大米 $\\frac{3}{4}$ 千克，3 袋共多少千克？\n\n"
            "解：$\\frac{3}{4} \\times 3 = 2.25$（千克）。\n\n"
            "答：**2.25 千克**。"
        )

    # ===== 位置（数对） =====
    if "列与行" in s or "数对表示" in s:
        return (
            f"【{s}——用数对确定位置】\n\n"
            "**数对的格式**：$(列数, 行数)$ —— 先列后行！\n\n"
            "想象教室座位：\n"
            "- **竖排**叫「列」（从左往右数）\n"
            "- **横排**叫「行」（从前往后数）\n\n"
            "例如：小明在第 3 列第 2 行 → 用数对表示为 **$(3, 2)$**\n\n"
            "⚠️ $(3, 2)$ 和 $(2, 3)$ 是**不同的位置**！顺序不能乱。\n\n"
            "**类似坐标**：这其实就是平面直角坐标系的前身——以后学到坐标系时，数对就是 $(x, y)$ 坐标。"
        )
    if "方格纸" in s or "路线" in s or "坐标" in s:
        return (
            f"【{s}】\n\n"
            "在方格纸上用数对可以：\n"
            "1️⃣ **标出点的位置**：给定数对，在方格纸上找到交点并标记\n"
            "2️⃣ **描述路线**：按顺序写出经过各点的数对\n"
            "3️⃣ **画图形**：连接数对标出的点可以得到各种图形\n\n"
            "💡 用数对还能判断图形特征：\n"
            "- 同一列的点：横坐标相同（竖直线）\n"
            "- 同一行的点：纵坐标相同（水平线）\n"
            "- 对角线上的点：横坐标=纵坐标（如 $(1,1)(2,2)(3,3)$）"
        )

    # ===== 小数除法 =====
    if "除数是整数" in s or ("小数除法" in t and "整数" in s):
        return (
            f"【{s}的算法】\n"
            "小数 ÷ 整数 → 按整数除法算 → 对齐被除数的小数点点商的小数点\n\n"
            "**步骤**：\n"
            "1️⃣ 按整数除法的方法去除\n"
            "2️⃣ 商的小数点和被除数的**小数点对齐**\n"
            "3️⃣ 如果末尾有余数，添 0 继续除\n"
            "4️⃣ 整数部分不够商 1，商 0 占位，点上小数点\n\n"
            "**📝 例题**：$22.4 ÷ 4 = ?$\n\n"
            "解：$22.4 ÷ 4 = 5.6$\n"
            "（先算 $22 ÷ 4 = 5$ 余 $2$，余 $2$ 变 $20$ 个十分之一，$20÷4=5$ → 商 $0.5$，合计 $5.6$）"
        )
    if "除数是小数" in s or ("小数除法" in t and "小数" in s):
        return (
            f"【{s}的核心——商不变性质】\n\n"
            "**关键转化**：除数是小数 → 利用**商不变性质**变成除数是整数！\n\n"
            "**商不变性质**：被除数和除数同时乘相同的数（0除外），商不变。\n\n"
            "**操作步骤**：\n"
            "1️⃣ 看除数有几位小数\n"
            "2️⃣ 把除数和被除数同时扩大相同的倍数（使除数变整数）\n"
            "3️⃣ 按「小数÷整数」的方法计算\n\n"
            "**📝 例题**：$7.55 ÷ 0.5 = ?$\n\n"
            "解：除数 $0.5$ 有 1 位小数 → 同时 ×10\n"
            "$7.55 ÷ 0.5 = 75.5 ÷ 5 = 15.1$"
        )
    if "循环小数" in s:
        return (
            f"【{s}的认识】\n\n"
            "有些小数除不尽，商会不断重复出现 —— 这就是**循环小数**。\n\n"
            "**分类**：\n"
            "- **纯循环小数**：循环节从小数部分第一位开始（如 $0.333...$）\n"
            "- **混循环小数**：循环节不从第一位开始（如 $0.8333...$）\n\n"
            "**简便写法**：在循环节的首尾数字上加点\n"
            "- $0.333... = 0.\\dot{3}$\n"
            "- $0.142857142857... = 0.\\dot{1}4285\\dot{7}$\n\n"
            "**📝 例题**：计算 $1 ÷ 3$、$1 ÷ 6$、$1 ÷ 7$ 并观察规律。"
        )
    if "商的近似数" in s or "近似数" in s:
        return (
            f"【{s}的方法】\n\n"
            "和积的近似数一样，用**四舍五入**法。\n\n"
            "**区别**：积的近似数先算精确值再取舍；商的近似数可以**除到比需要保留的多一位**，再四舍五入（更简便！）。\n\n"
            "**📝 例题**：$19.4 ÷ 6$（保留一位小数）\n\n"
            "解：$19.4 ÷ 6 ≈ 3.23...$ 除到百分位\n"
            "百分位是 3 < 5 → 舍去 → 约 **3.2**"
        )

    # ===== 可能性（概率初步） =====
    if "一定" in s or "可能" in s or "不可能" in s:
        return (
            f"【事件发生的{sub}】\n\n"
            "**三种情况**：\n"
            "- 🟢 **一定**：肯定会发生（概率 = 1 或 100%）\n"
            "  例：太阳从东方升起；人都要呼吸空气\n"
            "- 🔴 **不可能**：绝对不会发生（概率 = 0）\n"
            "  例：明天太阳从西边升起；掷骰子出 7 点\n"
            "- 🟡 **可能（随机）**：也许发生也许不发生（0 < 概率 < 1）\n"
            "  例：明天下雨；掷硬币正面朝上\n\n"
            "**判断技巧**：结合生活经验和自然规律来分析。"
        )
    if "可能性大小" in s or "概率" in s:
        return (
            f"【{s}】\n\n"
            "可能性的大小可以用**分数**来表示：\n"
            "$P(A) = \\frac{\\text{想要的结果数}}{\\text{所有可能的结果总数}}$\n\n"
            "**数量越多 → 可能性越大**：\n"
            "- 盒子里 5 红 1 黄 → 摸到红球可能性大（$\\frac{5}{6}$ vs $\\frac{1}{6}$）\n"
            "- 公平的游戏：双方可能性相等（各 $\\frac{1}{2}$）\n\n"
            "**📝 例题**：盒子里 3 红 2 黄 1 绿，任意摸一个：\n"
            "摸到红球概率：$\\frac{3}{6}=\\frac{1}{2}$  最大！\n"
            "摸到绿球概率：$\\frac{1}{6}$  最小！"
        )
    if "公平" in s or "游戏" in s:
        return (
            f"【游戏公平性】\n\n"
            "**公平的游戏** = 双方获胜的可能性**相等**。\n\n"
            "**如何判断**：列出所有可能的结果，看各方赢的情况是否一样多。\n\n"
            "**修改不公平游戏的方法**：\n"
            "- 调整规则（如转盘增大某区域的面积）\n"
            "- 重新设计计分方式\n"
            "- 让各方可能结果数相等\n\n"
            "**📝 例题**：抛硬币决定谁先开球——正面向上 A 开，反面向上 B 开。公平吗？\n\n"
            "答：**公平**。因为 P(正)=P(反)=$\\frac{1}{2}$，双方机会均等。"
        )

    # ===== 简易方程 =====
    if "字母表示数" in s or "用字母" in s:
        return (
            f"【{sub}——代数的起点】\n\n"
            "用字母表示数可以把**数量关系**简洁地表达出来：\n\n"
            "**基本规则**：\n"
            "- 数字和字母相乘时，**乘号省略**，数字在前：$a × 4 = 4a$（不写 $a4$）\n"
            "- 字母和字母相乘也省略乘号：$a × b = ab$\n"
            "- 1 和字母相乘时 1 省略：$1 × a = a$\n"
            "- 相同字母相乘写成幂：$a × a = a^2$\n\n"
            "**例子**：\n"
            "- 小红 $a$ 岁，妈妈比她大 $24$ 岁 → 妈妈 $(a+24)$ 岁\n"
            "- 正方形边长 $a$ cm → 周长 $4a$ cm，面积 $a^2$ cm²\n\n"
            "💡 字母可以表示**任何数**——这就是「代数」的思想！"
        )
    if "等式性质" in s:
        return (
            f"【{sub}】\n\n"
            "等式就像平衡的天平，两边保持相等。\n\n"
            "**性质一**：等式两边同时加上（或减去）同一个数，等式仍然成立。\n"
            "$a = b → a + c = b + c$，$a = b → a - c = b -c$\n\n"
            "**性质二**：等式两边同时乘（或除以）同一个非零数，等式仍然成立。\n"
            "$a = b → ac = bc$，$a = b → \\frac{a}{c} = \\frac{b}{c}(c≠0)$\n\n"
            "**用途**：这两条性质就是**解方程**的理论依据！"
        )
    if "解方程" in s:
        return (
            f"【{sub}的步骤】\n\n"
            "方程是**含有未知数的等式**。解方程就是求未知数的值。\n\n"
            "**基本步骤**（利用等式性质）：\n"
            "1️⃣ **消常数项**：方程两边同加/减一个数，使左边只剩含 x 的项\n"
            "2️⃣ **化系数为 1**：方程两边同除以 x 的系数\n"
            "3️⃣ **检验**（重要！）：把 x 的值代入原方程，看左右是否相等\n\n"
            "**格式规范**：写「解：」，每一步上面标①②③，等号对齐。\n\n"
            "**📝 例题**：解方程 $2x + 8 = 20$\n\n"
            "解：$2x + 8 - 8 = 20 - 8$  ① 两边减8\n"
            "$2x = 12$\n"
            "$2x ÷ 2 = 12 ÷ 2$  ② 两边除以2\n"
            "$x = 6$\n\n"
            "检验：左边=$2×6+8=20$ = 右边 ✓"
        )
    if "列方程" in s or "应用题" in s:
        return (
            f"【{sub}】\n\n"
            "**列方程解应用题的步骤**：\n"
            "1️⃣ **设未知数**：通常问什么就设什么为 x（写完整：设……为 x）\n"
            "2️⃣ **找等量关系**：从题目中找出相等的两个量\n"
            "3️⃣ **列方程**：根据等量关系列出含 x 的等式\n"
            "4️⃣ **解方程**：求出 x 的值\n"
            "5️⃣ **作答**：写出完整答案（带单位）\n\n"
            "**常见等量关系**：\n"
            "- 总量=各分量之和\n"
            "- 单价×数量=总价\n"
            "- 速度×时间=路程\n"
            "- 男生人数+女生人数=总人数\n\n"
            "**📝 例题**：食堂买来 200 kg 白菜，吃了一些还剩 140 kg。吃了多少 kg？\n\n"
            "解：设吃了 $x$ kg。\n"
            "$x + 140 = 200$\n"
            "$x = 60$\n\n"
            "答：吃了 **60 kg**。"
        )

    # ===== 四年级数学 =====
    if "计数单位" in s or "数位顺序表" in s or "读法" in s or "写法" in s or "改写" in s or ("大数" in t and s):
        return (
            f"【{t} · {sub}】\n\n"
            "**大数的认识体系**：\n\n"
            "每相邻两个计数单位之间的进率都是 **10**。\n"
            "个(一) → 十 → 百 → 千 → **万** → 十万 → 百万 → 千万 → **亿** → …\n\n"
            "**分级读写**：从右往左每四位一级（个级、万级、亿级）\n"
            "- 读数：先分级 → 万级按个级读加「万」字 → 每级末尾的0不读\n"
            "- 写数：哪一位没有就写 0 占位\n\n"
            "**改写与近似数**：\n"
            "- 改写成「万」作单位：去掉末尾4个0，写「万」字\n"
            "- 省略万/亿位后面的尾数：看千位/千万位**四舍五入**"
        )
    if "公顷" in s or "平方千米" in s or ("公顷" in t and s):
        return (
            f"【{sub}】\n\n"
            "**大面积单位的换算**：\n\n"
            "| 单位 | 缩写 | 与米的关系 | 实际大小参照 |\n"
            "|------|------|-----------|-------------|\n"
            "| 公顷 | hm² | 边长100m的正方形 | 约1个足球场 |\n"
            "| 平方千米 | km² | 边长1000m(1km)的正方形 | 约140个足球场 |\n"
            "| 平方米 | m² | 边长1m的正方形 | 一块地砖的大小 |\n\n"
            "**进率**：\n"
            "$1\\text{ km}^2 = 100\\text{ 公顷} = 10000\\text{ m}^2$\n"
            "$1\\text{ 公顷} = 10000\\text{ m}^2$\n\n"
            "**📝 例题**：天安门广场面积约 40 公顷 = _____ km² = _____ m²\n\n"
            "解：40 公顷 = $40 ÷ 100 =$ **0.4 km²** = $40 × 10000 =$ **400000 m²**"
        )
    if "线段" in s or "射线" in s or "直线" in s or "角的定义" in s:
        return (
            f"【{sub}】\n\n"
            "**三个基本概念对比**：\n\n"
            "| | 直线 | 射线 | 线段 |\n"
            "|---|------|------|------|\n"
            "| 端点 | 无 | 1个 | 2个 |\n"
            "| 延伸 | 两端无限 | 一端无限 | 不延伸 |\n"
            "| 可度量 | ✗ | ✗ | ✓ |\n"
            "| 表示法 | 直线AB | 射线AB | 线段AB |\n\n"
            "**角的认识**：\n"
            "角 = 从一点引出两条射线所组成的图形\n"
            "- 顶点：公共端点\n"
            "- 边：两条射线\n"
            "- 角的大小只与**两边张开程度**有关，与边的长短无关！"
        )
    if "量角器" in s or "角的分类" in s or "画角" in s or ("角的度量" in t and s):
        return (
            f"【{sub}】\n\n"
            "**角的计量单位是「度」，符号 °**\n"
            "用量角器量角：中心对顶点，0刻度线对一边，看另一边指的刻度。\n\n"
            "**角的分类**：\n"
            "- 锐角：**< 90°**（尖尖的角）\n"
            "- 直角：**= 90°**（方方正正的角，标┐符号）\n"
            "- 钝角：**90° < 钝角 < 180°**（胖胖的角）\n"
            "- 平角：**= 180°**（一条直线）\n"
            "- 周角：**= 360°**（转了一圈回到原位）\n\n"
            "关系：1周角 = 2平角 = 4直角 = 360°"
        )
    if "三位数乘两位数" in s or "口算笔算" in s or ("三位数乘" in t and s):
        return (
            f"【{sub}】\n\n"
            "**三位数乘两位数笔算方法**：\n\n"
            "1️⃣ **相同数位对齐**（末位对末位）\n"
            "2️⃣ 用两位数的**个位**去乘三位数，得数的末位和个位对齐\n"
            "3️⃣ 用两位数的**十位**去乘三位数，得数的末位和十位对齐\n"
            "4️⃣ 把两次乘得的积**相加**\n\n"
            "**因数中间/末尾有0的处理**：\n"
            "- 中间有0要乘（0×任何数=0，但别忘了加进位！）\n"
            "- 末尾有0可以先不管，最后在积的末尾添0\n\n"
            "**📝 例题**：$124 × 23 = ?$\n\n"
            "  124\n"
            "× 23\n"
            "----\n"
            " 372  （124×3）\n"
            "248   （124×20，左移一位）\n"
            "----\n"
            "2852"
        )
    if "平行" in s or "垂直" in s or "平行四边形" in s and "梯形" not in t:
        return (
            f"【{sub}】\n\n"
            "**平行**：在同一平面内，**永不相交**的两条直线互相平行。（记作 a∥b）\n\n"
            "**垂直**：两条直线相交成**直角**（90°），就说它们互相垂直。（记作 a⊥b）\n"
            "- 交点叫**垂足**\n"
            "- 过一点能画**一条**已知直线的垂线和平行线\n\n"
            "**平行四边形特征**：\n"
            "- 两组对边分别**平行且相等**\n"
            "- 对角相等\n"
            "- 容易变形（伸缩门原理）\n\n"
            "**梯形特征**：\n"
            "- 只有一组对边**平行**\n"
            "- 平行的两边叫**上底、下底**，不平行的叫**腰**\n"
            "- 等腰梯形两腰相等"
        )
    if "画高" in s or ("平行四边形" in t and ("梯形" in s or "高" in s)):
        return (
            f"【{sub}】\n\n"
            "**从一条边上的一点向对边作垂线，这点和垂足间的线段叫做高**。\n\n"
            "**各类图形的高的特点**：\n"
            "- **平行四边形**：有无数条高（任选一边作底的垂线），所有高都相等\n"
            "- **梯形**：夹在上底和下底之间，也有无数条\n"
            "- **三角形**：从顶点向对边（或延长线）作垂线，有3条高\n\n"
            "💡 作图要点：用直角三角板的一条直角边与底重合，沿底滑动到顶点，另一直角边画的就是高。"
        )
    if "口算除法" in s or "试商" in s or "商是一位" in s or "商是两位" in s or ("除数" in t and s):
        return (
            f"【{sub}】\n\n"
            "除数是两位数的除法，关键是**试商**。\n\n"
            "**试商方法——四舍五入法**：\n"
            "1️⃣ 把除数看成最接近的**整十数**（用四舍五入）\n"
            "2️⃣ 用这个整十数去除被除数的前几位\n"
            "3️⃣ 初商可能偏大偏小，需要**调商**\n\n"
            "**调商口诀**：\n"
            "- 初商大了 → 往小调（商减小 1）\n"
            "- 初商小了 → 往大调（商增加 1）\n\n"
            "**商的变化规律**：\n"
            "- 不变：被除数和除数同时乘/除以同一个数（≠0），商不变\n"
            "- 被除数不变，除数×几 → 商反而变为原来的几分之一\n\n"
            "**📝 例题**：$280 ÷ 35 = ?$  （把 35 看成 40 试商）"
        )
    if "条形图" in s or "统计图" in s or ("条形统计图" in t and s):
        return (
            f"【{sub}】\n\n"
            "**条形统计图的特点**：\n"
            "- 用**直条的长短**直观表示数量的多少\n"
            "- 能清楚地看出**各种数量的多少**，便于比较\n\n"
            "**两种类型**：\n"
            "- **单式条形图**：只有一组数据\n"
            "- **复式条形图**：有两组或多组数据（用不同颜色区分，要有**图例**）\n\n"
            "**制作步骤**：\n"
            "1️⃣ 写标题、标注单位\n"
            "2️⃣ 画横轴（类别）和纵轴（数量，注意刻度均匀）\n"
            "3️⃣ 根据数据画直条（宽度一致、间隔均匀）\n"
            "4️⃣ 标数据（写在直条上方）\n\n"
            "**分析时关注**：最多/最少、相差多少、总和是多少"
        )
    if "沏茶" in s or "烙饼" in s or "田忌" in s or ("优化" in t and s):
        return (
            f"【{sub}——统筹优化思想】\n\n"
            "**核心原则**：合理安排顺序，让时间/资源利用最优。\n\n"
            "**① 沏茶问题（并行处理）**：\n"
            "能同时做的事情同时做，节省总时间。\n"
            "例：洗水壶1min→烧水8min（同时洗茶叶、找茶杯）→沏1min = 共10min（不是11min）\n\n"
            "**② 烙饼问题（交替优化）**：\n"
            "锅里每次最多烙2张饼面，要充分利用锅的空间。\n"
            "3张饼最优：先烙1、2的正面→取1放3烙2反+3正→烙1反+3反 = 共9分钟（不是12分钟）\n\n"
            "**③ 对策问题（田忌赛马）**：\n"
            "知己知彼，以弱胜强——用最弱的对方强的，留最强的对付对方次强的。"
        )

    # ===== 六年级数学补充 =====
    if "倒数" in s or ("分数除法" in t and "倒数" in s):
        return (
            f"【{sub}】\n\n"
            "**倒数的定义**：乘积是 **1** 的两个数互为倒数。\n"
            "$a × \\frac{1}{a} = 1$（$a ≠ 0$）\n\n"
            "**求倒数的方法**：\n"
            "- **真分数/假分数**：分子分母互换位置（$\\frac{3}{4} → \\frac{4}{3}$）\n"
            "- **整数**：先写成分母为1的分数，再颠倒（$5 = \\frac{5}{1} → \\frac{1}{5}$）\n"
            "- **小数**：先化成分数，再颠倒（$0.25 = \\frac{1}{4} → 4$）\n"
            "- **1的倒数是1，0没有倒数**（0不能做分母！）\n\n"
            "💡 倒数的关键作用：**分数除法转化为分数乘法**！"
        )
    if "分数除法计算" in s or ("分数除法" in t and ("计算" in s or "混合" in s)):
        return (
            f"【{sub}】\n\n"
            "**核心法则：除以一个数等于乘这个数的倒数！**\n\n"
            "$a ÷ b = a × \\frac{1}{b}$（$b ≠ 0$）\n\n"
            "**具体类型**：\n"
            "① 分数 ÷ 整数：$\\frac{3}{4} ÷ 6 = \\frac{3}{4} × \\frac{1}{6} = \\frac{1}{8}$\n"
            "② 分数 ÷ 分数：$\\frac{2}{3} ÷ \\frac{4}{9} = \\frac{2}{3} × \\frac{9}{4} = \\frac{3}{2}$\n"
            "③ 整数 ÷ 分数：$6 ÷ \\frac{3}{4} = 6 × \\frac{4}{3} = 8$\n"
            "④ 带分数要先化假分数再算\n\n"
            "**⚠️ 易错**：只颠倒除数（后面的那个），不要把被除数也颠倒了！"
        )
    if "百分数" in s and "意义" in s:
        return (
            f"【{sub}】\n\n"
            "**百分数**表示一个数是另一个数的百分之几（也叫**百分率**或**百分比**)。\n"
            "符号：**%**（读作「百分之…」）\n\n"
            "**与分数的区别**：\n"
            "- **百分数**：只表示两个数的倍比关系（后面不能带单位！）\n"
            "- **分数**：可以表示具体数量（可带单位，如 $\\frac{1}{2}$ kg）\n\n"
            "**常见百分率**：\n"
            "- 出勤率 = 出勤人数 ÷ 应出勤人数 × 100%\n"
            "- 合格率 = 合格数 ÷ 总数 × 100%\n"
            "- 发芽率 = 发芽数 ÷ 种子总数 × 100%\n"
            "- 增长率 = 增长量 ÷ 原来的量 × 100%"
        )
    if "互化" in s or ("百分数" in t and ("小数" in s or "分数" in s)) :
        return (
            f"【{sub}】\n\n"
            "**三者互化方法**：\n\n"
            "**① 小数 → 百分数**：小数点向右移两位，加%\n"
            "$0.78 = 78\\%$，$1 = 100\\%$，$0.5 = 50\\%$\n\n"
            "**② 百分数 → 小数**：去掉%，小数点向左移两位\n"
            "$43\\% = 0.43$，$120\\% = 1.2$\n\n"
            "**③ 分数 → 百分数**：先化小数再转百分数\n"
            "$\\frac{3}{4} = 0.75 = 75\\%$，$\\frac{1}{3} ≈ 33.3\\%$\n\n"
            "**④ 百分数 → 分数**：写成分母100的分数，约分\n"
            "$20\\% = \\frac{20}{100} = \\frac{1}{5}$\n\n"
            "💡 记住几个常用的：$\\frac{1}{2}=50\\%$，$\\frac{1}{4}=25\\%$，$\\frac{1}{5}=20\\%$，$\\frac{1}{8}=12.5\\%$"
        )
    if "圆柱" in s and ("认识" in s or "表面积" in s or "体积" in s) or ("圆柱" in t and s):
        return (
            f"【{sub}】\n\n"
            "**圆柱的基本特征**：\n"
            "- 上下两个**圆形底面**（完全相同、互相平行）\n"
            "- 一个**侧面**（展开是长方形/正方形）\n"
            "- 高：两底面之间的距离\n\n"
            "**表面积**：$S = 2πr^2 + 2πrh = 2πr(r+h)$\n"
            "= 两个底面积 + 侧面积\n\n"
            "**体积**：$V = πr^2h$（底面积 × 高）\n\n"
            "⚠️ 侧面展开图的**长 = 底面周长**，**宽 = 圆柱的高**。\n\n"
            "**📝 例题**：圆柱底面半径 $2\\text{cm}$，高 $5\\text{cm}$。表面积和体积？\n\n"
            "$S = 2×3.14×2^2 + 2×3.14×2×5 = 25.12 + 62.88 = 88(\\text{cm}^2)$\n"
            "$V = 3.14×2^2×5 = 62.8(\\text{cm}^3)$"
        )
    if "圆锥" in s or ("圆锥" in t and s):
        return (
            f"【{sub}】\n\n"
            "**圆锥的特征**：\n"
            "- 一个圆形底面 + 一个**曲面侧面**\n"
            "- 一个**顶点**（到底面圆心的距离是高）\n"
            "- 只有 **1 条高**（从顶点垂直到底面圆心）\n\n"
            "**体积公式**：$V = \\frac{1}{3}πr^2h$\n"
            "= **等底等高的圆柱体积的 $\\frac{1}{3}$**\n\n"
            "**🔑 这个 $\\frac{1}{3}$ 极其重要！**\n"
            "圆锥削成最大的圆柱：体积变为 3 倍；\n"
            "圆柱削成最大的圆锥：削去了体积的 $\\frac{2}{3}$。\n\n"
            "**📝 例题**：圆锥底面半径 $3\\text{cm}$，高 $6\\text{cm}$。体积？\n\n"
            "$V = \\frac{1}{3} × 3.14 × 3^2 × 6 = \\frac{1}{3} × 169.56 = 56.52(\\text{cm}^3)$"
        )
    if "比例的意义" in s or ("比例" in t and "意义" in s):
        return (
            f"【{sub}】\n\n"
            "**比例**：表示两个**比**相等的式子，叫做比例。\n"
            "$a:b = c:d$ 或 $\\frac{a}{b} = \\frac{c}{d}$\n\n"
            "**各部分名称**：\n"
            "$a:b = c:d$ 中，$a,d$ 叫**外项**，$b,c$ 叫**内项**。\n\n"
            "**基本性质**：两外项之积 = 两内项之积\n"
            "$a × d = b × c$（交叉相乘相等）\n\n"
            "**判断能否组成比例**：\n"
            "算出两个比的比值（或算外项积和内项积），若相等则能组成比例。\n\n"
            "**📝 例题**：$3:4$ 和 $9:12$ 能组成比例吗？\n\n"
            "$3:4 = 0.75$，$9:12 = 0.75$ → 相等 → **能**组成比例 $3:4 = 9:12$"
        )
    if "解比例" in s or ("比例" in t and ("基本" in s or "解" in s)):
        return (
            f"【{sub}】\n\n"
            "**解比例**：根据比例的基本性质求未知项。\n\n"
            "**方法**：\n"
            "1️⃣ 设未知数为 x\n"
            "2️⃣ 根据「外项积=内项积」化为方程\n"
            "3️⃣ 解方程\n\n"
            "**📝 例题**：解比例 $x : 4 = 9 : 12$\n\n"
            "解：$12x = 4 × 9$  （外项积=内项积）\n"
            "$12x = 36$\n"
            "$x = 3$"
        )
    if "正比例" in s or "反比例" in s or ("比例" in t and ("正" in s or "反" in s)):
        return (
            f"【{sub}】\n\n"
            "**两种相关联的量**：一种量变化，另一种量也随着变化。\n\n"
            "**正比例（$y = kx$，k一定）**：\n"
            "- 两种量的**比值一定** → 成正比例\n"
            "- 图像：过原点的**一条直线**（上升）\n"
            "- 例：速度一定，路程与时间成正比例；单价一定，总价与数量成正比例\n\n"
            "**反比例（$xy = k$，k一定）**：\n"
            "- 两种量的**乘积一定** → 成反比例\n"
            "- 图像：**曲线**（下降）\n"
            "- 例：路程一定，速度与时间成反比例；总量一定，工作效率与时间成反比例\n\n"
            "**判断口诀**：「先找关联，一定的是乘还是除→乘则反，除则正」"
        )
    if "比例尺" in s:
        return (
            f"【{sub}】\n\n"
            "**比例尺** = 图上距离 : 实际距离\n\n"
            "**三种形式**：\n"
            "- **数值式**：$1:1000000$（或 $\\frac{1}{1000000}$）\n"
            "- **线段式**：画一段标 0 和实际距离\n"
            "- **文字式**：「图上 1cm 代表实际 10km」\n\n"
            "**换算**：\n"
            "实际距离 = 图上距离 ÷ 比例尺\n"
            "图上距离 = 实际距离 × 比例尺\n\n"
            "**📝 例题**：地图比例尺 1:5000000，量得甲乙两地 3cm。实际距离？\n\n"
            "实际距离 $= 3 ÷ \\frac{1}{5000000} = 3 × 5000000 = 15000000\\text{cm} = 150\\text{km}$"
        )
    if "抽屉" in s or "鸽巢" in s or "最不利" in s:
        return (
            f"【{sub}——抽屉原理】\n\n"
            "**基本原理**：把 n+1 个物体放进 n 个抽屉，至少有一个抽屉里放了 ≥2 个物体。\n\n"
            "**最不利原则**（保证型问题）：考虑最倒霉的情况。\n\n"
            "**解题模式**：\n"
            "「至少数 = 物体数 ÷ 抽屉数（向上取整）」\n"
            "即：$\\lceil \\frac{n}{m} \\rceil$\n\n"
            "**📝 例题**：52 个同学至少有几人同一个月生日？\n\n"
            "解：12个月（抽屉），52 人（物体）\n"
            "$52 ÷ 12 = 4$ 余 $4$\n"
            "即使每月都分了 4 人，还有 4 人没分 → 这 4 人无论放哪月，都会使那月变成 5 人\n\n"
            "答：**至少 5 人**同月。"
        )
    if "植树" in s or ("植树" in t and s):
        return (
            f"【{sub}】\n\n"
            "植树问题的核心是找**间隔数**与**棵数**的关系：\n\n"
            "**① 两端都栽**：棵数 = 间隔数 + 1 = 全长 ÷ 间距 + 1\n"
            "（手指数 = 间隔数 + 1）\n\n"
            "**② 两端都不栽**：棵数 = 间隔数 - 1 = 全长 ÷ 间距 - 1\n\n"
            "**③ 封闭图形（环形）**：棵数 = 间隔数 = 全长 ÷ 间距\n"
            "（环形首尾相连，不需要 +1 或 -1）\n"
            "例：圆形池塘周长 120m，每隔 6 米栽一棵 → $120÷6=20$ 棵\n\n"
            "**📝 例题**：在一条 100m 长的路一侧植树（两端都栽），每隔 5m 栽一棵。一共栽多少棵？\n\n"
            "解：$100 ÷ 5 + 1 = 20 + 1 = 21$（棵）\n\n"
            "答：共栽 **21 棵**。"
        )

    # ===== 其他年级数学 =====
    if "大数的认识" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "认识更大的数是小学数学的重要内容。从个级（个十百千）扩展到万级（万千百万）、亿级。\n"
            "重点掌握：**分级读写法**（四位一级）、**数位顺序表**、**改写和求近似数**。\n"
            "建议配合数位顺序表反复练习读法和写法，特别注意中间和末尾有 0 的情况。"
        )
    if "角的度量" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "本单元学习角的度量工具（量角器）和分类。核心技能：**正确使用量角器量角和画角**。\n"
            "记住五类角的大小关系：锐角 < 直角(90°) < 钝角 < 平角(180°) < 周角(360°)。\n"
            "要多动手操作——量角器的中心要对准顶点，0刻度线要对准角的一边。"
        )
    if "平行四边形和梯形" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "本单元学习两类特殊的四边形。重点是理解**平行和垂直**的概念，掌握平行四边形和梯形的特征。\n"
            "学会用直尺和三角板**画垂线和平行线**，会给这些图形**画高**（高必须垂直于底边）。"
        )
    if "除数是两位数的除法" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "本单元学习除数是两位数的笔算除法。核心是**试商方法**（四舍五入法把除数看成整十数）和**调商技巧**。\n"
            "还要理解**商的变化规律**——这是后续学习分数、小数除法和比的基础。"
        )
    if "条形统计图" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "本单元学习用条形统计图整理和分析数据。重点是**复式条形图**的制作和解读——学会比较两组数据的差异。\n"
            "要注意：直条的宽度要一致、间隔要均匀、纵轴刻度要从 0 开始才不会误导。"
        )
    if "数学广角·优化" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "优化问题训练我们的**统筹思维**——怎样安排才能用时最少、效率最高？\n"
            "经典问题包括沏茶（并行处理）、烙饼（交替优化）、田忌赛马（对策论入门）。"
        )
    if "简易方程" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "方程是代数学的开端！用字母代替数，用等式表达数量关系，通过**等式性质**求解。\n"
            "这是从「算术思维」向「代数思维」的重要跨越。重点：解方程的规范书写和列方程解决实际问题。"
        )
    if "分数除法" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "分数除法的核心法则是「**除以一个数等于乘这个数的倒数**」。\n"
            "先学好**倒数**的概念，再掌握分数除法的计算方法，最后应用于解决实际问题中的「已知一个数的几分之几是多少，求这个数」。"
        )
    if "百分数" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "百分数在生活中无处不在——折扣、利率、税率、命中率、发芽率……\n"
            "核心是理解**百分数的意义**（表示两个数的倍比关系），熟练**分数、小数、百分数的互化**，并能解决各种百分数应用题。"
        )
    if "圆柱与圆锥" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "立体几何进入新阶段！从平面图形扩展到**旋转体**。\n"
            "圆柱由矩形旋转而成，圆锥由直角三角形旋转而成。重点是**表面积和体积公式的理解和应用**。\n"
            "特别记住：圆锥体积是等底等高圆柱的 **$\\frac{1}{3}$**！"
        )
    if "比例" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "比例是比的知识延伸，也是中学正比例函数的基础。\n"
            "核心：比例的基本性质（内外项积相等）、**正比例和反比例的判断**、解比例、比例尺的应用。\n"
            "判断口诀：「先关联，后定量——乘积一定反比例，比值一定正比例」"
        )
    if "数学广角·鸽巢" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "鸽巢原理（也叫抽屉原理）是组合数学中最基本的原理。\n"
            "核心思想：如果物体数比抽屉数多，那么至少有一个抽屉里有多个物体。常用于解决「至少…」「保证…」类型的问题。\n"
            "关键是用好**最不利原则**（考虑最坏情况）。"
        )
    if "整理与复习" in t:
        return (
            f"【{t} · {sub}】\n\n"
            "这是小学数学的总复习阶段。系统回顾六年来学的数与代数（整数/小数/分数/方程）、图形与几何（平面图形/立体图形/位置）、统计与概率（统计图/可能性）三大领域。\n"
            "建议按知识网络图逐个梳理，找出薄弱环节重点突破。"
        )

    # ===== 非数学学科 =====
    # 语文
    if subject == "语文":
        return (
            f"{open_line}\n\n"
            f"「{sub}」是语文学习中的重要内容。\n\n"
            f"**学习建议**：\n"
            f"1. 多朗读课文，感受语言节奏和情感\n"
            f"2. 积累文中的好词好句，摘抄到笔记本上\n"
            f"3. 思考作者的写作手法（比喻/拟人/排比/对比等）\n"
            f"4. 结合生活体验理解文章主旨\n"
            f"5. 尝试用自己话复述或仿写片段"
        )
    # 英语
    if subject == "英语":
        return (
            f"{open_line}\n\n"
            f"**{sub}** Learning Focus:\n\n"
            f"1. **Listen & Repeat**: 听标准发音，模仿语调和重音\n"
            f"2. **Key Patterns**: 掌握本课的核心句型结构\n"
            f"3. **Practice**: 用新学的表达造自己的句子\n"
            f"4. **Vocabulary**: 记忆单词时注意拼写和用法搭配\n"
            f"5. **Role-play**: 找伙伴进行对话练习"
        )
    # 物理
    if subject == "物理":
        return (
            f"{open_line}\n\n"
            f"**{sub}** 的学习要点：\n\n"
            f"1. **理解物理本质**：不要死记公式，先弄清概念的物理含义\n"
            f"2. **单位很重要**：国际单位制（SI）要牢记，计算前先统一单位\n"
            f"3. **联系生活**：观察身边的现象（如惯性、浮力、光的折射）\n"
            f"4. **画图分析**：受力分析图、光路图、电路图帮助理解\n"
            f"5. **实验验证**：亲手做实验比看书印象深刻得多"
        )
    # 化学
    if subject == "化学":
        return (
            f"{open_line}\n\n"
            f"**{sub}** 学习要点：\n\n"
            f"1. **物质观**：世界由元素组成，化学反应是原子的重新排列\n"
            f"2. **方程式**：配平是基本功，条件（△/点燃/催化剂）不能漏\n"
            f"3. **实验安全**：了解药品性质和操作规范\n"
            f"4. **归纳对比**：酸碱盐的性质用表格对比记忆\n"
            f"5. **联系生活**：厨房中的化学、环境污染与治理"
        )
    # 生物
    if subject == "生物":
        return (
            f"{open_line}\n\n"
            f"**{sub}** 学习要点：\n\n"
            f"1. **结构与功能相适应**：生物学的核心思想\n"
            f"2. **观察为主**：借助显微镜和插图理解微观结构\n"
            f"3. **概念辨析**：容易混淆的概念（如DNA/基因/染色体）要做对比表\n"
            f"4. **知识网络**：按层次（细胞→组织→器官→系统→个体→种群→群落→生态系统）构建框架\n"
            f"5. **关注前沿**：基因编辑、克隆技术、生态保护等热点"
        )
    # 科学（小学）
    if subject == "科学":
        return (
            f"{open_line}\n\n"
            f"关于「{sub}」的学习要点：\n\n"
            f"1. **动手实验**：科学课的灵魂是实验——认真观察记录现象\n"
            f"2. **提出问题**：看到现象多问「为什么」「如果…会怎样」\n"
            f"3. **猜想验证**：先提出假设，再设计实验验证\n"
            f"4. **记录数据**：用表格和图表整理观察结果\n"
            f"5. **得出结论**：基于证据得出结论，而不是凭感觉"
        )
    # 历史
    if subject == "历史":
        return (
            f"{open_line}\n\n"
            f"学习「{sub}」的建议：\n\n"
            f"1. **时间线思维**：把事件放到时间轴上看前后因果关系\n"
            f"2. **人物-事件-影响**：三位一体记忆\n"
            f"3. **地图辅助**：结合历史地图理解空间变化\n"
            f"4. **唯物史观**：从经济基础、社会矛盾角度分析历史进程\n"
            f"5. **以史为鉴**：思考历史对今天的启示"
        )
    # 地理
    if subject == "地理":
        return (
            f"{open_line}\n\n"
            f"「{sub}」学习要点：\n\n"
            f"1. **图文结合**：地理离不开图——分布图/示意图/统计图都要会读\n"
            f"2. **空间定位**：知道「在哪里」是第一步\n"
            f"3. **因果分析**：自然环境（地形气候河流）→ 人文活动（农业工业城市）\n"
            f"4. **比较法**：对比不同地区的异同（如秦岭淮河南北差异）\n"
            f"5. **联系实际**：关注身边的地理问题（天气/交通/环境）"
        )
    # 政治/道德与法治
    if subject in ("道德与法治", "思想政治"):
        return (
            f"{open_line}\n\n"
            f"学习「{sub}」的方法：\n\n"
            f"1. **是什么-为什么-怎么做**：三步框架梳理观点\n"
            f"2. **联系生活**：从身边新闻和社会热点理解抽象概念\n"
            f"3. **价值判断**：培养正确的价值观和法治意识\n"
            f"4. **知行合一**：把学到的道理落实到行动中\n"
            f"5. **关注时事**：结合最新政策和法律动态"
        )

    # ===== 通用知识点关键词桥（覆盖缺专门分支的常见小学知识点）=====
    # 这些知识点没有独立分支时，用关键词命中生成可出题的真实内容（含 $进率=$ 与属性句）
    if any(k in s for k in ("毫米", "分米", "厘米", "千米", "公里", "吨", "长度单位", "质量单位", "测量")) or "测量" in t:
        return (
            f"【{sub}——常见的度量单位】\n\n"
            "**长度单位及进率**：\n"
            "$1\\text{ km} = 1000\\text{ m}$\n"
            "$1\\text{ m} = 10\\text{ dm} = 100\\text{ cm}$\n"
            "$1\\text{ dm} = 10\\text{ cm}$，$1\\text{ cm} = 10\\text{ mm}$\n\n"
            "**质量单位及进率**：\n"
            "$1\\text{ t} = 1000\\text{ kg}$，$1\\text{ kg} = 1000\\text{ g}$\n\n"
            "**换算方法**：大单位化小单位乘进率，小单位化大单位除以进率。\n"
            "⚠️ 千米和米之间隔了「分米、厘米」，1 km = 1000 m 而不是 100 m！"
        )
    if ("角" in s and any(k in s for k in ("直角", "锐角", "钝角", "平角", "周角", "画", "分类", "各部分", "初步"))) \
            or "角的初步认识" in t or ("角" in t and "认识" in t):
        return (
            f"【{sub}——角的认识】\n\n"
            "**角的计量单位是「度」，符号 °**。角的大小与两边张开程度有关，与边的长短无关。\n\n"
            "**角的分类**：\n"
            "$锐角 < 90°$\n"
            "$直角 = 90°$\n"
            "$90° < 钝角 < 180°$\n"
            "$平角 = 180°$\n"
            "$周角 = 360°$\n\n"
            "关系：$1\\text{ 周角} = 2\\text{ 平角} = 4\\text{ 直角} = 360°$\n"
            "画直角要用三角板的直角，画角要用量角器。"
        )
    if "倍" in s or "倍" in t:
        return (
            f"【{sub}——倍的意义】\n\n"
            "**倍**表示两个数之间的倍数比较关系，即一个数里包含几个另一个数。\n\n"
            "**求一个数的几倍是多少**：用**乘法**。\n"
            "例：12 的 3 倍是多少？ $12 × 3 = 36$\n\n"
            "**求一个数是另一个数的几倍**：用**除法**。\n"
            "例：36 是 12 的几倍？ $36 ÷ 12 = 3$（倍）\n\n"
            "⚠️ 「倍」后面**不写单位**，它是表示关系的数。"
        )
    if "表内乘法" in s or "乘法口诀" in s or ("乘法" in t and "表内" in s):
        return (
            f"【{sub}——表内乘法】\n\n"
            "**乘法是求几个相同加数和的简便运算**。\n"
            "例：$6 × 7 = 42$（表示 7 个 6 相加）\n\n"
            "**乘法口诀表**要背熟，它是所有乘除法计算的基础。\n"
            "⚠️ 交换两个因数的位置，积不变（$a × b = b × a$）。"
        )
    if any(k in s for k in ("时", "分", "秒", "钟表", "时间", "日历", "年", "月", "钟")) \
            or "认识时间" in t or "认识钟表" in t:
        return (
            f"【{sub}——时间单位】\n\n"
            "**时间单位及进率**：\n"
            "$1\\text{ 时} = 60\\text{ 分}$，$1\\text{ 分} = 60\\text{ 秒}$\n\n"
            "**认钟表**：分针走一圈（60 小格）= 1 小时；时针走一大格 = 1 小时。\n"
            "短针（时针）看「时」，长针（分针）看「分」。\n\n"
            "⚠️ 时针过了几就是几时多，分针指向数字几就乘 5 得分钟数。"
        )
    if any(k in s for k in ("上下", "左右", "前后", "位置", "方向", "东南西北")) \
            or "位置" in t or "方向" in t:
        return (
            f"【{sub}——位置与方向】\n\n"
            "**确定位置常用方法**：\n"
            "- 用**上、下、左、右、前、后**描述相对位置\n"
            "- 用**东、南、西、北**描述方向（面北背南，左西右东）\n"
            "- 用**数对 (列,行)** 表示确定位置（先列后行）\n\n"
            "描述路线要说清方向和距离，如「从学校向北走 200 米到图书馆」。"
        )

    # ===== 高中数学·函数概念 =====
    if "函数概念" in s or ("函数" in s and any(k in s for k in ("定义","映射","对应"))):
        return (
            f"【{s}】\n\n"
            "**函数的定义**：设A、B是非空数集，如果按照某种确定的对应关系f，使对于集合A中的**任意一个**数x，\n"
            "在集合B中都有**唯一确定**的数f(x)和它对应，就称f:A→B为从集合A到集合B的一个函数。\n\n"
            "**三要素**：定义域A、值域{f(x)|x∈A}、对应关系f（缺一不可）\n\n"
            "**📝 例题1**：函数 $f(x)=\\frac{\\sqrt{x-1}}{x-2}$ 的定义域是？\n"
            "解：需满足 $x-1 \\geq 0$ 且 $x-2 \\neq 0$ → $x \\geq 1$ 且 $x \\neq 2$\n"
            "答案：$[1, 2) \\cup (2, +\\infty)$\n\n"
            "**📝 例题2**：若 $f(x)=x^2-2x$，则 $f(3)=$ ____，$f(0)=$ ____\n"
            "解：$f(3) = 3^2 - 2\\times 3 = 9 - 6 = 3$；$f(0) = 0^2 - 0 = 0$"
        )
    if "单调性" in s or ("增" in s and "减" in s):
        return (
            f"【{s}】\n\n"
            "**单调性的定义**：\n"
            "- **增函数**：任取 $x_1 < x_2$，都有 $f(x_1) < f(x_2)$（图象上升）\n"
            "- **减函数**：任取 $x_1 < x_2$，都有 $f(x_1) > f(x_2)$（图象下降）\n\n"
            "**判定方法**：作差法/作商法/导数法（选修）\n\n"
            "**📝 例题**：证明 $f(x) = x^2$ 在 $(0, +\\infty)$ 上是增函数。\n"
            "证：任取 $0 < x_1 < x_2$，则 $f(x_1)-f(x_2) = x_1^2-x_2^2 = (x_1+x_2)(x_1-x_2)$\n"
            "$\\because x_1+x_2 > 0, x_1-x_2 < 0$ ∴ $f(x_1)-f(x_2) < 0$，即 $f(x_1) < f(x_2)$ ✓"
        )
    if "奇偶性" in s:
        return (
            f"【{s}】\n\n"
            "**奇偶性的定义**（前提：定义域关于原点对称）：\n"
            "- **偶函数**：$f(-x) = f(x)$（图象关于y轴对称），如 $f(x)=x^2$, $f(x)=|x|$\n"
            "- **奇函数**：$f(-x) = -f(x)$（图象关于原点对称），如 $f(x)=x^3$, $f(x)=\\frac{1}{x}$\n\n"
            "**📝 例题1**：判断 $f(x) = x^4 + x^2 + 1$ 的奇偶性。\n"
            "解：$f(-x) = (-x)^4+(-x)^2+1 = x^4+x^2+1 = f(x)$ → **偶函数** ✓\n\n"
            "**📝 例题2**：判断 $f(x) = x^3 - x$ 的奇偶性。\n"
            "解：$f(-x) = (-x)^3-(-x) = -x^3+x = -(x^3-x) = -f(x)$ → **奇函数** ✓\n\n"
            "⚠️ 若定义域不关于原点对称（如 $f(x)=x^2, x\\in[0,+∞)$），则**非奇非偶**！"
        )
    if "值域" in s or ("最值" in s and "函数" in t):
        return (
            f"【{s}——求函数值域的方法】\n\n"
            "**常用方法**：\n"
            "1. **观察法**：一次函数、二次函数直接看\n"
            "2. **配方法**：二次型 $f(x)=ax^2+bx+c$ 配方后看顶点\n"
            "3. **换元法**：复合函数换元转化\n"
            "4. **分离常数法**：分式函数分离常数\n"
            "5. **单调性法**：利用函数单调性确定范围\n\n"
            "**📝 例题**：求 $f(x) = x^2 - 4x + 3$ 在 $x\\in[0,3]$ 上的值域。\n"
            "解：配方得 $f(x)=(x-2)^2-1$，对称轴 $x=2∈[0,3]$\n"
            "$f_{min}=f(2)=-1$；端点 $f(0)=3, f(3)=0$ → $f_{max}=3$\n"
            "答案：值域为 $[-1, 3]$"
        )
    if "函数图像" in s or "图象变换" in s or "平移伸缩" in s:
        return (
            f"【{s}——函数图象的变换】\n\n"
            "**基本变换规则**（由 $y=f(x)$ 得到新图象）：\n\n"
            "| 变换 | 解析式 | 规律 |\n"
            "|------|--------|------|\n"
            "| 左移a | $y=f(x+a)$ | **左加右减** |\n"
            "| 上移b | $y=f(x)+b$ | **上正下负** |\n"
            "| 关于x轴翻折 | $y=-f(x)$ | x不变，y变号 |\n"
            "| 关于y轴翻折 | $y=f(-x)$ | y不变，x变号 |\n"
            "| 横向伸缩k倍 | $y=f(kx)$ | 横坐标变为原来的 $1/k$ |\n\n"
            "**📝 例题**：将 $y=x^2$ 的图象**左移1个单位再上移2个单位**，得到的解析式是？\n"
            "解：左移1 → $y=(x+1)^2$；上移2 → $y=(x+1)^2+2$\n"
            "展开：$y=x^2+2x+3$"
        )

    # ===== 高中数学·三角函数 =====
    if "三角函数" in s or any(k in s for k in ("正弦","余弦","正切","sin","cos","tan","诱导公式")) \
            or (any(k in t for k in ("三角函数","三角恒等"))):
        return (
            f"【{s}】\n\n"
            "**任意角的三角函数**（单位圆定义）：\n"
            "$\\sin \\alpha = y$, $\\cos \\alpha = x$, $\\tan \\alpha = \\frac{y}{x}$（$x≠0$）\n\n"
            "**同角基本关系**：\n"
            "$\\sin^2\\alpha + \\cos^2\\alpha = 1$（平方关系）\n"
            "$\\tan \\alpha = \\frac{\\sin\\alpha}{\\cos\\alpha}$（商数关系）\n\n"
            "**诱导公式口诀**：「奇变偶不变，符号看象限」\n\n"
            "**📝 例题1**：已知 $\\sin\\alpha = \\frac{3}{5}$，$\\alpha$ 在第二象限，求 $\\cos\\alpha$ 和 $\\tan\\alpha$。\n"
            "解：$\\cos\\alpha = -\\sqrt{1-\\sin^2\\alpha} = -\\sqrt{1-\\frac{9}{25}} = -\\frac{4}{5}$（二象限cos<0）\n"
            "$\\tan\\alpha = \\frac{\\sin\\alpha}{\\cos\\alpha} = \\frac{3/5}{-4/5} = -\\frac{3}{4}$\n\n"
            "**📝 例题2**：$\\sin(180°-\\alpha)=$ ____，$\\cos(\\pi+\\alpha)=$ ____\n"
            "解：$\\sin(180°-\\alpha)=\\sin\\alpha$（奇变偶不变：180°=2×90°偶，不变；二象限sin>0）\n"
            "$\\cos(\\pi+\\alpha)=-\\cos\\alpha$（π=2×π/2偶，不变；三象限cos<0）"
        )
    if "两角和差" in s or "辅助角" in s or "倍角公式" in s or "半角" in s:
        return (
            f"【{s}】\n\n"
            "**两角和与差公式**：\n"
            "$\\sin(\\alpha\\pm\\beta)=\\sin\\alpha\\cos\\beta\\pm\\cos\\alpha\\sin\\beta$\n"
            "$\\cos(\\alpha\\pm\\beta)=\\cos\\alpha\\cos\\beta\\mp\\sin\\alpha\\sin\\beta$\n"
            "$\\tan(\\alpha\\pm\\beta)=\\frac{\\tan\\alpha\\pm\\tan\\beta}{1\\mp\\tan\\alpha\\tan\\beta}$\n\n"
            "**二倍角公式**：\n"
            "$\\sin 2\\alpha = 2\\sin\\alpha\\cos\\alpha$\n"
            "$\\cos 2\\alpha = \\cos^2\\alpha-\\sin^2\\alpha = 2\\cos^2\\alpha-1 = 1-2\\sin^2\\alpha$\n\n"
            "**📝 例题**：已知 $\\cos\\alpha = \\frac{4}{5}$，$\\alpha\\in(0,\\frac{\\pi}{2})$，求 $\\sin 2\\alpha$。\n"
            "解：$\\sin\\alpha = \\sqrt{1-(\\frac{4}{5})^2} = \\frac{3}{5}$\n"
            "$\\sin 2\\alpha = 2\\times\\frac{3}{5}\\times\\frac{4}{5} = \\frac{24}{25}$"
        )

    # ===== 高中数学·数列 =====
    if "数列" in t or "等差" in s or "等比" in s or "通项" in s or "求和" in s:
        return (
            f"【{s}】\n\n"
            "**等差数列**：$a_n = a_1+(n-1)d$，前n项和 $S_n = \\frac{n(a_1+a_n)}{2} = na_1+\\frac{n(n-1)}{2}d$\n\n"
            "**等比数列**：$a_n=a_1 q^{n-1}$，前n项和 $S_n = \\frac{a_1(1-q^n)}{1-q}$（$q\\neq 1$）\n\n"
            "**重要性质**：\n"
            "- 等差：$m+n=p+q \\Rightarrow a_m+a_n=a_p+a_q$（下标和相等→项的和相等）\n"
            "- 等比：$m+n=p+q \\Rightarrow a_ma_n=a_pa_q$\n\n"
            "**📝 例题1**：等差数列中 $a_1=2, d=3$，则 $a_{10}=$ ____, $S_{10}=$ ____\n"
            "解：$a_{10}=2+9\\times3=29$；$S_{10}=\\frac{10\\times(2+29)}{2}=155$\n\n"
            "**📝 例题2**：等比数列中 $a_1=3, q=2$，则 $a_5=$ ____, $S_4=$ ____\n"
            "解：$a_5=3\\times 2^{4}=48$；$S_4=\\frac{3\\times(1-16)}{1-2}=45$"
        )

    # ===== 高中数学·向量 =====
    if "向量" in s or "平面向量" in t:
        return (
            f"【{s}】\n\n"
            "**向量的线性运算**：\n"
            "- 加法：三角形法则 / 平行四边形法则\n"
            "- 减法：$\\vec{a}-\\vec{b}=$ 从B指向A（共起点时）\n"
            "- 数乘：$\\lambda\\vec{a}$（$\\lambda>0$ 同向，$\\lambda<0$ 反向）\n\n"
            "**数量积（点乘）**：$\\vec{a}\\cdot\\vec{b}=|\\vec{a}||\\vec{b}|\\cos\\theta = x_1x_2+y_1y_2$\n\n"
            "**坐标运算**：$\\vec{a}(x_1,y_1), \\vec{b}(x_2,y_2)$ → $\\vec{a}\\cdot\\vec{b}=x_1x_2+y_1y_2$\n"
            "模长：$|\\vec{a}|=\\sqrt{x_1^2+y_1^2}$；夹角：$\\cos\\theta=\\frac{\\vec{a}\\cdot\\vec{b}}{|\\vec{a}||\\vec{b}|}$\n\n"
            "**📝 例题**：已知 $\\vec{a}=(3,4), \\vec{b}=(1,-2)$，求 $\\vec{a}\\cdot\\vec{b}$ 和 $|\\vec{a}|$。\n"
            "解：$\\vec{a}\\cdot\\vec{b}=3\\times1+4\\times(-2)=3-8=-5$；$|\\vec{a}|=\\sqrt{3^2+4^2}=5$"
        )

    # ===== 高中数学·立体几何 =====
    if "立体" in s or "空间" in t or "柱体" in s or "锥体" in s or "球" in s and "面积" not in s:
        return (
            f"【{s}】\n\n"
            "**常见空间几何体的体积与表面积**：\n\n"
            "| 几何体 | 体积V | 表面积S |\n"
            "|--------|-------|----------|\n"
            "| 长方体 | $abc$ | $2(ab+bc+ca)$ |\n"
            "| 正方体 | $a^3$ | $6a^2$ |\n"
            "| 圆柱 | $\\pi r^2 h$ | $2\\pi r(r+h)$ |\n"
            "| 圆锥 | $\\frac{1}{3}\\pi r^2 h$ | $\\pi r(r+l)$ |\n"
            "| 球 | $\\frac{4}{3}\\pi R^3$ | $4\\pi R^2$ |\n\n"
            "**📝 例题**：一个圆柱底面半径 $r=3\\text{cm}$，高 $h=5\\text{cm}$。求体积和表面积。\n"
            "解：$V=\\pi\\times 3^2\\times 5=45\\pi\\approx 141.37(\\text{cm}^3)$\n"
            "$S=2\\pi\\times 3\\times(3+5)=48\\pi\\approx 150.80(\\text{cm}^2)$"
        )
    if "线面" in s or "平行垂直" in s or "二面角" in s:
        return (
            f"【{s}】\n\n"
            "**线面平行判定**：平面外一条直线与此平面内的一条直线平行，则该直线与此平面平行。\n\n"
            "**线面垂直判定**：若一条直线与一个平面内的**两条相交直线**都垂直，则该直线与此平面垂直。\n\n"
            "**三垂线定理**（及其逆定理）：关键找**射影**\n\n"
            "**📝 例题**：在正方体ABCD-A'B'C'D'中，证明直线AC // 平面A'C'D。\n"
            "证：连接AD'交A'D于O，连接OC。由中位线知 AC // OC，又 OC⊂平面A'C'D \n"
            "且 AC ⊄ 平面A'C'D → AC // 平面A'C'D ✓"
        )

    # ===== 高中数学·解析几何 =====
    if "直线" in s and "圆" not in t or "斜率" in s or "距离" in s and "点到直" in s:
        return (
            f"【{s}】\n\n"
            "**直线的方程**：\n"
            "- 点斜式：$y-y_0=k(x-x_0)$\n"
            "- 斜截式：$y=kx+b$（k=斜率, b=y轴截距）\n"
            "- 一般式：$Ax+By+C=0$（$A^2+B^2>0$）\n\n"
            "**两点间距离**：$|AB|=\\sqrt{(x_2-x_1)^2+(y_2-y_1)^2}$\n"
            "**点到直线距离**：$d=\\frac{|Ax_0+By_0+C|}{\\sqrt{A^2+B^2}}$\n"
            "**两条直线平行**：$k_1=k_2$（斜率存在时）；**垂直**：$k_1k_2=-1$\n\n"
            "**📝 例题**：过点 A(1,2) 且斜率为 -1 的直线方程是______；点 P(3,4) 到该直线的距离是______。\n"
            "解：点斜式 $y-2=-(x-1)$ → $x+y-3=0$ 或 $y=-x+3$\n"
            "距离：$d=\\frac{|3+4-3|}{\\sqrt{1^2+1^2}}=\\frac{4}{\\sqrt{2}}=2\\sqrt{2}$"
        )
    if "圆" in s and "解析" in t or "圆的方程" in s:
        return (
            f"【{s}】\n\n"
            "**圆的标准方程**：$(x-a)^2+(y-b)^2=r^2$（圆心C(a,b)，半径r）\n"
            "**一般方程**：$x^2+y^2+Dx+Ey+F=0$（$D^2+E^2-4F>0$）\n\n"
            "**位置关系**（圆心到直线距离d vs 半径r）：\n"
            "- 相离：$d>r$（无公共点）\n"
            "- 相切：$d=r$（1个公共点）\n"
            "- 相交：$d<r$（2个公共点）\n\n"
            "**📝 例题**：圆心 C(3,-2)，半径 $r=4$，写出标准方程。点 P(6,2) 与圆的位置关系？\n"
            "解：$(x-3)^2+(y+2)^2=16$；$d=\\sqrt{(6-3)^2+(2+2)^2}=\\sqrt{9+16}=5>4$ → 圆外"
        )

    # ===== 高中数学·导数 =====
    if "导数" in s or "微分" in s or "变化率" in s or "极值" in s and "函数" in t:
        return (
            f"【{s}】\n\n"
            "**基本初等函数的导数**：\n"
            "$(x^n)'=nx^{n-1}$，$(e^x)'=e^x$，$(\\ln x)'=\\frac{1}{x}$\n"
            "$(\\sin x)'=\\cos x$，$(\\cos x)'=-\\sin x$，$(\\tan x)'=\\sec^2 x$\n\n"
            "**运算法则**：$(u\\pm v)'=u'\\pm v'$，$(uv)'=u'v+uv'$，$(\\frac{u}{v})'=\\frac{u'v-uv'}{v^2}$\n\n"
            "**极值判定**：$f'(x_0)=0$（必要条件），若 $f'(x)$ 在 $x_0$ 处**左正右负**→极大值\n\n"
            "**📝 例题**：求 $f(x)=x^3-3x^2+2$ 的单调区间和极值。\n"
            "解：$f'(x)=3x^2-6x=3x(x-2)$\n"
            "令 $f'(x)=0$ → $x=0$ 或 $x=2$\n"
            "↑: $(-\\infty,0)\\cup(2,+\\infty)$ ↓: $(0,2)\n"
            "$f_{极大}=f(0)=2$；$f_{极小}=f(2)=-2$"
        )

    # ===== 高中数学·概率统计 =====
    if "概率" in s or "排列组合" in s or "计数" in s or "统计" in s:
        return (
            f"【{s}】\n\n"
            "**古典概型**：$P(A)=\\frac{m}{n}$（m=事件A包含的基本结果数，n=总结果数）\n\n"
            "**排列**：$A_n^m = n(n-1)(n-2)...(n-m+1)=\\frac{n!}{(n-m)!}$（有序）\n"
            "**组合**：$C_n^m = \\frac{A_n^m}{m!}=\\frac{n!}{m!(n-m)!}$（无序）\n\n"
            "**互斥事件**：$P(A\\cup B)=P(A)+P(B)$\n"
            "**独立事件**：$P(AB)=P(A)\\times P(B)$\n\n"
            "**📝 例题1**：从5人中选3人参加活动，有多少种选法？（有序/无序各多少？）\n"
            "解：有序：$A_5^3=5\\times 4\\times 3=60$；无序：$C_5^3=\\frac{60}{3!}=10$\n\n"
            "**📝 例题2**：掷两枚骰子，点数之和为7的概率是多少？\n"
            "解：总结果 $6\\times6=36$ 种；和为7：(1,6)(2,5)(3,4)(4,3)(5,2)(6,1) 共6种\n"
            "$P=\\frac{6}{36}=\\frac{1}{6}$"
        )

    # ===== 高中数学·不等式 =====
    if "不等式" in s or "均值不等式" in s or "基本不等式" in s:
        return (
            f"【{s}】\n\n"
            "**基本不等式（均值不等式）**：\n"
            "$a+b \\geq 2\\sqrt{ab}$（当且仅当 $a=b$ 时取等号，$a,b>0$）\n\n"
            "**变形形式**：\n"
            "$\\frac{a+b}{2} \\geq \\sqrt{ab}$（算术平均≥几何平均）\n"
            "$ab \\leq (\\frac{a+b}{2})^2$（定和求积最大/定积求和最小）\n\n"
            "**📝 例题**：若 $x>0$，则 $x+\\frac{4}{x}$ 的最小值是？何时取得？\n"
            "解：由均值不等式 $x+\\frac{4}{x} \\geq 2\\sqrt{x\\cdot\\frac{4}{x}}=4$\n"
            "当且仅当 $x=\\frac{4}{x}$ 即 $x=2$ 时取最小值4"
        )

    # 最终兜底（理论上高中数学覆盖后极少走到这里）
    return (
        f"{open_line}\n\n"
        f"**{sub}** 是「{t}」的重要组成部分。\n\n"
        f"**学习建议**：\n"
        f"1. 理清基本概念和定义\n"
        f"2. 掌握核心公式和方法\n"
        f"3. 做典型例题加深理解\n"
        f"4. 总结易错点避免踩坑\n"
        f"5. 及时练习巩固提升"
    )


def _gen_multi_subject_content(topic_title, sub, subject):
    """为非数学学科生成针对每个子知识点的详细讲解内容（全学科智能引擎）。
    根据子知识点名称自动识别概念类型，生成含定义、关键概念、例题的差异化内容。
    覆盖：生物、物理、化学、科学(小学)、语文、英语、历史、地理、政治等。
    """
    s, t, subj = sub, topic_title, subject
    ls = s.lower()

    # ==================== 生物 ====================
    if subject == "生物":
        return _gen_bio_content(t, s)

    # ==================== 物理 ====================
    if subject == "物理":
        return _gen_physics_content(t, s)

    # ==================== 化学 ====================
    if subject == "化学":
        return _gen_chem_content(t, s)

    # ==================== 科学（小学）====================
    if subject == "科学":
        return _gen_science_content(t, s)

    # ==================== 语文 ====================
    if subject == "语文":
        return _gen_chinese_content(t, s)

    # ==================== 英语 ====================
    if subject == "英语":
        return _gen_english_content(t, s)

    # ==================== 历史 ====================
    if subject == "历史":
        return _gen_history_content(t, s)

    # ==================== 地理 ====================
    if subject == "地理":
        return _gen_geography_content(t, s)

    # ==================== 政治/道德与法治 ====================
    if subject in ("道德与法治", "思想政治"):
        open_line = _SUBJECT_OPEN.get(subject, "")
        return (
            f"{open_line}\n\n"
            f"**{s}**（来自「{t}」）的学习要点：\n\n"
            f"1. **是什么**：「{s}」的核心含义与基本要求是什么？\n"
            f"2. **为什么**：它要解决什么问题、有什么意义和价值？\n"
            f"3. **怎么做**：在生活和行动中我们应如何践行？\n\n"
            f"建议结合身边的生活实例与社会新闻来理解这些规则和观念，\n"
            f"思考它们如何指导我们的日常行为与选择。"
        )

    # ==================== 数学（含高中）====================
    if subject == "数学":
        return _gen_math_content(t, s)

    # 最终兜底
    open_line = _SUBJECT_OPEN.get(subject, "学习这部分，先理解再练习最重要。")
    return (
        f"{open_line}\n\n"
        f"【{s}】\n\n"
        f"这是「{t}」中的重要内容。学习时建议：\n"
        f"1. 先理解 {s} 的基本定义和核心概念\n"
        f"2. 结合课本中的例子和图示加深理解\n"
        f"3. 通过练习检验是否真正掌握\n"
        f"4. 注意与已学知识的联系和区别"
    )


def _gen_math_content(t, s, open_line="", subject="数学"):
    """数学学科智能内容引擎——覆盖小学/初中/高中全学段。
    为每个子知识点生成：定义+核心公式+具体例题(带完整步骤)。
    """
    ls = s.lower()
    # ---- 高中·圆锥曲线 ----
    if "椭圆" in s:
        return (
            f"【{s}——平面内到两定点距离之和为常数的点的轨迹】\n\n"
            f"**定义**：平面内与两个定点 F₁、F₂ 的距离之和等于常数（大于 |F₁F₂|）的点的集合。\n"
            f"这「两个定点」叫**焦点**，两焦点间距离叫**焦距 2c**；「距离之和」叫**长轴长 2a**。\n\n"
            f"**标准方程**（中心在原点）：\n"
            f"• 焦点在 x 轴上：x²/a² + y²/b² = 1 （a > b > 0）\n"
            f"• 焦点在 y 轴上：y²/a² + x²/b² = 1 （a > b > 0）\n\n"
            f"**核心关系**（必须牢记）：a² = b² + c²\n"
            f"其中 c = √(a² − b²) 是半焦距，离心率 e = c/a < 1。\n\n"
            f"💡 **生活类比**：拿一根细绳两端固定在图板上（两个焦点），用铅笔绷紧绳子画一圈——画出来的就是椭圆。绳子的总长度就是 2a！\n\n"
            f"📐 **例题**：已知椭圆 x²/25 + y²/16 = 1，求它的长轴、短轴、焦点坐标和离心率。\n"
            f"解：① a²=25 → a=5，长轴2a=10；② b²=16 → b=4，短轴2b=8\n"
            f"③ c²=a²−b²=25−16=9 → c=3；④ 焦点在x轴：(±3, 0)；⑤ e=c/a=3/5=0.6"
        )
    if "双曲线" in s:
        return (
            f"【{s}——平面内到两定点距离之差的绝对值为常数的点的轨迹】\n\n"
            f"**定义**：|PF₁ − PF₂| = 2a（常数，小于 |F₁F₂|）。注意是「差的绝对值」不是「和」！\n\n"
            f"**标准方程**：\n"
            f"• 焦点在 x 轴上：x²/a² − y²/b² = 1\n"
            f"• 焦点在 y 轴上：y²/a² − x²/b² = 1\n\n"
            f"**核心关系**（和椭圆不同！）：c² = a² + b²  （c 最大！）\n"
            f"离心率 e = c/a > 1。\n\n"
            f"⚠️ 椭圆是 a²=b²+c²（a最大），双曲线是 c²=a²+b²（c最大），千万别记混！\n\n"
            f"**渐近线**（双曲线独有）：过中心的两条直线 y = ±(b/a)x（焦点在x轴时），双曲线无限靠近但永远不碰到它们。\n\n"
            f"📐 **例题**：双曲线 x²/9 − y²/4 = 1，求渐近线方程、焦点坐标和离心率。\n"
            f"解：① a=3,b=2 → 渐近线 y = ±(2/3)x；② c²=a²+b²=9+4=13 → c=√13；\n"
            f"③ 焦点(±√13, 0)；④ e=c/a=√13/3 ≈ 1.20"
        )
    if "抛物线" in s:
        return (
            f"【{s}——到定点和定直线距离相等的点的轨迹】\n\n"
            f"**定义**：点到焦点 F 的距离 = 点到准线 l 的距离。只有一个焦点、一条准线。\n\n"
            f"**四种标准方程**（顶点都在原点）：\n"
            f"• y² = 2px（p>0）→ 开口向右，焦点(p/2, 0)，准线 x = −p/2\n"
            f"• y² = −2px（p>0）→ 开口向左，焦点(−p/2, 0)，准线 x = p/2\n"
            f"• x² = 2py（p>0）→ 开口向上，焦点(0, p/2)，准线 y = −p/2\n"
            f"• x² = −2py（p>0）→ 开口向下，焦点(0, −p/2)，准线 y = p/2\n\n"
            f"**记忆技巧**：一次项是谁，谁就是开口方向；p 是焦点到顶点距离的 **2 倍**。\n\n"
            f"📐 **例题**：求抛物线 y² = 8x 的焦点坐标、准线方程和开口方向。\n"
            f"解：① 2p=8 → p=4 → 开口向右（y的一次项）；② 焦点(p/2,0)=(2,0)；\n"
            f"③ 准线 x = −p/2 = −2"
        )
    if "离心率" in s and ("曲线" in t or "圆锥" in t):
        return (
            f"【{s}——描述圆锥曲线「扁」或「开」的程度】\n\n"
            f"**定义**：e = c/a（椭圆/双曲线都用这个公式）\n"
            f"• 椭圆：0 < e < 1，e 越接近 0 越圆，e 越接近 1 越扁\n"
            f"• 双曲线：e > 1，e 越大「开口」越大\n"
            f"• 抛物线：e = 1（特殊情况，定义方式不同）\n\n"
            f"**统一理解**：e 衡量的是「偏离圆形的程度」——圆(e≈0) → 椭圆(0<e<1) → 抛物线(e=1) → 双曲线(e>1)\n\n"
            f"📐 **例题**：椭圆离心率为 0.6，短半轴 b=4，求长半轴 a 和焦距 c。\n"
            f"解：由 e=c/a=0.6 得 c=0.6a；代入 a²=b²+c² → a²=16+(0.6a)²=16+0.36a²\n"
            f"→ 0.64a²=16 → a²=25 → a=5；c=0.6×5=3"
        )
    if "标准方程" in s and ("曲线" in t or "圆锥" in t):
        return (
            f"【圆锥曲线的标准方程汇总】\n\n"
            f"| 曲线   | 标准方程（焦点在x轴）     | a,b,c 关系    | 离心率范围 |\n"
            f"|--------|--------------------------|---------------|------------|\n"
            f"| 椭圆   | x²/a²+y²/b²=1            | a²=b²+c²      | 0<e<1      |\n"
            f"| 双曲线 | x²/a²−y²/b²=1            | c²=a²+b²      | e>1        |\n"
            f"| 抛物线 | y²=2px                   | —             | e=1        |\n\n"
            f"**判断方法**：看方程里 x² 和 y² 的符号——同号是椭圆，异号是双曲线，只有一项平方是抛物线。\n\n"
            f"📐 **例题**：判断 4x²+9y²=36 是什么曲线，并化为标准形式。\n"
            f"解：两边÷36 → x²/9+y²/4=1 → x²和y²**同号**且系数为正 → **椭圆**\n"
            f"a=3, b=2, c=√(9−4)=√5, e=√5/3"
        )

    # ---- 高中·函数 ----
    if "函数" in s and ("单调" in s or "奇偶" in s or "性质" in s):
        return (
            f"【{s}】\n\n"
            f"**单调性**：在区间 I 上，若 x₁<x₂ 时总有 f(x₁)<f(x₂) → **增函数**；若 f(x₁)>f(x₂) → **减函数**。\n"
            f"判断方法：取任意 x₁,x₂∈I，作差 f(x₁)−f(x₂) 或作商 f(x₁)/f(x₂)（正值时），看符号。\n\n"
            f"**奇偶性**：定义域关于原点对称是前提条件！\n"
            f"• 奇函数：f(−x) = −f(x)（图像关于**原点对称**）\n"
            f"• 偶函数：f(−x) = f(x)（图像关于**y轴对称**）\n\n"
            f"📐 **例题**：判断 f(x)=x³+x 的奇偶性和单调性。\n"
            f"解：① 定义域 R 关于原点对称 ✓\n"
            f"② f(−x)=(−x)³+(−x)=−x³−x=−(x³+x)=−f(x) → **奇函数**\n"
            f"③ f'(x)=3x²+1 > 0 恒成立 → 在 (−∞,+∞) 上**严格递增**"
        )
    if "指数" in s or "对数" in s:
        return (
            f"【{s}】\n\n"
            f"**指数函数** y=aˣ（a>0 且 a≠1）：\n"
            f"• a>1 时：过(0,1)，在 R 上**递增**\n"
            f"• 0<a<1 时：过(0,1)，在 R 上**递减**\n\n"
            f"**对数函数** y=logₐx（a>0 且 a≠1）：指数函数的反函数！\n"
            f"• 定义域 x>0（真数必须大于0！）\n"
            f"• 过(1, 0)；a>1 递增，0<a<1 递减\n\n"
            f"**核心公式**：aˡᵒᵍᵃᴺ = N  和  logₐ(aᵇ) = b  （互为逆运算）\n\n"
            f"📐 **例题**：计算 log₂8 + log₃27。\n"
            f"解：log₂8 = log₂(2³) = 3；log₃27 = log₃(3³) = 3；答案 = 3+3 = **6**"
        )

    # ---- 高中·三角函数 ----
    if "三角" in s or ("正弦" in s and "余弦" in s):
        return (
            f"【{s}】\n\n"
            f"**定义（单位圆法）**：设角 α 终边上一点 P(x,y)，r=√(x²+y²)：\n"
            f"• sinα = y/r  • cosα = x/r  • tanα = y/x（x≠0）\n\n"
            f"**基本关系**（必须背熟）：sin²α + cos²α = 1；tanα = sinα/cosα\n\n"
            f"**诱导公式口诀**：「奇变偶不变，符号看象限」\n"
            f"• 奇(π/2±α)：变名（sin↔cos）；偶(kπ±α)：不变名\n"
            f"• 符号看原角所在象限\n\n"
            f"**二倍角公式**：sin2α=2sinαcosα；cos2α=cos²α−sin²α=2cos²α−1=1−2sin²α\n\n"
            f"📐 **例题**：已知 sinα = 3/5，α 在第二象限，求 cosα 和 tanα。\n"
            f"解：cos²α=1−sin²α=1−9/25=16/25 → cosα=−4/5（第二象限cos为负）\n"
            f"tanα=sinα/cosα=(3/5)/(−4/5)=−3/4"
        )
    if "正弦定理" in s or "余弦定理" in s:
        return (
            f"【{s}】\n\n"
            f"**正弦定理**：a/sinA = b/sinB = c/sinC = 2R（R 为外接圆半径）\n"
            f"适用：知两角一边(AAS/ASA)、两边及对角之一(SSA，需讨论)\n\n"
            f"**余弦定理**：a² = b² + c² − 2bc·cosA\n"
            f"变形：cosA = (b²+c²−a²)/(2bc)\n"
            f"适用：三边(SSS)、两边夹角(SAS)\n\n"
            f"📐 **例题**：△ABC 中，a=7, b=10, cosC=1/2，求边 c。\n"
            f"解：c²=a²+b²−2ab·cosC=49+100−2×7×10×(1/2)=149−70=79\n"
            f"c=√79 ≈ 8.89"
        )

    # ---- 高中·数列 ----
    if "等差" in s:
        return (
            f"【等差数列】相邻两项的差等于同一个常数 d。\n\n"
            f"**通项公式**：aₙ = a₁ + (n−1)d\n\n"
            f"**前 n 项和**：Sₙ = n(a₁+aₙ)/2 = na₁ + n(n−1)d/2\n\n"
            f"**性质**：m+n=p+q 时，aₘ+aₙ=aₚ+aq（下标和相等则项的和相等）\n\n"
            f"📐 **例题**：等差数列 {{aₙ}} 中，a₁=2, d=3，求 a₁₀ 和 S₁₀。\n"
            f"解：a₁₀=2+(10−1)×3=2+27=29；S₁₀=10×(2+29)/2=10×31/2=**155**"
        )
    if "等比" in s:
        return (
            f"【等比数列】相邻两项的比值等于同一个常数 q（q≠0）。\n\n"
            f"**通项公式**：aₙ = a₁ · qⁿ⁻¹\n\n"
            f"**前 n 项和**：Sₙ = a₁(1−qⁿ)/(1−q) （q≠1）；当 q=1 时 Sₙ = na₁\n\n"
            f"📐 **例题**：等比数列 {{aₙ}} 中，a₁=3, q=2，求 a₅ 和 S₅。\n"
            f"解：a₅=3×2⁴=3×16=48；S₅=3×(1−32)/(1−2)=3×(−31)/(−1)=**93**"
        )

    # ---- 高中·向量 ----
    if "向量" in s:
        return (
            f"【平面向量】既有大小又有方向的量。\n\n"
            f"**基本运算**（设 **a**=(x₁,y₁), **b**=(x₂,y₂)）：\n"
            f"• 加法：**a**+**b**=(x₁+x₂, y₁+y₂)（三角形法则/平行四边形法则）\n"
            f"• 数乘：k**a**=(kx₁, ky₁)\n"
            f"• 数量积（点积）：**a**·**b**=x₁x₂+y₁y₂=|**a**||**b**|cosθ\n\n"
            f"**重要应用**：\n"
            f"• 模：|**a**|=√(x²+y²)\n"
            f"• 两向量垂直 ⇔ **a**·**b**=0\n"
            f"• 两向量平行（共线） ⇔ x₁y₂−x₂y₁=0\n\n"
            f"📐 **例题**：已知 **a**=(3,4), **b**=(−1,2)，求 **a**·**b**、|**a**| 和夹角 θ。\n"
            f"解：**a**·**b**=3×(−1)+4×2=5；|**a**|=√(9+16)=5；|**b**|=√(1+4)=√5\n"
            f"cosθ=5/(5×√5)=1/√5≈0.447 → θ≈63.4°"
        )

    # ---- 高中·立体几何 ----
    if "立体" in s or "空间" in s:
        return (
            f"【空间中的位置关系】\n\n"
            f"**线面平行判定**：平面外一条直线与此平面内的一条直线平行，则该直线与此平面平行。\n"
            f"**线面垂直判定**：一条直线与一个平面内的两条相交直线都垂直，则该直线与此平面垂直。\n\n"
            f"**三垂线定理**：平面内的一条直线如果与斜线在这个平面内的射影垂直，则它也和这条斜线垂直。\n\n"
            f"**常用体积/面积公式**：\n"
            f"• 长方体：V=abc；球：V=4πr³/3，S=4πr²\n"
            f"• 锥体：V=底面积×高/3；柱体：V=底面积×高\n\n"
            f"📐 **例题**：正方体 ABCD-A'B'C'D' 棱长为 2，求 A'C' 与平面 ABCD 所成角的正弦值。\n"
            f"解：建立坐标系：A(0,0,0), B(2,0,0), C(2,2,0), D(0,2,0), A'(0,0,2), C'(2,2,2)\n"
            f"A'C' 向量=(2,2,0)，平面 ABCD 法向量 **n**=(0,0,1)\n"
            f"sinθ=|**n**·**A'C'**|/(|**n**||**A'C'**|)=0/(1×√8)=0 → 实际所成角为 0°（因为 A'C' ∥ 平面ABCD）"
        )

    # ---- 高中·导数 ----
    if "导" in s:
        return (
            f"【导数——研究函数变化率的工具】\n\n"
            f"**定义**：f'(x₀) = lim[Δx→0] [f(x₀+Δx)−f(x₀)]/Δx\n\n"
            f"**基本求导公式**（必须熟练）：\n"
            f"• C' = 0  • (xⁿ)' = nxⁿ⁻¹  • (eˣ)' = eˣ  • (ln x)' = 1/x\n"
            f"• (sin x)' = cos x  • (cos x)' = −sin x  • (aˣ)' = aˣ ln a\n\n"
            f"**导数的意义**：\n"
            f"f'(x) > 0 → f(x) **递增**；f'(x) < 0 → f(x) **递减**\n"
            f"f'(x) = 0 且变号 → **极值点**（正→负极大，负→正极小）\n\n"
            f"📐 **例题**：求 f(x)=x³−3x²+1 的单调区间和极值。\n"
            f"解：f'(x)=3x²−6x=3x(x−2)\n"
            f"令 f'(x)=0 → x=0 或 x=2\n"
            f"x<0: f'>0 递增；(0,2): f'<0 递减；x>2: f'>0 递增\n"
            f"极大值 f(0)=1；极小值 f(2)=8−12+1=−3"
        )

    # ---- 高中·概率统计 ----
    if "概率" in s:
        return (
            f"【概率——事件发生可能性的度量】\n\n"
            f"**古典概型**：P(A) = 有利结果数 / 总结果数（等可能事件）\n"
            f"**互斥事件**：P(A∪B) = P(A)+P(B)（不能同时发生的事件）\n"
            f"**独立事件**：P(AB) = P(A)×P(B)（互相不影响的事件）\n\n"
            f"**条件概率**：P(B|A) = P(AB)/P(A)（在 A 发生的条件下 B 发生的概率）\n\n"
            f"📐 **例题**：袋中有 3 红 2 白共 5 个球，不放回地取 2 个，求恰好 1 红 1 白的概率。\n"
            f"解：总取法 C(5,2)=10 种；恰 1红1白 = 取1红(C(3,1))×取1白(C(2,1))=3×2=6 种\n"
            f"P = 6/10 = **3/5 = 0.6**"
        )
    if "统计" in s:
        return (
            f"【统计——从数据中提取信息】\n\n"
            f"**平均数**：x̄ = (x₁+x₂+…+xₙ)/n\n"
            f"**方差**：s² = [(x₁−x̄)²+(x₂−x̄)²+…+(xₙ−x̄)²]/n（衡量数据离散程度）\n"
            f"**标准差**：s = √s²（与数据同单位，更直观）\n\n"
            f"**中位数**：排序后中间的数（偶数个取中间两数的平均）\n"
            f"**众数**：出现次数最多的数\n\n"
            f"📐 **例题**：数据 2, 4, 4, 5, 7, 9，求平均数、方差和中位数。\n"
            f"解：x̄=(2+4+4+5+7+9)/6=31/6≈5.17\n"
            f"s²=[(−3.17)²+(−1.17)²+(−1.17)²+(−0.17)²+(1.83)²+(3.83)²]/6≈4.47\n"
            f"中位数=(4+5)/2=**4.5**"
        )

    # ---- 初中·一元二次方程 ----
    if "二次" in s and "方程" in s:
        return (
            f"【一元二次方程 ax²+bx+c=0（a≠0）】\n\n"
            f"**求根公式**（万能工具）：x = [−b±√(b²−4ac)] / (2a)\n\n"
            f"**判别式 Δ = b²−4ac** 决定根的情况：\n"
            f"• Δ > 0 → 两个不等实根  • Δ = 0 → 两个相等实根  • Δ < 0 → 无实根\n\n"
            f"**韦达定理**（根与系数的关系）：x₁+x₂ = −b/a, x₁·x₂ = c/a\n\n"
            f"📐 **例题**：解方程 2x²−5x+2=0。\n"
            f"解：a=2,b=−5,c=2；Δ=(−5)²−4×2×2=25−16=9>0（两不等实根）\n"
            f"x=[5±√9]/(2×2)=[5±3]/4 → x₁=(5+3)/4=**2**, x₂=(5−3)/4=**1/2**"
        )

    # ---- 初中·勾股定理 ----
    if "勾股定理" in s and "逆" not in s:
        return (
            f"【勾股定理——直角三角形三边的数量关系】\n\n"
            f"**文字表述**：直角三角形两条直角边的平方和，等于斜边的平方。\n\n"
            f"**公式**（核心，必须牢记）：\n"
            f"若直角三角形两直角边为 a、b，斜边为 c，则 **a² + b² = c²**。\n\n"
            f"**几何意义**：以两条直角边为边长的两个小正方形面积之和，正好等于以斜边为边长的大正方形面积。\n\n"
            f"**什么时候用？**\n"
            f"• 已知直角三角形两边，求第三边；\n"
            f"• 已知三角形三边，判断它是不是直角三角形（结合逆定理）；\n"
            f"• 求平面/立体图形中的长度、距离。\n\n"
            f"⚠️ **易错点**：一定要先确认哪个角是直角，直角所对的边才是斜边 c；别把直角边和斜边搞反。\n\n"
            f"📐 **例题**：直角三角形的两条直角边分别为 6 cm 和 8 cm，求斜边。\n"
            f"解：由勾股定理 a² + b² = c²，得 c² = 6² + 8² = 36 + 64 = 100，所以 c = √100 = **10 cm**。"
        )
    if "逆定理" in s:
        return (
            f"【勾股定理的逆定理——判断直角三角形】\n\n"
            f"**文字表述**：如果一个三角形的三边 a、b、c 满足 **a² + b² = c²**，那么这个三角形是直角三角形，且边 c 所对的角是直角。\n\n"
            f"**与勾股定理的区别**：\n"
            f"• 勾股定理：已知是直角三角形 → 得 a²+b²=c²\n"
            f"• 逆定理：已知 a²+b²=c² → 判断它是直角三角形\n"
            f"一句话：**勾股定理是「性质」，逆定理是「判定」**。\n\n"
            f"**判断步骤**：\n"
            f"1. 找出最长边 c；2. 计算 a²+b² 和 c²；3. 若相等 → 直角三角形；若不等 → 不是。\n\n"
            f"📐 **例题**：判断三边长为 9、12、15 的三角形是否为直角三角形。\n"
            f"解：最长边为 15。计算 9² + 12² = 81 + 144 = 225，15² = 225。\n"
            f"因为 9² + 12² = 15²，所以该三角形是直角三角形，直角对着边 15。"
        )
    if "勾股数" in s:
        return (
            f"【勾股数——能构成直角三角形三边的正整数】\n\n"
            f"**定义**：满足 **a² + b² = c²** 的三个正整数 (a, b, c)，叫做一组勾股数。\n"
            f"其中 a、b 是直角边，c 是斜边。\n\n"
            f"**常见勾股数（必须熟悉）**：\n"
            f"• 3、4、5（最基础）\n"
            f"• 5、12、13\n"
            f"• 8、15、17\n"
            f"• 7、24、25\n"
            f"• 9、40、41\n\n"
            f"**重要性质**：\n"
            f"• 任意勾股数同时乘以一个正整数 k，得到的 (ka, kb, kc) 仍是勾股数。\n"
            f"  例如 3、4、5 同乘 2 得 6、8、10，也是勾股数。\n"
            f"• 勾股数一定是正整数，像 1、√3、2 虽满足 1²+(√3)²=2²，但不是勾股数。\n\n"
            f"📐 **例题**：下列哪组是勾股数？A. 2、3、4  B. 6、8、10  C. 5、5、5\n"
            f"解：A. 2²+3²=13 ≠ 4²=16，不是；B. 6²+8²=36+64=100=10²，是；C. 5²+5²=50 ≠ 5²=25，不是。\n"
            f"答案选 **B**。"
        )
    if ("距离" in s or "最短" in s) and ("勾股" in t or "直角" in t or "平面" in t):
        return (
            f"【用勾股定理求距离】\n\n"
            f"**基本思想**：把要求的线段放到一个直角三角形中，让它成为直角边或斜边，再用 a²+b²=c² 计算。\n\n"
            f"**常见模型**：\n"
            f"• 数轴上两点距离：|a − b|；\n"
            f"• 平面上两点距离：构造水平、竖直直角边，斜边即为所求；\n"
            f"• 立体图形表面最短路径：把立体图形展开成平面，化曲为直后用勾股定理。\n\n"
            f"📐 **例题**：在边长为 4 的正方体中，求从顶点 A 到相对顶点 B 沿表面爬行的最短距离。\n"
            f"解：把正方体一个侧面展开，A 到 B 的水平距离为 4+4=8，竖直距离为 4。\n"
            f"最短距离 = √(8² + 4²) = √(64+16) = √80 = **4√5 ≈ 8.94**。"
        )
    if "应用" in s and ("勾股" in t or "直角" in t):
        return (
            f"【勾股定理的实际应用】\n\n"
            f"**解题套路**：\n"
            f"1. 把实际问题画成几何图形，标出已知长度和要求的量；\n"
            f"2. 找到或构造直角三角形；\n"
            f"3. 设未知数，用 a² + b² = c² 列方程；\n"
            f"4. 解方程并检验答案是否符合实际意义。\n\n"
            f"**常见场景**：梯子靠墙、芦苇出水、船距灯塔、矩形对角线、斜坡长度等。\n\n"
            f"📐 **例题**：一根 5 米长的梯子斜靠在墙上，梯脚离墙 3 米，求梯子上端离地面多高？\n"
            f"解：梯子、墙、地面构成直角三角形，梯子为斜边 c=5，梯脚到墙的距离 a=3。\n"
            f"设上端离地面 b 米，由 a²+b²=c² 得 3²+b²=5² → b²=25−9=16 → b=**4 米**。"
        )

    # ---- 小学/初中通用数学兜底 ----
    if "圆" in s and "认" in s:
        return (
            f"【{s}】\n\n"
            f"**圆的定义**：平面上到一个定点（圆心）的距离等于定长（半径）的所有点组成的图形。\n\n"
            f"**关键公式**：\n"
            f"周长 C = 2πr = πd；面积 S = πr²（r 半径, d 直径, d=2r）\n\n"
            f"📐 **例题**：一个圆形花坛半径 3 米，求周长和面积（π取3.14）。\n"
            f"解：周长 = 2×3.14×3 = **18.84 米**；面积 = 3.14×3² = 3.14×9 = **28.26 平方米**"
        )
    if "分数" in s:
        return (
            f"【{s}】\n\n"
            f"分数表示整体的一部分。分母表示分成几份，分子表示取了几份。\n\n"
            f"**基本运算**：\n"
            f"• 加减：先通分（找最小公倍数），再加减分子\n"
            f"• 乘法：分子×分子，分母×分母\n"
            f"• 除法：乘以倒数（颠倒分子分母后相乘）\n\n"
            f"📐 **例题**：计算 2/3 + 1/4。\n"
            f"解：通分，最小公倍数为 12 → 2/3=8/12, 1/4=3/12\n"
            f"8/12 + 3/12 = **11/12**"
        )
    if "比例" in s or "百分" in s:
        return (
            f"【{s}】\n\n"
            f"**百分数**：分母为100的特殊分数，用%表示。如 25%=25/100=1/4=0.25\n\n"
            f"**比例**：两个比相等的式子 a:b = c:d；内项积=外项积 → ad=bc\n\n"
            f"📐 **例题**：一件衣服原价200元，打八折出售，现价多少？\n"
            f"解：八折 = 80% = 0.8；现价 = 200 × 0.8 = **160 元**"
        )

    # 数学最终兜底——至少给出学习框架
    return (
        f"【{s}——「{t}」的核心知识】\n\n"
        f"学习 {s} 需要掌握以下要点：\n\n"
        f"1. **理解基本概念**：弄清 {s} 的定义、几何直观和物理含义\n"
        f"2. **记住核心公式**：相关公式不仅要会背，还要知道怎么推导、什么时候用\n"
        f"3. **做典型例题**：每种题型做 3~5 道，总结解题规律\n"
        f"4. **注意易错点**：常见错误包括公式记混、计算粗心、忽略隐含条件等\n\n"
        f"建议配合课本例题和课后习题同步练习，有疑问随时问老师。"
    )


def _gen_bio_content(t, s):
    """生物学科智能内容引擎"""
    # ---- 七年级·绿色植物 ----
    if "藻类" in s or "苔藓" in s or "蕨类" in s:
        return (
            f"【{s}——孢子植物】\n\n"
            f"这三类植物都不产生**种子**，靠**孢子**繁殖，属于**孢子植物**。\n\n"
            f"**藻类植物**（如海带、紫菜）：\n"
            f"- 结构最简单，没有**根、茎、叶**的分化\n"
            f"- 多生活在**水中**\n"
            f"- 作用：大气中 **90% 的氧气**来自藻类的光合作用！\n\n"
            f"**苔藓植物**（如葫芦藓）：\n"
            f"- 有茎和叶的分化，但**没有真正的根**（只有假根，起固定作用）\n"
            f"- 植株矮小（输导组织不发达）\n"
            f"- 监测**空气污染程度的指示植物**（对SO₂敏感）\n\n"
            f"**蕨类植物**（如肾蕨、满江红）：\n"
            f"- 有**根、茎、叶**的分化，体内有**输导组织**\n"
            f"- 长得比苔藓高大\n"
            f"- 古代蕨类埋藏地下→**煤**\n\n"
            f"💡 进化趋势：藻类 → 苔藓 → 蕨类（结构越来越复杂）"
        )
    if "种子植物" in s:
        return (
            f"【{s}——用种子繁殖的植物】\n\n"
            f"种子植物包括两大类：\n\n"
            f"**① 裸子植物**（如松、柏、杉、银杏）：\n"
            f"- 种子**裸露**，无果皮包被\n"
            f"- 根、茎、叶发达，输导组织完善\n"
            f"- 适应干旱和贫瘠环境\n\n"
            f"**② 被子植物**（如苹果、大豆、玉米）：\n"
            f"- 种子外有**果皮包被**，形成**果实**\n"
            f"- 地球上**种类最多、分布最广**的植物\n"
            f"- 有花（被子植物又名**开花植物/有花植物**）\n\n"
            f"⚠️ 松果不是果实（裸子植物无果皮包被）！\n\n"
            f"**种子的基本结构**：种皮 + 胚（子叶、胚芽、胚轴、胚根），胚是新植株的幼体。"
        )
    if "蒸腾作用" in s:
        return (
            f"【{s}——水分从植物体表散失】\n\n"
            f"**定义**：水分从活的植物体表面（主要是**叶片**）以**水蒸气**形式散失到大气中的过程。\n\n"
            f"**主要器官**：叶——具体是通过**气孔**散失的。\n"
            f"气孔由一对**保卫细胞**围成，是蒸腾作用的「门户」。\n\n"
            f"**蒸腾作用的意义**：\n"
            f"1. **拉动水分和无机盐向上运输**的「泵」（根吸水的动力）\n"
            f"2. **降低叶片温度**，防止强光灼伤\n"
            f"3. 提高大气湿度，增加降水\n\n"
            f"💡 一株玉米一生中通过蒸腾作用散失的水超过 **200 kg**！"
        )
    if "光合作用" in s:
        return (
            f"【{s}——绿色植物制造有机物】\n\n"
            f"**定义**：绿色植物通过**叶绿体**，利用**光能**，把二氧化碳和水转化成储存能量的**有机物**（主要是淀粉），并释放出**氧气**的过程。\n\n"
            f"**反应式**：\n"
            f"二氧化碳 + 水 --[叶绿体/光能]--> 有机物(储存能量) + 氧气\n\n"
            f"**场所**：叶绿体（主要在叶肉细胞中）\n\n"
            f"**原料**：CO₂（从气孔进入）+ H₂O（由根吸收经导管运输）\n\n"
            f"**产物**：有机物（淀粉等，储存在细胞中）+ O₂（释放到大气）\n\n"
            f"**条件**：**光**（能量来源）+ **叶绿体**（反应场所）\n\n"
            f"**意义**：\n"
            f"1. 制造有机物（食物链的基础，所有生物的能量源头）\n"
            f"2. 转化和储存光能\n"
            f"3. 维持大气中**碳—氧平衡**（吸收CO₂释放O₂）\n\n"
            f"⚠️ 光合作用只在**有光**时进行；呼吸作用**时刻进行**。"
        )
    if "呼吸作用" in s:
        return (
            f"【{s}——分解有机物释放能量】\n\n"
            f"**定义**：活细胞利用氧，将有机物分解成**二氧化碳和水**，同时将储存在有机物中的**能量释放出来**，供给生命活动需要的过程。\n\n"
            f"**反应式**：\n"
            f"有机物(储存能量) + 氧气 → 二氧化碳 + 水 + 能量\n\n"
            f"**场所**：线粒体（所有活细胞的「动力车间」）\n\n"
            f"**实质**：**分解有机物，释放能量**\n\n"
            f"⚠️ 呼吸作用 vs 光合作用的区别：\n\n"
            f"| | 呼吸作用 | 光合作用 |\n"
            f"|---|---|---|\n"
            f"| 条件 | 有光无光都行 | 必须有光 |\n"
            f"| 场所 | 线粒体 | 叶绿体 |\n"
            f"| 物质变化 | 有机物→CO₂+H₂O | CO₂+H₂O→有机物 |\n"
            f"| 能量变化 | 释放能量 | 储存能量 |\n"
            f"| 关系 | 互相**对立统一**，共同维持生物圈碳-氧平衡 | |\n\n"
            f"💡 应用：中耕松土（增加根部氧气促进呼吸）、低温储存果蔬（降低呼吸减少消耗）、合理灌溉。"
        )
    if "细胞" in s:
        return (
            f"【{s}——生命的基本单位】\n\n"
            f"**细胞是生物体结构和功能的基本单位**（除病毒外）。\n\n"
            f"**动物细胞基本结构**：\n"
            f"- **细胞膜**：控制物质进出（选择性透过性）\n"
            f"- **细胞质**：代谢的主要场所，含各种细胞器\n"
            f"- **细胞核**：遗传信息库，控制中心\n"
            f"- **线粒体**：呼吸作用场所，「动力车间」\n\n"
            f"**植物细胞特有**（动物细胞没有）：\n"
            f"- **细胞壁**：保护和支持（使植物细胞呈方形）\n"
            f"- **叶绿体**：光合作用场所\n"
            f"- **液泡**：含细胞液（溶解糖类色素等）\n\n"
            f"**细胞分裂**：一个细胞→两个细胞。分裂时**染色体先复制再均分**，保证新细胞遗传物质不变。\n\n"
            f"**细胞生长**：体积由小变大；**细胞分化**：形态功能发生改变，形成不同组织。"
        )
    if "生态系统" in s:
        return (
            f"【{s}】\n\n"
            f"**生态系统的组成**：\n\n"
            f"① **非生物成分**：阳光、空气、水、温度等\n\n"
            f"② **生物成分**：\n"
            f"- **生产者**（绿色植物）：通过光合作用制造有机物\n"
            f"- **消费者**（动物）：直接或间接以植物为食\n"
            f"- **分解者**（细菌、真菌）：分解动植物遗体，促进物质循环\n\n"
            f"**食物链和食物网**：\n"
            f"- 食物链：生产者 → 初级消费者 → 次级消费者…（箭头指向捕食者）\n"
            f"- 营养级越高，积累的有毒物质越多（**生物富集/生物放大**）\n\n"
            f"**自动调节能力**：生态系统有一定自我调节能力，但这种能力是**有限度的**。\n"
            f"超过限度→生态系统遭到破坏（如草原过度放牧→荒漠化）。"
        )
    if "遗传" in s or "变异" in s or "基因" in s:
        return (
            f"【{s}】\n\n"
            f"**基因**是有遗传效应的DNA片段，位于**染色体**上。\n\n"
            f"染色体 = DNA + 蛋白质（存在于细胞核中）\n\n"
            f"在生物体的体细胞中，染色体是**成对存在**的（一条来自父方，一条来自母方）；\n"
            f"生殖细胞（精子/卵细胞）中染色体**减半**（成单存在）。\n\n"
            f"**显性基因**（大写字母A）**隐性基因**（小写字母a）：\n"
            f"- AA 或 Aa → 表现**显性性状**\n"
            f"- aa → 表现**隐性性状**\n\n"
            f"**遗传病**：由遗传物质改变引起（如白化病、色盲、血友病）。\n"
            f"近亲结婚→后代患隐性遗传病的概率大大增加（禁止近亲结婚的原因）。"
        )

    # ---- 高中生物：必修一·分子与细胞 ----
    if any(k in s for k in ("蛋白质","氨基酸","肽键","一级结构")):
        return (
            f"【{s}——生命活动的主要承担者】\n\n"
            f"**基本组成单位：氨基酸**（约20种）\n"
            f"- 结构通式：至少有一个氨基(-NH₂)和一个羧基(-COOH)连在同一个碳原子上\n"
            f"- 区分种类看 **R基（侧链）** 不同\n\n"
            f"**脱水缩合形成肽链**：\n"
            f"- 一个氨基酸的羧基 + 另一个的氨基 → 脱去一分子水 → 形成 **肽键(-CO-NH-)**\n"
            f"- n个氨基酸脱水缩合 → 形成(n-1)个肽键，脱去(n-1)分子水\n\n"
            f"**蛋白质结构层次**：\n"
            f"- 一级：氨基酸序列（决定空间结构的基础）\n"
            f"- 二级：α-螺旋、β-折叠（氢键维持）\n"
            f"- 三级：整条肽链的空间折叠（侧链R基相互作用）\n"
            f"- 四级：多条肽链组装成功能蛋白（如血红蛋白4条链）\n\n"
            f"📐 例题：100个氨基酸形成的肽链中有多少个肽键？答：99个，脱去99分子水。\n"
            f"💡 变性：高温/强酸破坏空间结构，肽键不断裂（不可逆）；水解才断裂肽键。"
        )
    if any(k in s for k in ("核酸","DNA","RNA","核苷酸","碱基")):
        return (
            f"【{s}——遗传信息的携带者】\n\n"
            f"**两类核酸比较**：\n\n"
            f"| | DNA（脱氧核糖核酸）| RNA（核糖核酸）|\n"
            f"|---|---|---|\n"
            f"| 分布 | 主要在细胞核（线粒体/叶绿体也有）| 主要在细胞质 |\n"
            f"| 五碳糖 | 脱氧核糖 | 核糖 |\n"
            f"| 碱基 | A T G C | A U G C |\n"
            f"| 基本单位 | 脱氧核苷酸(4种) | 核糖核苷酸(4种) |\n"
            f"| 结构 | 通常双螺旋 | 通常单链 |\n\n"
            f"**核苷酸 = 五碳糖 + 含氮碱基 + 磷酸**\n\n"
            f"⚠️ T（胸腺嘧啶）是DNA特有的；U（尿嘧啶）是RNA特有的——常考点！\n\n"
            f"💡 记忆口诀：DNA用T不用U，RNA用U不用T。"
        )
    if any(k in s for k in ("酶","活性","专一性","最适温度","最适pH")):
        return (
            f"【{s}——生物催化剂】\n\n"
            f"**本质**：绝大多数是**蛋白质**，少数是**RNA（核酶）**。\n\n"
            f"**特性**：\n"
            f"- **高效性**：催化效率是无机催化剂的10⁷~10¹³倍\n"
            f"- **专一性**：一种酶只能催化一种或一类化学反应（锁钥模型）\n"
            f"- **作用条件较温和**：需要适宜的温度和pH\n\n"
            f"**影响酶活性的因素**：\n"
            f"- 温度：低温抑制（可恢复），高温变性（不可逆）\n"
            f"- pH：过酸过碱都使酶变性失活\n\n"
            f"📐 例题：胃蛋白酶最适pH≈1.5（酸性），进入小肠（pH≈7.6）后失活。唾液淀粉酶最适pH≈6.8，最适温度37℃。\n\n"
            f"💡 实验：用碘液检测淀粉，用斐林试剂检测还原糖。对照实验必须遵循单一变量原则。"
        )
    if s == "ATP":
        return (
            f"【ATP——直接能源物质】\n\n"
            f"**全称**：三磷酸腺苷（Adenosine Triphosphate）\n\n"
            f"**结构简式**：A-P～P～P\n"
            f"- A = 腺苷（腺嘌呤+核糖）\n"
            f"- P = 磷酸基团\n"
            f"- ～= 高能磷酸键（远离A的那个容易断裂释放能量）\n\n"
            f"**ATP与ADP的循环转化**：\n"
            f"ATP ⇌ ADP + Pi + 能量\n"
            f"- 合成（放能反应）：呼吸作用、光合作用\n"
            f"- 水解（吸能反应）：肌肉收缩、主动运输、神经传导等\n\n"
            f"⚠️ ATP在体内含量很少但转化极快——就像「零花钱」，随用随取。\n\n"
            f"💡 人体每天合成/水解约40-70kg当量的ATP，但体内瞬时只有几克。"
        )
    if any(k in s for k in ("细胞膜","流动镶嵌","磷脂双分子层","选择透过性","自由扩散","主动运输")):
        return (
            f"【{s}——系统的边界】\n\n"
            f"**流动镶嵌模型**（辛格&尼科尔森，1972）：\n"
            f"- **磷脂双分子层**：基本支架（头部亲水朝外，尾部疏水朝内）\n"
            f"- **蛋白质**：镶嵌/贯穿/覆盖在磷脂上（有的可移动）\n"
            f"- **糖被**：细胞膜外表面（识别、保护、润滑）\n\n"
            f"**功能**：\n"
            f"1. 将细胞与外界分隔开\n"
            f"2. 控制物质进出（**选择透过性**）\n"
            f"3. 进行细胞间信息交流（糖蛋白识别）\n\n"
            f"**物质跨膜运输方式**：\n\n"
            f"| 方式 | 浓度梯度 | 载体 | 能量 | 例子 |\n"
            f"|---|---|---|---|---|\n"
            f"| 自由扩散 | 高→低 | ✗ | ✗ | O₂、CO₂、水、乙醇 |\n"
            f"| 协助扩散 | 高→低 | ✓ | ✗ | 葡萄糖进红细胞 |\n"
            f"| 主动运输 | 低→高 | ✓ | ✓ | 离子、葡萄糖进小肠上皮细胞 |\n"
            f"| 胞吞/胞吐 | — | — | ✓ | 大分子（蛋白/多糖）|\n\n"
            f"📐 例题：某离子从细胞内浓度0.01到外界浓度0.02，仍能继续吸收→说明是**主动运输**（逆浓度）。"
        )
    if any(k in s for k in ("细胞器","线粒体","叶绿体","核糖体","内质网","高尔基体","液泡","溶酶体")):
        return (
            f"【{s}——细胞内的分工合作】\n\n"
            f"**双层膜细胞器**：\n"
            f"- **线粒体**：有氧呼吸主要场所，「动力车间」→内膜折叠成嵴增大面积\n"
            f"- **叶绿体**：光合作用场所（植物特有）→ 基粒（类囊体堆叠）+ 基质\n\n"
            f"**单层膜细胞器**：\n"
            f"- **内质网**：粗面（附核糖体，分泌蛋白合成加工）+ 滑面（脂质合成）\n"
            f"- **高尔基体**：加工分类包装发送「邮政中心」（动物：分泌物；植物：细胞壁）\n"
            f"- **液泡**：含细胞液（色素/糖类/无机盐），维持渗透压\n"
            f"- **溶酶体**：含水解酶，「消化车间」（分解衰老损伤的细胞器）\n\n"
            f"**无膜细胞器**：\n"
            f"- **核糖体**：「生产蛋白质的机器」→ 无膜，由rRNA+蛋白质组成\n"
            f"- **中心体**：动物和低等植物有→ 与细胞分裂纺锤体形成有关\n\n"
            f"💡 分泌蛋白合成路径：核糖体→内质网→囊泡→高尔基体→囊泡→细胞膜（全程需线粒体供能）"
        )
    if any(k in s for k in ("有丝分裂","间期","前期","中期","后期","末期","染色体","染色单体","着丝点")):
        return (
            f"【{s}——细胞的增殖方式】\n\n"
            f"**细胞周期** = 分裂间期（90%~95%）+ 分裂期(M)（5%~10%）：前中后末\n\n"
            f"**各时期特征**：\n\n"
            f"| 期 | 染色体行为 | 关键记忆 |\n"
            f"|---|---|---|\n"
            f"| 间期 | DNA复制+蛋白质合成（染色体复制） | 「看不见的变化最重要」|\n"
            f"| 前期 | 核膜核仁消失→染色体出现→纺锤体形成 | 「膜仁消失显两体」|\n"
            f"| 中期 | 染色体排列在赤道板上 | 「形定数晰赤道齐」|\n"
            f"| 后期 | 着丝点分裂→姐妹染色单体分开→染色体数目加倍 | 「点裂数加均两极」|\n"
            f"| 末期 | 核膜核仁重建→染色体变细长→纺锤体消失 | \"两消两现重开始\" |\n\n"
            f"**重要数量关系**：\n"
            f"- DNA数 = 染色体数 × 每条染色体DNA数\n"
            f"- 染色单体数 = 0 或 = 2×染色体数（存在时才有）\n"
            f"- 后期特点：着丝点分裂→染色单体变为0，染色体暂时加倍\n\n"
            f"📐 例题：某细胞有4条染色体，间期复制后DNA=8，后期染色体=8（暂时加倍），末期结束=4。"
        )
    if any(k in s for k in ("分化","全能性","干细胞","组织培养","脱分化","再分化")):
        return (
            f"【{s}——细胞 becoming 专业】\n\n"
            f"**概念**：相同细胞的后代在形态、结构和生理功能上发生**稳定性差异**的过程。\n\n"
            f"**本质**：基因的选择性表达（不是基因改变！）\n"
            f"- 所有体细胞含完整的遗传信息（除生殖细胞）\n"
            f"- 不同细胞表达不同基因 → 产生不同蛋白质 → 功能不同\n\n"
            f"**细胞全能性**：已分化的细胞仍然具有发育成完整个体的潜能。\n"
            f"- 全能性高低：受精卵 > 生殖细胞 > 体细胞\n"
            f"- 植物细胞全能性 > 动物细胞（植物更容易通过组织培养再生完整植株）\n\n"
            f"**应用——植物组织培养**：\n"
            f"离体器官/组织/细胞 → **脱分化**→ 愈伤团 → **再分化**→ 根芽 → 完整植株\n"
            f"- 条件：无菌、适宜激素配比、适宜光照（再分化时）\n\n"
            f"💡 干细胞：未分化的细胞，具有自我更新和多向分化潜能（如造血干细胞→各类血细胞）。"
        )
    if any(k in s for k in ("衰老","凋亡","癌变","癌细胞","接触抑制","无限增殖")):
        return (
            f"【{s}——细胞的命运】\n\n"
            f"**细胞衰老特征**：\n"
            f"- 水分减少→萎缩、代谢减慢\n"
            f"- 酶活性降低→呼吸减慢\n"
            f"- 色素积累→老年斑\n"
            f"- 核体积增大、核膜内折\n"
            f"- 染色质固缩\n\n"
            f"**细胞凋亡**（ programmed cell death）：\n"
            f"- 由基因控制的**程序性死亡**（正常生理现象）\n"
            f"- 如：手指形成时指间细胞凋亡、蝌蚪尾部消失\n\n"
            f"**细胞癌变**（关键考点）：\n"
            f"- **原因**：原癌基因激活 + 抑癌基因失活\n"
            f"- **特征**：①无限增殖 ②形态改变 ③表面糖蛋白减少→易转移\n"
            f"- **致癌因子**：物理（紫外线/X射线）、化学（黄曲霉毒素/亚硝胺）、病毒\n\n"
            f"📐 例题：癌细胞易转移的根本原因是**细胞膜表面糖蛋白减少**，细胞间的黏着性降低。"
        )

    # ---- 高中生物：必修二·遗传与进化 ----
    if any(k in s for k in ("减数分裂","同源染色体","四分体","联会","初级精母","次级精母")):
        return (
            f"【{s}——产生生殖细胞的特殊分裂】\n\n"
            f"**核心事件**：染色体复制一次，细胞连续分裂两次 → 配子染色体数减半\n\n"
            f"**精子形成过程**：\n"
            f"精原细胞(2N) --[间期:DNA复制]--> 初级精母细胞(2N)\n"
            f"  --[减Ⅰ:同源分离]--> 次级精母细胞(N) [两个]\n"
            f"  --[减Ⅱ:姐妹分离]--> 精细胞(N) [四个] --> 精子\n\n"
            f"**关键区分**（高考必考）：\n\n"
            f"| | 减数第一次分裂 | 减数第二次分裂 |\n"
            f"|---|---|---|\n"
            f"| 同源染色体？ | ✓ 有 | ✗ 无（已分开）|\n"
            f"| 特殊行为 | 同源联会→四分体→分离 | 着丝点分裂 |\n"
            f"| 染色体数 | 2N→N | N→2N→N |\n"
            f"| DNA数 | 4C→2C | 2C→C |\n"
            f"| 意义 | 同源染色体分离→非同源自由组合 | 姐妹染色单体分开 |\n\n"
            f"⚠️ 四分体 = 1对同源染色体 + 4条染色单体（只出现在减Ⅰ前期）。"
            f"N对染色体 → N个四分体。\n\n"
            f"📐 例题：人的精原细胞46条染色体，减Ⅰ后有23对→减Ⅱ后每个次级精母23条→最终精子各23条。"
        )
    if any(k in s for k in ("DNA结构","双螺旋","碱基互补","沃森","克里克","碱基配对")):
        return (
            f"【{s}——遗传物质的结构】\n\n"
            f"**DNA双螺旋结构**（1953年沃森&克里克）：\n\n"
            f"- **两条反向平行的多核苷酸链**盘旋成双螺旋\n"
            f"- 外侧：**脱氧核糖+磷酸交替连接**构成基本骨架\n"
            f"- 内侧：**碱基对(A-T, G-C)** 通过氢键相连\n\n"
            f"**碱基互补配对原则**：\n"
            f"A（腺嘌呤）= T（胸腺嘧啶）（2个氢键）\n"
            f"G（鸟嘌呤）≡ C（胞嘧啶）（3个氢键）\n\n"
            f"** Chargaff规则**：任何DNA中，A=T，G=C\n"
            f"∴ A+G = T+C = 50%（嘌呤=嘧啶）\n\n"
            f"📐 例题：某DNA片段A占30%→T也30%，G=C=20%。若该片段有1000bp，则A=T=300，G=C=200。\n"
            f"💡 G≡C配对含3个氢键更稳定→GC含量高的DNA耐热性强（如嗜热菌DNA GC含量高）。"
        )
    if any(k in s for k in ("基因表达","转录","翻译","mRNA","tRNA","密码子","反密码子","核糖体")):
        return (
            f"【{s}——从基因到蛋白质】\n\n"
            f"**中心法则**：DNA →(转录)→ RNA →(翻译)→ 蛋白质\n\n"
            f"**转录**（细胞核内进行）：\n"
            f"- 模板：DNA的一条链（模板链）\n"
            f"- 原料：四种核糖核苷酸\n"
            f"- 酶：RNA聚合酶\n"
            f"- 产物：mRNA（信使RNA）+ tRNA + rRNA\n"
            f"- 特点：以碱基互补配对（A-U, T-A, G-C, C-G）\n\n"
            f"**翻译**（核糖体上进行）：\n"
            f"- mRNA上的每3个相邻碱基 = 一个**密码子**（共64种，61个编码AA，3个终止）\n"
            f"- tRNA一端携带**反密码子**（与mRNA配对），另一端携带对应**氨基酸**\n"
            f"- 从起始密码(AUG)开始，到终止密码(UAA/UAG/UGA)停止\n\n"
            f"📐 例题：一条mRNA有300个碱基→编码100个氨基酸（忽略终止码），若考虑终止码则最多99个AA。"
        )
    if any(k in s for k in ("分离定律","孟德尔","杂合子","纯合子","显性","隐性","性状分离比")):
        return (
            f"【{s}——孟德尔第一定律】\n\n"
            f"**实验材料：豌豆的优点**：\n"
            f"- 自花传粉、闭花授粉→自然状态下纯种\n"
            f"- 有易于区分的相对性状（高茎vs矮茎、圆粒vs皱粒等）\n\n"
            f"**一对相对性状杂交实验结果**：\n"
            f"F₁ 全部表现为**显性性状**（如高茎）\n"
            f"F₂ 出现**性状分离** → 显性:隐性 ≈ **3:1**\n\n"
            f"**假说-演绎法验证**：\n"
            f"1. 假说：①遗传因子成对存在 ②分别进入不同配子 ③受精时随机结合\n"
            f"2. 演绎：F₁(Aa) × F₁(Aa) → 后代1AA:2Aa:1aa → 表型3:1\n"
            f"3. 测交实验验证：Aa × aa → 1:1 ✓\n\n"
            f"📐 例题：杂合子自交n代后，纯合子比例 = 1-(1/2)ⁿ，杂合子=(1/2)ⁿ。\n"
            f"💡 分离定律本质：**同源染色体上等位基因的分离**（发生在减Ⅰ后期）。"
        )
    if any(k in s for k in ("伴性遗传","红绿色盲","血友病","X连锁","交叉遗传")):
        return (
            f"【{s}——性染色体上的遗传】\n\n"
            f"**人类性别决定**：XX女性 / XY男性（父亲决定子女性别——提供X或Y）\n\n"
            f"**伴X隐性遗传特点**（红绿色盲/血友病）：\n"
            f"- **男性患者多于女性**（只需一个X带致病基因就发病）\n"
            f"- **交叉遗传**：男患者的致病基因一定来自母亲，传给女儿\n"
            f"- **女性携带者**：表型正常但可能传给儿子\n\n"
            f"**常见遗传系谱判断口诀**：\n"
            f"- 无中生有为隐性，有中生无为显性\n"
            f"- 隐性遗传看女病：父子都病为伴性（否则常隐）\n"
            f"- 显性遗传看男病：母女都病为伴性（否则常显）\n\n"
            f"📐 例题：正常夫妇生出色盲儿子→母亲一定是携带者(XᴮXᵇ)，父亲正常(XᴮY)。\n"
            f"他们再生一个正常女儿的概率 = 3/4 × 1/2 = 3/8（先算正常概率3/4，再算女儿概率1/2）。"
        )
    if any(k in s for k in ("基因突变","诱变育种","镰刀型","碱基替换","物理诱变","化学诱变")):
        return (
            f"【{s}——基因结构的改变】\n\n"
            f"**类型**：\n"
            f"- **碱基替换**：一个碱基换成另一个（如镰刀型贫血症：GAG→GTG，Glu→Val）\n"
            f"- **增添/缺失**：插入或丢失碱基→阅读框移位→后续全错\n\n"
            f"**特点**：\n"
            f"- **普遍性**：所有生物都可能发生\n"
            f"- **随机性**：时间/部位不固定\n"
            f"- **低频性**：自然突变率很低（10⁻⁵~10⁻⁸）\n"
            f"- **多数有害**：但也有少数有利（如抗药性突变）\n"
            f"- **不定向性**：一个基因可以突变成多个不同的等位基因\n\n"
            f"**诱变因素**：\n"
            f"- 物理：紫外线、X射线、γ射线\n"
            f"- 化学：亚硝酸、硫酸二乙酯、碱基类似物\n"
            f"- 生物：病毒\n\n"
            f"💡 应用：**诱变育种**（高产青霉素菌株就是通过诱变获得的）。优点：大幅提高变异频率；缺点：盲目性大。"
        )

    # ---- 高中生物：选择性必修 · 稳态与环境 ----
    if any(k in s for k in ("内环境","稳态","血浆","组织液","淋巴","渗透压","缓冲")):
        return (
            f"【{s}——细胞生活的液体环境】\n\n"
            f"**体液的组成**：\n"
            f"- 细胞内液（约占2/3）\n"
            f"- 细胞外液 = **内环境**（约占1/3）：血浆 + 组织液 + 淋巴\n\n"
            f"**三者关系**：\n"
            f"血浆 ←→ 组织液（双向渗透）\n"
            f"  ↓ 单向渗入\n"
            f"淋巴 → 回流到血浆\n\n"
            f"**内环境的理化性质**：\n"
            f"- 渗透压：主要由NaCl（血浆）和白蛋白决定\n"
            f"- 酸碱度：pH 7.35~7.45（靠HCO₃⁻/H₂CO₃缓冲对维持）\n"
            f"- 温度：约37℃（酶的最适温度）\n\n"
            f"**稳态**：正常机体通过调节作用，使各个器官、系统协调活动，共同维持内环境相对稳定的状态。\n"
            f"稳态是机体**正常生命活动的必要条件**。"
        )
    if any(k in s for k in ("神经调节","反射","反射弧","突触","兴奋传递","静息电位","动作电位")):
        return (
            f"【{s}——神经系统的基本方式】\n\n"
            f"**反射弧**（完成反射活动的结构基础）：\n"
            f"感受器 → 传入神经 → 神经中枢 → 传出神经 → 效应器\n"
            f"\n"
            f"**兴奋在神经纤维上的传导**：\n"
            f"- 静息电位：**内负外正**（K⁺外流导致）\n"
            f"- 动作电位：**内正外负**（Na⁺内流导致）\n"
            f"- 局部电流 → 双向传导（速度快）\n\n"
            f"**兴奋在神经元之间的传递——突触**：\n"
            f"突触前膜 → 释放**神经递质**（胞吐）→ 经突触间隙 → 与突触后膜受体结合\n"
            f"- **单向传递**！（递质只能由前膜释放作用于后膜）\n"
            f"- 信号转换：电信号→化学信号→电信号\n"
            f"- 存在**突触延搁**（慢于神经纤维传导）\n\n"
            f"📐 例题：刺激脊髓中间神经元，兴奋可以从传入→传出，但不能反向——因为突触传递单向。"
        )
    if any(k in s for k in ("免疫","抗原","抗体","B细胞","T细胞","吞噬细胞","体液免疫","细胞免疫")):
        return (
            f"【{s}——人体的三道防线】\n\n"
            f"**三道防线**：\n"
            f"1. 第一道：皮肤、黏膜（非特异性）\n"
            f"2. 第二道：体液中的杀菌物质和吞噬细胞（非特异性）\n"
            f"3. 第三道：免疫器官+免疫细胞（**特异性免疫**）\n\n"
            f"**体液免疫**（B细胞主导）：\n"
            f"抗原 → 吞噬细胞处理呈递 → T细胞辅助 → B细胞活化 → \n"
            f"浆细胞 → 分泌**抗体**（与抗原特异性结合）+ 记忆B细胞\n\n"
            f"**细胞免疫**（T细胞主导）：\n"
            f"靶细胞（被病原体感染的细胞）→ T细胞识别并活化 → \n"
            f"效应T细胞 → 裂解靶细胞 + 记忆T细胞\n\n"
            f"💡 过敏反应：已免疫的机体再次接受**相同过敏原**时发生的过度免疫反应（不损伤组织细胞，有明显遗传倾向/个体差异）。"
        )
    if any(k in s for k in ("种群","出生率","死亡率","增长率","K值","J型增长","S型增长","年龄结构")):
        return (
            f"【{s}——同一区域内同种生物的全部个体】\n\n"
            f"**种群数量特征之间的关系**：\n\n"
            f"```\n"
            f"       出生率、迁入率\n"
            f"         ↓     ↓\n"
            f"种群密度 ← ——→ 死亡率、迁出率\n"
            f"         ↑\n"
            f"   年龄结构和性别比例（影响出生率/死亡率）\n"
            f"```\n\n"
            f"**种群增长曲线**：\n"
            f"- **J型增长**：理想条件（资源无限、无天敌）→ Nₜ=N₀λᵗ（λ>1）\n"
            f"- **S型增长**：现实有限环境 → 存在**K值（环境容纳量）**\n"
            f"  - K/2 时增长速率最大（渔业捕捞的最佳时机）\n"
            f"  - K值不是固定不变的，会随环境变化\n\n"
            f"**年龄结构类型**：\n"
            f"- 增长型（幼年多）：种群数量将增加\n"
            f"- 稳定型（各年龄比例相当）：相对稳定\n"
            f"- 衰退型（老年多）：种群数量将减少\n\n"
            f"📐 例题：某种群初始100，年增长率为20%（J型），5年后=100×1.2⁵≈249只。"
        )
    if any(k in s for k in ("群落","优势种","丰富度","群落演替","初生演替","次生演替")):
        return (
            f"【{s}——同一时间内聚集在一定区域的各种生物种群的集合】\n\n"
            f"**群落的物种组成**：\n"
            f"- **丰富度**：群落中物种数目的多少\n"
            f"- **优势种**：数量多、影响大的物种\n\n"
            f"**群落结构**：\n"
            f"- **垂直结构**：分层现象（森林乔木层→灌木层→草本层→地被层）→ 提高光能利用率\n"
            f"- **水平结构**：镶嵌分布（地形/土壤/光照差异造成）\n\n"
            f"**群落演替**（随时间推移一个群落替代另一个）：\n\n"
            f"| | 初生演替 | 次生演替 |\n"
            f"|---|---|---|\n"
            f"| 起点 | 从无到有（裸岩/沙丘）| 有土壤和繁殖体（火灾后草地）|\n"
            f"| 速度 | 极慢（百年~千年）| 较快（几十年~百年）|\n"
            f"| 阶段 | 地衣阶段→苔藓→草本→灌木→森林 | 多年生杂草→灌木→乔木|\n"
            f"| 例 | 裸岩演替 | 弃耕农田演替 |\n\n"
            f"💡 人类活动往往会使群落演替按照不同于自然演替的速度和方向进行（如砍伐/造林/围湖造田）。"
        )

    # ---- 高中生物：选择性必修三·生物技术与工程 ----
    if any(k in s for k in ("发酵工程","微生物培养","培养基","灭菌","接种")):
        return (
            f"【{s}——利用微生物生产产品】\n\n"
            f"**培养基的基本成分**：碳源、氮源、水、无机盐\n"
            f"- 固体培养基加**琼脂**（凝固剂）\n"
            f"- 选择培养基：允许特定微生物生长（如尿素培养基筛选分解菌）\n\n"
            f"**灭菌 vs 消毒**（重要区别）：\n"
            f"- **灭菌**：杀灭所有微生物（包括芽孢/孢子）→ 高压蒸汽灭菌121℃/15min\n"
            f"- **消毒**：杀死部分有害微生物（不一定杀灭芽孢）→ 煮沸/酒精/紫外线\n\n"
            f"**发酵工程流程**：\n"
            f"菌种选育 → 培养基配制 → 灭菌 → 扩大培养 → 接种 → 发酵罐控制条件 → \n"
            f"产物分离提纯\n\n"
            f"**常见发酵产物**：\n"
            f"- 啤酒/白酒（酵母菌，厌氧产乙醇）\n"
            f"- 醋（醋酸菌，好氧）\n"
            f"- 泡菜/酸奶（乳酸菌，厌氧产乳酸）\n\n"
            f"📐 例题：制作酸奶需要在**密封、30-35℃、无氧条件下发酵**（乳酸菌厌氧且最适此温度）。"
        )
    if any(k in s for k in ("细胞工程","动物细胞培养","克隆","单克隆抗体","杂交瘤","融合")):
        return (
            f"【{s}——细胞水平的操作技术】\n\n"
            f"**动物细胞培养**：\n"
            f"- 取材：胚胎/幼龄组织（分裂旺盛）\n"
            f"- 消化：胰蛋白酶分散成单个细胞\n"
            f"- 原代培养 → **接触抑制**（贴壁生长到表面相互接触时停止分裂）\n"
            f"- 传代培养：分瓶继续培养（一般10-50代内保持正常二倍体型）\n\n"
            f"**单克隆抗体技术**（1975年 Köhler & Milstein，诺贝尔奖）：\n"
            f"1. 给小鼠注射特定**抗原** → 小鼠产生免疫应答\n"
            f"2. 取出**B淋巴细胞**（能产生特异性抗体但不能无限增殖）\n"
            f"3. 与**骨髓瘤细胞**（能无限增殖但不产生抗体）**融合**\n"
            f"4. 用**选择培养基**筛选出**杂交瘤细胞**（既能产抗体又能无限增殖）\n"
            f"5. 克隆化培养+抗体检测→筛选出能产所需抗体的杂交瘤株\n\n"
            f"💡 单克隆抗体优点：**特异性强、灵敏度高、可大量制备**。应用于诊断试剂/靶向药物。"
        )
    if any(k in s for k in ("基因工程","重组DNA","限制酶","DNA连接酶","运载体","质粒","目的基因")):
        return (
            f"【{s}——按意愿定向改造生物】\n\n"
            f"**基本工具**：\n"
            f"- **限制性核酸内切酶（限制酶）**：「分子剪刀」— 识别特定序列并切断\n"
            f"- **DNA连接酶**：「分子胶水」— 连接DNA片段\n"
            f"- **运载体**（常用质粒）：将目的基因导入受体细胞\n\n"
            f"**操作步骤**：\n"
            f"1. **获取目的基因**：从基因组文库/PCR/人工合成\n"
            f"2. **构建基因表达载体**：目的基因 + 启动子 + 终止子 + 标记基因 + 复制原点\n"
            f"3. **导入受体细胞**：显微注射（动物）/ Ca²⁺处理法（细菌）/ 农杆菌法（植物）\n"
            f"4. **目的基因检测与鉴定**：\n"
            f"   - DNA水平：核酸分子杂交\n"
            f"   - RNA水平：分子杂交检测是否转录\n"
            f"   - 蛋白质水平：抗原-抗体杂交\n\n"
            f"📐 例题：一种限制酶识别序列GAATTC，在G和A之间切开→产生**黏性末端**（AATT突出）。\n"
            f"不同酶如果切出相同的黏性末端也可以连接——这是基因工程拼接的关键原理。"
        )
    if any(k in s for k in ("胚胎工程","体外受精","胚胎移植","试管婴儿","桑椹胚","囊胚","原始性腺")):
        return (
            f"【{s}——对早期胚胎所进行的操作】\n\n"
            f"**理论基础**：哺乳动物的**受精和早期胚胎发育规律**（减数分裂→受精→卵裂→囊胚）\n\n"
            f"**主要技术环节**：\n\n"
            f"① **体外受精**：\n"
            f"  - 卵母细胞采集+成熟培养（MⅡ中期才能受精）\n"
            f"  - 精子获能处理后与卵子共培养\n"
            f"  - 受精标志：透明带观察到**两个极体**\n\n"
            f"② **早期胚胎培养**：\n"
            f"  - 发育过程：受精卵 → 卵裂期 → **桑椹胚**（32细胞左右，所有细胞具全能性）→ \n"
            f"    **囊胚**（内细胞团将来发育为胎儿本身+滋养层发育为胎膜胎盘）\n"
            f"  - 发育培养液中通常要加入**血清**\n\n"
            f"③ **胚胎移植**（核心技术）：\n"
            f"  - 将早期胚胎移植到**同种的、生理状态相同的雌性动物**体内\n"
            f"  - 胚胎移植是胚胎工程的**最后一道工序**\n"
            f"  - 受体对移入子宫的外来胚胎基本不发生**免疫排斥**\n\n"
            f"④ **胚胎分割**：\n"
            f"  - 选择**桑椹胚或囊胚**进行机械分割（注意均等分割内细胞团）\n"
            f"  - 来自同一胚胎的后代具有**相同的遗传物质**（相当于无性繁殖/克隆）\n\n"
            f"⑤ **胚胎干细胞**：\n"
            f"  - 来源：**原始性腺**或**囊胚的内细胞团**\n"
            f"  - 特点：体积小、细胞核大、核仁明显；**具有发育的全能性**\n"
            f"  - 应用：治疗人类疾病（如帕金森/糖尿病）、研究体外 differentiation\n\n"
            f"📐 例题：一头名贵奶牛产生的胚胎经分割为4份→移植到4头代孕母牛→可获得4头遗传物质完全相同的小牛。"
        )
    if any(k in s for k in ("安全伦理","生物安全","伦理问题","克隆人","设计婴儿","转基因食品")):
        return (
            f"【{s}——科技发展带来的思考】\n\n"
            f"**一、转基因生物的安全性讨论**：\n\n"
            f"① **食物安全**方面：\n"
            f"  - 担心：滞后效应（毒性/过敏原）、营养成分改变、宗教/素食顾虑\n"
            f"  - 反驳：严格检测+多年食用无不良记录+传统作物也有安全问题\n\n"
            f"② **生物安全**方面：\n"
            f"  - 担心：转基因植物扩散→成为「超级杂草」、转基因逃逸污染野生近缘种\n"
            f"  - 反驳：天然植物也有扩散风险、可通过物理/生物隔离防控\n\n"
            f"③ **环境安全**方面：\n"
            f"  - 担心：影响非目标生物（如转Bt玉米花粉毒死蝴蝶幼虫）\n"
            f"  - 反驳：科学评估证明风险可控、减少农药使用反而保护生态\n\n"
            f"**二、关注生物技术的伦理问题**：\n\n"
            f"① **克隆人**（生殖性克隆）：\n"
            f"  - 各国立法一致**禁止**（伦理：违反人类尊严；技术：成功率极低/畸形率高）\n"
            f"  - **治疗性克隆**：利用胚胎干细胞培育组织器官用于医疗——多数国家允许规范研究\n\n"
            f"② **设计试管婴儿**：\n"
            f"  - 为救治患病同胞而设计HLA匹配的婴儿\n"
            f"  - 争议：把人当作「工具」还是「目的」？\n"
            f"  - 目前共识：可用于治病但不应用于挑选性别/外貌/智力\n\n"
            f"③ **基因身份证**：\n"
            f"  - 包含个人基因信息的证件\n"
            f"  - 隐忧：基因歧视（就业/保险/婚恋中被不公平对待）\n\n"
            f"💡 核心原则：科技发展必须**以人为本**——既要大胆创新推动进步，也要守住伦理底线保障人权。"
        )
    if any(k in s for k in ("植物激素","生长素","吲哚乙酸","顶端优势","两重性","乙烯","脱落酸")):
        return (
            f"【{s}——植物体内的微量调节物质】\n\n"
            f"**生长素的发现**（温特实验，1928）：\n"
            f"- 达尔文→向光性实验（胚芽鞘尖端感光）\n"
            f"- 波森/詹森→尖端产生某种「影响」可透过琼脂片\n"
            f"- **温特**：证实这种影响是一种**化学物质**→ 后来命名为**生长素（IAA/吲哚乙酸）**\n\n"
            f"**生长素的运输**：\n"
            f"- 极性运输：从**形态学上端→下端**（主动运输）\n"
            f"- 横向运输：单侧光下从向光侧→背光侧（导致背光侧生长快→向光弯曲）\n\n"
            f"**两重性**（重要考点）：\n"
            f"- 低浓度**促进**生长，高浓度**抑制**生长\n"
            f"- **顶端优势**：顶芽优先生长→侧芽受抑制（顶芽IAA向下运输积累在侧芽→浓度过高）\n"
            f"- 应用：除草剂（高浓度抑制/杀死双子叶杂草）\n\n"
            f"**五大类植物激素对比**：\n\n"
            f"| 激素 | 主要作用 | 合成部位 |\n"
            f"|---|---|---|\n"
            f"| 生长素 | 促进生长/生根/果实发育 | 幼嫩芽/叶/种子 |\n"
            f"| 赤霉素 | 促进细胞伸长/解除休眠/促进发芽 | 未成熟种子/幼根/幼芽 |\n"
            f"| 细胞分裂素 | 促进细胞分裂 | 主要是根尖 |\n"
            f"| 脱落酸 | 抑制细胞分裂/促进叶和果实的衰老脱落 | 根冠/萎蔫叶片 |\n"
            f"| 乙烯 | 促进果实成熟 | 各部位（成熟组织中更多）|\n\n"
            f"📐 例题：扦插枝条带芽易生根（芽产生生长素）；果园修剪去除顶芽→打破顶端优势→促进侧芽萌发→增产。"
        )

    # ---- 生物通用关键词匹配（保留原有初中分支）----
    if any(k in s for k in ("消化","营养","维生素","食物")):
        return (
            f"【{s}】\n\n"
            f"人体需要的六大营养物质：\n"
            f"**糖类**（供能主力）、**蛋白质**（生长发育修复）、**脂肪**（备用能源）、\n"
            f"**维生素**（调节代谢，缺乏症各异）、**水**（细胞主要成分）、**无机盐**。\n\n"
            f"消化系统：消化道（口腔→咽→食道→胃→小肠→大肠→肛门）+ 消化腺。\n"
            f"**小肠**是主要的消化和吸收场所（面积大、有多种消化液）。"
        )
    if any(k in s for k in("循环","血液","心脏","血管","动脉","静脉")):
        return (
            f"【{s}】\n\n"
            f"血液由**血浆**（运载血细胞、运输营养废物）和**血细胞**组成：\n"
            f"- **红细胞**（最多）：运输O₂和部分CO₂，含血红蛋白（Fe²⁺，红色）\n"
            f"- **白细胞**（最少最大）：吞噬病菌，防御疾病\n"
            f"- **血小板**（最小）：止血和加速凝血\n\n"
            f"心脏四腔：左心房、左心室、右心房、右心室。\n"
            f"**心室壁厚于心房**，**左心室壁最厚**（输送距离最长）。"
        )
    if any(k in s for k in("激素","内分泌","甲状腺","胰岛素","生长素")):
        return (
            f"【{s}】\n\n"
            f"激素是由**内分泌腺**分泌的对身体有特殊调节作用的化学物质。\n\n"
            f"常见激素及其作用：\n"
            f"- **生长激素**（垂体）：促进生长——幼年过多=巨人症，过少=侏儒症\n"
            f"- **甲状腺激素**（甲状腺）：促进代谢和发育——幼年缺碘=呆小症\n"
            f"- **胰岛素**（胰腺）：调节血糖——分泌不足=糖尿病\n\n"
            f"神经调节 vs 激素调节：神经快而精确；激素慢但持久。两者共同协调人体生理活动。"
        )

    # ---- 补充覆盖：高中生物高频子点 ----
    if any(k in s for k in ("中心法则","复制","表达")):
        return (
            f"【{s}——遗传信息的流动方向】\n\n"
            f"**中心法则**（Crick提出）：\n"
            f"DNA --(复制)--> DNA    （遗传信息传递给后代）\n"
            f"DNA --(转录)--> RNA   （基因表达第一步）\n"
            f"RNA --(翻译)--> 蛋白质  （基因表达第二步，合成功能产物）\n\n"
            f"**补充（后来发现）**：\n"
            f"- RNA --(复制)--> RNA     （某些病毒，如HIV逆转录、烟草花叶病毒复制）\n"
            f"- RNA --(逆转录)--> DNA   （逆转录病毒/反转录病毒，需逆转录酶）\n\n"
            f"⚠️ 中心法则的**核心意义**：遗传信息从核酸流向蛋白质是单向不可逆的。\n"
            f"但RNA在某些情况下可以自我复制或逆向转录——这是对中心法则的重要补充。"
        )
    if any(k in s for k in ("染色体变异","数目变异","结构变异","缺失","重复","倒位","易位","三体","单体")):
        return (
            f"【{s}——染色体水平的变异】\n\n"
            f"**染色体结构变异**（4种类型）：\n"
            f"| 类型 | 定义 | 影响 |\n"
            f"|---|---|---|\n"
            f"| 缺失 | 染色体片段丢失 | 基因减少 |\n"
            f"| 重复 | 染色体片段增加 | 基因增多 |\n"
            f"| 倒位 | 片段位置颠倒(180°旋转) | 基因顺序改变 |\n"
            f"| 易位 | 非同源染色体间交换片段 | 可能激活癌基因 |\n\n"
            f"**染色体数目变异**：\n"
            f"- **个别增减**：21三体综合征（多一条21号）、性腺发育不良（XO）\n"
            f"- **成倍变化**：多倍体（如三倍体西瓜无籽/甜）\n\n"
            f"📐 例题：猫叫综合征是第5号染色体**部分缺失**导致的（属于结构变异中的缺失型）。"
        )
    if any(k in s for k in ("育种","杂交育种","诱变","单倍体育种","多倍体育种")):
        return (
            f"【{s}——创造优良品种的方法】\n\n"
            f"**四种育种方法对比**：\n\n"
            f"| 方法 | 原理 | 优点 | 缺点 | 代表 |\n"
            f"|---|---|---|---|---|\n"
            f"| 杂交育种 | 基因重组 | 操作简单 | 耗时长 | 高产抗病小麦 |\n"
            f"| 诱变育种 | 基因突变 | 大幅提高变异率 | 盲目性强/有害多 | 青霉素高产菌株 |\n"
            f"| 单倍体育种 | 染色体变异 | 明显缩短育种年限 | 技术复杂/成本高 | 抗病水稻 |\n"
            f"| 多倍体育种 | 染色体变异 | 器官大/产量高 | 发育迟缓/结实率低 | 无籽西瓜/八倍体小黑麦 |\n\n"
            f"💡 **单倍体育种流程**：\nF₁花粉 → 离体培养→单倍体幼苗→秋水仙素处理→纯合二倍体（2年即可得到稳定品系，比杂交育种的5-6年快很多）"
        )
    if any(k in s for k in ("现代进化理论","自然选择","物种形成","生殖隔离","地理隔离")):
        return (
            f"【{s}——现代生物进化理论】\n\n"
            f"**达尔文自然选择学说要点**：过度繁殖+生存斗争+遗传变异+适者生存\n\n"
            f"**现代进化理论**（在达尔文基础上发展）：\n"
            f"1. **种群是进化的基本单位**（不是个体！）\n"
            f"2. **突变和基因重组提供原材料**（突变包括基因突变+染色体变异）\n"
            f"3. **自然选择决定进化方向**（定向选择使种群基因频率定向改变）\n"
            f"4. **隔离导致新物种形成**\n\n"
            f"**物种形成的三个环节**：\n"
            f"突变/基因重组 → 自然选择（基因频率改变）→ **隔离**（生殖隔离=新物种标志）\n\n"
            f"地理隔离 vs 生殖隔离：\n"
            f"- 地理隔离：物理障碍阻止交配（如山脉/河流）→ 不一定是不同物种\n"
            f"- **生殖隔离**：不能交配或交配后不能产生可育后代 → **才是不同物种的根本标志**\n\n"
            f"📐 例案：东北虎与华南虎有地理隔离但仍属同一物种；马和驴杂交产生骡（不育）→ 存在生殖隔离→ 不同物种。"
        )
    if any(k in s for k in ("发酵","微生物培养","酵母菌","乳酸菌","醋酸菌")):
        return (
            f"【{s}——利用微生物生产产品】\n\n"
            f"**传统发酵技术**：\n\n"
            f"| 产品 | 微生物 | 条件 | 关键原理 |\n"
            f"|---|---|---|---|\n"
            f"| 果酒 | 酵母菌 | 18-25℃、缺氧 | 先通气后密封（先繁殖后产酒精）|\n"
            f"| 果醋 | 醋酸菌 | 30-35℃、**好氧** | 糖→酒精→醋酸（两步发酵）|\n"
            f"| 泡菜 | 乳酸菌 | 常温、**厌氧** | 乳酸发酵（pH降至3-4抑制杂菌）|\n"
            f"| 馒头 | 酵母菌 | 温暖、有氧 | CO₂使面团膨松（发面）|\n\n"
            f"⚠️ 果酒制作关键细节：\n"
            f"- 每天拧松瓶盖放气（CO₂过多会炸瓶）\n"
            f"- 葡萄汁不要装太满（留1/3空间防溢出）\n"
            f"- 温度控制18-25℃（过高酵母死亡，过低发酵慢）"
        )
    if any(k in s for k in ("光合作用","光反应","暗反应","类囊体","基粒","卡尔文循环","C3","C4","CAM")):
        return (
            f"【{s}高中版——能量转换的核心过程】\n\n"
            f"**总反应式**：6CO₂ + 12H₂O --[光/叶绿体]--> C₆H₁₂O₆ + 6O₂ + 6H₂O\n\n"
            f"**两个阶段**：\n\n"
            f"| | 光反应（类囊体薄膜上）| 暗反应（基质中）|\n"
            f"|---|---|---|\n"
            f"| 条件 | 光、色素、酶 | 多种酶（不需光直接参与）|\n"
            f"| 物质变化 | H₂O光解→O₂+[H] | CO₂固定→C₃还原→糖类|\n"
            f"| 能量变化 | 光能→ATP中活跃化学能 | ATP中活跃化学能→有机物中稳定化学能|\n\n"
            f"**影响因素**：\n"
            f"- 光照强度：直接影响光反应→限制暗反应\n"
            f"- CO₂浓度：影响暗反应固定速率\n"
            f"- 温度：影响酶活性（暗反应酶更敏感）\n"
            f"- 矿质元素：Mg²⁺（叶绿素组成）、N/P（ATP/NADPH成分）\n\n"
            f"📐 例题：突然停止光照→[H]和ATP↓→C₃还原受阻→C₃↑/C₅↓；突然停止CO₂→C₅↑/C₃↓。"
        )
    if any(k in s for k in ("细胞呼吸","有氧呼吸","无氧呼吸","糖酵解","柠檬酸循环","氧化磷酸化")):
        return (
            f"【{s}——释放能量的代谢过程】\n\n"
            f"**有氧呼吸**（主要在线粒体中进行）：\n"
            f"C₆H₁₂O₆ + 6O₂ + 6H₂O --[酶]--> 6CO₂ + 12H₂O + 能量（大量）\n\n"
            f"三个阶段：\n"
            f"① 细胞质基质：葡萄糖 → 2丙酮酸 + [H] + 少量ATP\n"
            f"② 线粒体基质：2丙酮酸 + 6H₂O → 6CO₂ + [H] + 少量ATP\n"
            f"③ 线粒体内膜：24[H] + 6O₂ → 12H₂O + **大量ATP**（约30/34个）\n\n"
            f"**无氧呼吸**（全过程在细胞质基质）：\n"
            f"- 动物：丙酮酸 → **乳酸**（如肌肉无氧运动后酸痛）\n"
            f"- 植物/酵母：丙酮酸 → **酒精+CO₂**（酿酒/面包发酵）\n"
            f"- 共同特点：只释放少量能量（第一阶段产生的少量ATP），大部分能量留在产物中\n\n"
            f"📐 例题：1mol葡萄糖有氧呼吸净产约30-32mol ATP，无氧呼吸只产2mol ATP。有氧产能效率约40%，其余以热散失。"
        )
    if any(k in s for k in ("体液调节","激素调节","反馈调节","血糖调节","水盐调节","体温调节")):
        return (
            f"【{s}——激素等化学物质通过体液传送的调节方式】\n\n"
            f"**血糖平衡调节**（胰岛素 vs 胰高血糖素拮抗作用）：\n"
            f"- 血糖升高 → 胰岛B细胞分泌**胰岛素**→ 促进摄取/利用/储存葡萄糖→ 血糖↓\n"
            f"- 血糖降低 → 胰岛A细胞分泌**胰高血糖素**→ 促进肝糖原分解/非糖转化→ 血糖↑\n\n"
            f"**体温调节**（下丘脑是中枢）：\n"
            f"- 寒冷：血管收缩（减少散热）+ 骨骼肌战栗（增加产热）+ 甲状腺素/肾上腺素↑\n"
            f"- 炎热：血管舒张（增加散热）+ 汗腺分泌汗液（蒸发散热）\n\n"
            f"**水平衡调节**（抗利尿激素ADH）：\n"
            f"- 缺水→下丘脑渗透压感受器→垂体释放ADH↑→肾小管/集合管重吸收水↑→尿量↓\n"
            f"- 饮水过量→相反\n\n"
            f"⚠️ 所有这些调节都有**负反馈**机制——结果反过来抑制原因本身，维持稳态。"
        )

    # 生物兜底
    return (
        f"【{s}】\n\n"
        f"这是生物学中「{t}」的重要内容。\n\n"
        f"学习时要抓住**结构与功能相适应**这一核心思想，\n"
        f"借助显微镜观察和插图理解微观结构，\n"
        f"用对比表格区分易混淆的概念，\n"
        f"按层次（细胞→组织→器官→系统→个体）构建知识网络。"
        f"\n\n💡 记住：观察实验是生物学的根基，多动手多思考！"
    )


def _gen_physics_content(t, s):
    """物理学科智能内容引擎 —— 每个子点独立详细讲解"""
    
    # ═══════════════════════════════════════
    #  机械运动/速度（独立分支）
    # ═══════════════════════════════════════
    if any(k in s for k in("机械运动","参照系","速度","路程","时间")) and "声" not in s:
        return (
            f"【{s}——运动的描述】\n\n"
            f"你坐在行驶的车里，路边的树在向后退——树真的在后退吗？当然不是！"
            f"这是因为你选了**车**作为参照物。这就是研究运动的第一步：**先选定参照物**。\n\n"

            f"**📌 一、参照物——判断运动的标准**\n\n"
            f"参照物是**假定不动的物体**。同一个物体，选不同的参照物，结论可能不同：\n"
            f"- 乘客坐在行驶的列车上：以**地面**为参照物→乘客在运动；以**列车**为参照物→乘客静止\n"
            f"- 月亮从云层中穿过：实际是**云在动**（以云为参照→月亮在运动）\n\n"
            f"⚠️ 参照物的选择是任意的，但通常选**地面或地面上静止的物体**。\n\n"

            f"**📏 二、速度——描述物体运动快慢的物理量**\n\n"
            f"定义：物体在单位时间内通过的路程。公式：$v = \\frac{{s}}{{t}}$\n\n"
            f"| 符号 | 含义 | 单位 | 常用单位 |\n"
            f"|------|------|------|----------|\n"
            f"| $v$ | 速度 | m/s | km/h |\n"
            f"| $s$ | 路程 | m | km |\n"
            f"| $t$ | 时间 | s | h |\n\n"
            f"单位换算：**1 m/s = 3.6 km/h**（乘3.6变km/h，除3.6变m/s）\n"
            f"例：36 km/h = 36÷3.6 = **10 m/s**\n\n"

            f"**🔄 三、匀速直线运动 vs 变速运动**\n\n"
            f"- **匀速直线运动**：速度不变、路径是直线（理想模型）。$s = vt$\n"
            f"- **变速运动**：速度随时间变化。用**平均速度**粗略描述：$\\bar{{v}} = \\frac{{s_{{总}}}}{{t_{{总}}}}$\n\n"
            f"⚠️ 平均速度**不等于**速度的平均值！必须用总路程÷总时间。"
        )

    # ═══════════════════════════════════════
    #  声现象（每个子点独立）
    # ═══════════════════════════════════════
    if ("声音" in s or "声" in s) and any(k in s for k in("产生","振动","声音产生","发声")):
        return (
            f"【{s}】\n\n"
            f"声音是怎么产生的？你说话时摸一下喉咙——是不是感觉到在**振动**？"
            f"一切发声体都在振动！振动停止，发声也停止（但声音可能还在传播）。\n\n"

            f"**实验验证**：\n"
            f"1. 用手拨动钢尺——尺子振动→发出\"嗡嗡\"声；停止振动→声音消失\n"
            f"2. 敲击鼓面——撒些碎纸屑在上面，看到纸屑在**跳动**（把鼓面的微小振动放大了）\n"
            f"3. 音叉实验——把振动的音叉接触水面，水花四溅（说明音叉确实在振动）\n\n"

            f"💡 关键结论：**声音是由物体振动产生的**。振动是发声的原因，但振动不一定都能听到（频率要在20~20000Hz之间）。"
        )
    
    if "传播" in s or ("声" in s and ("介质" in s or "传播速度" in s)):
        return (
            f"【{s}——声音怎么传到你耳朵里的？】\n\n"
            f"声音的传播需要**介质**（固体、液体、气体都可以），**真空不能传声**！\n\n"
            f"🔬 **经典实验——真空铃实验**：\n"
            f"把闹钟放在玻璃罩内，逐渐抽出空气→铃声越来越小→几乎听不到→说明**空气越少，传声越差**→推理出真空不能传声。\n\n"
            f"**不同介质中的声速比较**：\n"
            f"- 一般：**v固体 > v液体 > v气体**\n"
            f"- 15℃空气中：v ≈ **340 m/s**（这个数要背下来！）\n"
            f"- 钢铁中：v ≈ 5200 m/s（所以贴着铁轨能提前听到火车来了）\n\n"
            f"💡 回声现象：声音遇到障碍物反射回来。要区分开回声和原声，障碍物至少要离**17米远**（人耳分辨时间约0.1秒）。\n"
            f"应用：回声定位（蝙蝠）、声呐（探测海底深度）"
        )

    if any(k in s for k in("音调","响度","音色","音调响度","频率","振幅")):
        return (
            f"【{s}——声音的三要素】\n\n"
            f"同样是\"哆来咪\"，为什么每个人的声音不一样？为什么钢琴和小提琴弹同一个音符听起来也不同？"
            f"这就要用到声音的**三要素**：\n\n"

            f"**① 音调——声音的高低**（不是大小！）\n"
            f"- 由**频率**决定：频率越高→音调越高（声音越尖细）\n"
            f"- 频率：物体每秒振动的次数，单位Hz（赫兹）\n"
            f"- 例：女高音频率高于男低音；蚊子翅膀振动快→音调高（\"嗡嗡\"尖叫声）\n"
            f"- 人耳能听到的范围：**20 Hz ~ 20000 Hz**\n\n"

            f"**② 响度——声音的大小（强弱）**\n"
            f"- 由**振幅**决定：振幅越大→响度越大（声音越响）\n"
            f"- 还与距离有关：离声源越近→响度越大\n"
            f"- 例：用力敲鼓→鼓面振幅大→响度大；轻敲→响度小\n\n"

            f"**③ 音色——声音的品质/特色**\n"
            f"- 区分不同发声体的**最重要特征**！\n"
            f"- 同样唱一个\"啊\"字，你能分辨出是谁在唱→这就是**音色**不同\n"
            f"- 由发声体的材料、结构决定（每种乐器有自己独特的音色）\n\n"
            f"⚠️ 易混点：**音调≠响度！** 音调是高低（尖/沉），响度是大/小（响/轻）"
        )

    if "噪声" in s:
        return (
            f"【{s}】\n\n"
            f"从物理学角度：噪声是发声体做**无规则振动**产生的声音。\n"
            f"从环境保护角度：凡是妨碍人们正常休息、学习和工作的声音都是噪声。\n\n"

            f"**噪声的危害**：\n"
            f"- ≤30dB：较安静的正常环境\n"
            f"- 70~90dB：影响工作效率\n"
            f"- ≥150dB：突然暴露可致双耳完全失去听力\n\n"

            f"**控制噪声的三条途径**（考试重点）：\n"
            f"1. **在声源处减弱**：摩托车消声器、禁止鸣笛\n"
            f"2. **在传播过程中减弱**：隔音墙、种树、关门窗\n"
            f"3. **在人耳处减弱**：戴耳塞、耳罩\n\n"
            f"💡 记忆口诀：**\"源传人\"**——声源、传播过程、人耳"
        )

    # ═══════════════════════════════════════
    #  力学（每个子点独立）
    # ═══════════════════════════════════════
    if (s == "力的概念" or s == "力") and "合" not in s and "图" not in s and "弹" not in s and "重" not in s and "摩" not in s:
        return (
            f"【{s}】\n\n"
            f"什么是力？你推桌子、拉橡皮筋、踢足球……这些动作都有一个共同点："
            f"**物体对物体的作用**。这就是力的定义。\n\n"

            f"**力的两个关键**：\n"
            f"1. **力不能脱离物体而存在**——至少要有两个物体（施力物体 + 受力物体）\n"
            f"2. **力的作用是相互的**——你推墙，墙也在推你！（手会疼就是证据）\n\n"
            f"**力的作用效果**（两类，必考）：\n"
            f"1. **改变物体的形状**（形变）：捏橡皮泥、拉弹簧、压海绵\n"
            f"2. **改变物体的运动状态**（速度大小或方向变化）：\n"
            f"   - 从静止到运动 / 从运动到静止\n"
            f"   - 速度变大 / 速度变小 / 运动方向改变\n\n"
            f"**力的三要素**——影响力的效果三个因素：\n"
            f"✦ **大小**（用力越大效果越明显）\n"
            f"✦ **方向**（向左推 vs 向右推，效果相反）\n"
            f"✦ **作用点**（推门时把手的位置不同，省力程度不同）\n\n"
            f"力的单位：**N（牛顿）**。拿起两个鸡蛋的力大约是1N。"
        )

    if "弹力" in s:
        return (
            f"【{s}】\n\n"
            f"你压弹簧，弹簧要恢复原状就会反推你——这种**物体由于发生弹性形变而产生的力**叫弹力。\n\n"

            f"**产生条件（缺一不可）**：\n"
            f"1. 两物体**直接接触**\n"
            f"2. 发生了**弹性形变**（撤去外力后能恢复原状）\n\n"
            f"**常见的三种弹力**：\n"
            f"- **压力**：垂直于接触表面指向被压物体（书对桌面的压力↓）\n"
            f"- **支持力**：垂直于接触表面指向被支持物体（桌面对书的支持力↑）\n"
            f"- **拉力**：沿绳/杆指向绳收缩的方向\n\n"
            f"**弹簧测力计原理**：在弹性限度内，**弹簧的伸长量与所受拉力成正比**（F=kx，胡克定律的初中版）。\n"
            f"⚠️ 注意是**伸长量**（变化量），不是总长度！"
        )

    if "重力" in s and "心" not in s:
        return (
            f"【{s}】\n\n"
            f"抛出的球为什么会落回地面？因为地球对它有一种吸引力——**重力**。\n\n"
            f"**定义**：由于地球的吸引而使物体受到的力。符号：**G**\n\n"
            f"**重力公式**：**G = mg**\n"
            f"- G：重力（单位 N）\n"
            f"- m：质量（单位 kg）\n"
            f"- g：重力常数 ≈ **9.8 N/kg**（粗算可用10 N/kg）\n\n"
            f"**重力的方向**：**竖直向下**（不是\"垂直向下\"！竖直是指向地心的方向）\n"
            f"应用：重垂线（检查墙壁是否竖直）、水平仪\n\n"
            f"**重心**：重力在物体上的等效作用点。\n"
            f"- 质量均匀、形状规则的重心在**几何中心**\n"
            f"- 不规则物体的重心可以用**悬挂法**找出来"
        )

    if "摩擦" in s or "摩擦力" in s:
        return (
            f"【{s}】\n\n"
            f"你在冰面上比在地面上容易滑倒——这是因为**摩擦力**不同。\n"
            f"摩擦力是阻碍物体**相对运动**（或相对运动趋势）的力。\n\n"
            f"**两种摩擦力**：\n\n"
            f"① **静摩擦力**：物体有相对运动趋势但还没动时\n"
            f"   - 例：推箱子没推动时，箱子底部受到的就是静摩擦力\n"
            f"   - 大小：等于外力（0 ~ 最大静摩擦之间变化）\n\n"
            f"② **滑动摩擦力**：物体已经滑动时\n"
            f"   - 公式：**f = μN**（μ=摩擦系数，N=正压力）\n"
            f"   - 影响因素：**压力大小**和**接触面粗糙程度**\n"
            f"   - 与接触面积大小、运动速度快慢无关！\n\n"
            f"**增大/减小摩擦的方法**：\n"
            f"- 增大：增大压力、使接触面更粗糙（轮胎花纹）\n"
            f"- 减小：减小压力、加润滑油、变滑动为滚动（轴承）、使接触面分离（磁悬浮）"
        )

    if "合成" in s or "力的合成" in s:
        return (
            f"【{s}】\n\n"
            f"两个人一起推箱子，一个人向东推100N，另一个人向南推100N，箱子会往哪个方向走？"
            f"这就需要用到**力的合成**——求几个力的等效力。\n\n"
            f"**同一直线上二力合成**：\n"
            f"- 方向相同：F = F₁ + F₂（方向与这两个力相同）\n"
            f"- 方向相反：F = |F₁ − F₂|（方向与较大的那个力相同）\n"
            f"例：F₁=10N向东，F₂=3N向西 → 合力F=7N向东\n\n"

            f"**互成角度的二力合成**：用**平行四边形定则**\n"
            f"以两个力为邻边作平行四边形，**对角线**就是合力。\n"
            f"- 夹角越小→合力越大（夹角=0°时合力最大=F₁+F₂）\n"
            f"- 夹角越大→合力越小（夹角=180°时合力最小=|F₁−F₂|）\n"
            f"- 合力范围：|F₁−F₂| ≤ F ≤ F₁+F₂"
        )

    if "图示" in s or ("力" in s and "示意图" in s):
        return (
            f"【{s}】\n\n"
            f"力的图示是用一根**带箭头的线段**把力的三要素都表示出来：\n\n"
            f"画法步骤：\n"
            f"1. 确定受力物体（作用点画在物体上）\n"
            f"2. 沿力的方向画线段（长度表示力的大小——要先定标度！）\n"
            f"3. 在线段末端画箭头（表示方向）\n"
            f"4. 标明力的符号和数值（如 \"F=20N\"）\n\n"
            f"⚠️ 注意：同一幅图中，各力的标度必须统一！如果标度1段=5N，那么20N就画4段长。\n\n"
            f"与**力的示意图**的区别：示意图只需画出力的方向和作用点，不需要严格按比例画长度。"
        )

    # ═══════════════════════════════════════
    #  运动和力（牛顿定律相关）
    # ═══════════════════════════════════════
    if "惯性" in s and "定律" not in s:
        return (
            f"【{s}】\n\n"
            f"公交车突然刹车，你的身体为什么会向前倾？不是因为有什么力量推了你——而是因为**惯性**。\n\n"
            f"**惯性定义**：物体保持原来运动状态（静止或匀速直线运动）不变的**固有属性**。\n\n"
            f"关键理解：\n"
            f"1. **一切物体都有惯性**（不管是否在运动、不管受力与否）\n"
            f"2. 惯性**只跟质量有关**——质量越大，惯性越大（货车比轿车难刹车）\n"
            f"3. 惯性**不是力！** 不能说\"受到惯性\"、\"惯性力\"、\"惯性作用\"\n\n"
            f"生活中的惯性现象：\n"
            f"- ✅ 拍打衣服除尘（衣服动，灰尘因惯性保持静止→脱落）\n"
            f"- ✅ 锤头松了把柄撞地上（柄停，锤头继续向下→套紧）\n"
            f"- ✅ 跳远时助跑（起跳后身体因惯性保持向前的速度）\n"
            f"- ❌ 篮球投出去后继续飞行（不是\"受惯性力\"，是**有惯性**）"
        )

    if any(k in s for k in("牛顿第一定律","牛顿定律")):
        return (
            f"【{s}——力与运动的正确关系】\n\n"
            f"亚里士多德曾经认为：\"必须有力作用在物体上，物体才能运动。\"\n"
            f"这个错误观点统治了近2000年！直到伽利略用理想实验推翻了它。\n\n"
            f"伽利略的推理（理想斜面实验）：\n"
            f"让小球从一个斜面滚下再滚上另一个斜面→斜面越缓→小球滚得越远→"
            f"如果第二个斜面变成水平面→小球将**永远滚下去**……\n\n"
            f"后来牛顿总结出了**牛顿第一定律**（也叫惯性定律）：\n\n"
            f"**一切物体在没有受到力的作用时，总保持静止状态或匀速直线运动状态。**\n\n"
            f"⚠️ 重要推论：**力不是维持运动的原因，力是改变运动状态的原因！**\n"
            f"（这一点颠覆直觉但非常重要！）"
        )

    # ═══════════════════════════════════════
    #  压强（每个子点独立）
    # ═══════════════════════════════════════
    if ("压强" in s or "帕斯卡" in s) and "液" not in s and "大" not in s and "气" not in s and "流" not in s:
        return (
            f"【{s}】\n\n"
            f"为什么针尖容易刺破皮肤而手掌不容易？同样的力，**受力面积越小，效果越明显**——这就是**压强**的概念。\n\n"
            f"**定义**：物体所受的**压力**与**受力面积**之比。\n"
            f"公式：**p = F/S**\n\n"
            f"| 物理量 | 符号 | 单位 |\n"
            f"|--------|------|------|\n"
            f"| 压强 | p | Pa（帕斯卡）|\n"
            f"| 压力 | F | N（牛顿）|\n"
            f"| 受力面积 | S | m²（平方米）|\n\n"
            f"**增大/减小压强的方法**：\n"
            f"- 增大压强：**增大F**（用力按）或**减小S**（刀刃磨薄、钉子尖头）\n"
            f"- 减小压强：**减小F**或**增大S**（坦克履带、书包宽肩带、滑雪板）\n\n"
            f"换算：1 Pa = 1 N/m²（1平方米面积上受1牛顿的压力）"
        )

    if "液" in s and "压" in s:
        return (
            f"【{s}】\n\n"
            f"液体内部的压强有什么特点？为什么水坝要做成**下宽上窄**？\n"
            f"因为液体压强随深度增加而增大！\n\n"
            f"**液体压强公式**：**p = ρgh**\n"
            f"- p：压强（Pa）\n"
            f"- ρ：液体密度（kg/m³）\n"
            f"- g：9.8 N/kg\n"
            f"- h：**深度**（从液面向下到该点的竖直距离，m）\n\n"
            f"⚠️ 关键理解：\n"
            f"1. 液体压强只与**ρ**和**h**有关，与容器形状、液体总量无关！\n"
            f"2. 同一深度各个方向压强**相等**\n"
            f"3. h 是**深度**（从液面往下算），不是高度！\n\n"
            f"连通器原理：同种液体静止时，各容器液面保持相平（茶壶、锅炉水位计）"
        )

    if "大气" in s or ("气" in s and "压" in s):
        return (
            f"【{s}——看不见的大气压力】\n\n"
            f"空气也有重量，所以会对浸在其中的物体产生压强——**大气压强**。\n\n"
            f"**证明大气压存在的经典实验**：\n"
            f"1. **马德堡半球实验**（1654年）：两个铜半球抽去空气后，用了16匹马才拉开！证明了大气压非常大\n"
            f"2. **覆杯实验**：装满水的杯子盖上纸片倒过来——水不会流出来（大气压托住了纸片+水）\n\n"
            f"**测量——托里拆利实验**（1643年）：\n"
            f"在一根约1米长的玻璃管中灌满水银，倒置在水银槽中→管内水银面下降到约760mm处就不再降了\n"
            f"→ 管内上方是**真空**（托里拆利真空）\n"
            f"→ 760mm高的水银柱产生的压强 = **标准大气压**\n\n"
            f"**标准大气压值**：\n"
            f"1 atm = **760 mmHg** = **1.01×10⁵ Pa** ≈ **10⁵ Pa**（这个数要背！）\n\n"
            f"💡 应用：吸管喝饮料（大气压把饮料压入嘴里）、吸盘挂钩、注射器抽药液"
        )

    if "流体" in s and "压" in s:
        return (
            f"【{s}】\n\n"
            f"流体（流动的液体或气体）的压强有一个有趣的规律：流速越大的位置，压强越**小**！\n\n"
            f"**伯努利原理**（初中简化版）：\n"
            f"**流体流速大的地方压强小，流速小的地方压强大。**\n\n"
            f"生活实例：\n"
            f"1. **飞机升力**：机翼上凸下平→上方空气流速快→压强小；下方流速慢→压强大→产生向上的升力\n"
            f"2. **火车站安全线**：列车驶过时周围空气流速快→压强小→人容易被推向列车\n"
            f"3. **喷雾器**：按压活塞→小孔处流速快→压强小→液体被大气压压上来形成雾\n"
            f"4. **足球弧线球（香蕉球）**：旋转导致两侧空气流速不等→压强不等→球的轨迹弯曲"
        )

    # ═══════════════════════════════════════
    #  质量与密度（每个子点独立）
    # ═══════════════════════════════════════
    if "质量" in s and ("天平" in s or s == "质量" or "测量" not in s) and "密" not in s:
        return (
            f"【{s}】\n\n"
            f"**质量**：物体所含**物质的多少**，符号 **m**，单位 **kg**（千克）。\n\n"
            f"质量是物体的**固有属性**——不随形状、状态、位置改变！\n"
            f"- 一块铁做成铁锤还是铁钉→质量不变\n"
            f"- 水结成冰→质量不变（体积变大但物质多少没变）\n"
            f"- 宇航员到月球上→质量不变（重力变了但质量没变）\n\n"
            f"**质量的测量工具——天平**（托盘天平使用步骤）：\n"
            f"1. **调平**：把天平放水平→游码归零→调节平衡螺母使指针指中央\n"
            f"2. **称量**：左盘放物体、右盘放砝码（左物右码）\n"
            f"3. **读数**：m = 砝码总质量 + 游码对应刻度值\n\n"
            f"⚠️ 注意：不能直接称量超过量程的物品；用镊子取砝码（防止手汗腐蚀）；潮湿/化学药品放烧杯里称"
        )

    if s == "密度" or (s.find("密度") >= 0 and "测" not in s and "应" not in s and "鉴" not in s):
        return (
            f"【{s}】\n\n"
            f"同样体积的铁块和木块，为什么铁块重得多？因为它们内部物质的**密集程度**不同——这就是**密度**的概念。\n\n"

            f"**定义**：某种物质组成的物体的**质量与体积之比**。\n"
            f"公式：**ρ = m/V**\n\n"
            f"| 物理量 | 符号 | 单位 | 常见值 |\n"
            f"|--------|------|------|--------|\n"
            f"| 密度 | ρ | kg/m³ 或 g/cm³ | 水=1.0g/cm³ |\n"
            f"| 质量 | m | kg 或 g | — |\n"
            f"| 体积 | V | m³ 或 cm³ | — |\n\n"
            f"换算：**1 g/cm³ = 1000 kg/m³**（水的密度 = 1.0 g/cm³ = 1000 kg/m³）\n\n"
            f"常见物质密度记忆：\n"
            f"- 水银(13.6) > 铅(11.3) > 铜(8.9) > 铁(7.9) > 铝(2.7)\n"
            f"- 水(1.0) > 煤油(0.8) > 酒精(0.8)\n"
            f"- 空气≈1.29 kg/m³（远小于固体液体）"
        )

    if "测量" in s or ("密" in s and "测" in s):
        return (
            f"【{s}】\n\n"
            f"如何测量一块不规则石头的密度？需要两步：测质量 + 测体积。\n\n"

            f"**实验器材**：天平、量筒、水、细线、待测固体\n\n"
            f"**实验步骤**：\n"
            f"① 用天平测出固体的**质量 m**\n"
            f"② 量筒中倒入适量水，读出体积 **V₁**\n"
            f"③ 用细线拴住固体缓慢浸入水中，读出体积 **V₂**\n"
            f"④ 固体体积 V = V₂ − V₁\n"
            f"⑤ 计算密度 ρ = m / (V₂ − V₁)\n\n"
            f"⚠️ 关键细节：\n"
            f"- 量筒中的水要\"适量\"——能浸没固体且浸没后液面不超量程\n"
            f"- 固体要**缓慢**浸入（避免溅出水导致误差）\n"
            f"- 如果固体吸水（如砖块），需要在表面涂一层凡士林或用排沙法代替排水法"
        )

    if ("应用" in s or "鉴别" in s or "利用" in s) and "密" in s:
        return (
            f"【{s}】\n\n"
            f"密度在实际中有两大核心用途：\n\n"
            f"**一、鉴别物质**\n"
            f"测出一个物体的密度→查表对比→判断是什么物质。\n"
            f"例：一个金属球质量54g、体积10cm³ → ρ=5.4g/cm³ → 不是纯铝(2.7)也不是纯铁(7.9)，可能是合金。\n\n"
            f"**二、判断空心与否**\n"
            f"例：一个铁球质量158g、体积30cm³\n"
            f"- 如果是实心：V实 = m/ρ = 158÷7.9 = 20cm³\n"
            f"- 实际V=30cm³ > V实=20cm³ → **这个铁球是空心的！**\n\n"
            f"其他应用：\n"
            f"- 农业上：选种（饱满的种子密度大→沉底，瘪的浮起来）\n"
            f"- 工业上：根据不同密度分离矿石"
        )

    # ═══════════════════════════════════════
    #  内能细节（每个子点独立）
    # ═══════════════════════════════════════
    if "分子动理论" in s or "分子运动" in s or ("分子" in s and "热" in s):
        return (
            f"【{s}】\n\n"
            f"为什么能闻到花香？为什么布朗运动中花粉颗粒不停地做无规则运动？"
            f"这些都和分子的热运动有关。\n\n"

            f"**分子动理论的三个基本观点**：\n\n"
            f"1. **物质由分子构成**（分子直径约10⁻¹⁰m，极小）\n"
            f"2. **分子在永不停息地做无规则运动**（温度越高越剧烈）\n"
            f"   - 扩散现象证明：墨水在水中散开、长期堆放的煤墙变黑\n"
            f"3. **分子间存在间隙**（也相互作用：引力和斥力同时存在）\n"
            f"   - 引力：固体很难被拉断；斥力：固体很难被压缩\n\n"
            f"💡 物体的三态差异本质上是分子间距和运动的差异：\n"
            f"- 固体：间距小→有固定形状体积\n"
            f"- 液体：间距稍大→有固定体积无固定形状\n"
            f"- 气体：间距很大→无固定形状体积"
        )

    if s == "内能" or ("内能" in s and "比" not in s and "热机" not in s):
        return (
            f"【{s}】\n\n"
            f"一杯热水和一杯冷水有什么区别？从微观上看——热水里的分子运动更剧烈！"
            f"这种微观运动的能量就是**内能**。\n\n"

            f"**定义**：物体内所有分子的**动能**和**势能**的总和。\n\n"
            f"影响内能的因素：\n"
            f"1. **温度**：温度越高→分子运动越快→内能越大（最主要因素）\n"
            f"2. **质量/物质的量**：同温下越多物质→分子数越多→总内能越大\n"
            f"3. **物态**：同温度同质量的同种物质：气态内能>液态内能>固态内能\n\n"
            f"⚠️ 注意：**一切物体都有内能！** 即使温度为绝对零度(-273.15℃)也有零点能（初中层面记住\"都有\"即可）\n\n"
            f"**改变内能的两种方式**：\n"
            f"① **做功**（能量的转化）：摩擦生热（机械能→内能）、气体压缩升温\n"
            f"② **热传递**（能量的转移）：加热、冷却（从高温传向低温）\n"
            f"两者在**改变内能的效果上是等效的**"
        )

    if "比热容" in s or "比热" in s:
        return (
            f"【{s}——物质的\"热容量\"】\n\n"
            f"同样吸收100J的热量，水和油哪个升温更快？答案是**油**。"
            f"因为每种物质\"容纳热量\"的能力不同——这就是**比热容**。\n\n"

            f"**定义**：1kg的某种物质温度升高1℃所吸收的热量。\n"
            f"符号 **c**，单位 **J/(kg·℃)**。\n\n"
            f"**公式**：Q吸 = cmΔt （Q放 = cmΔt 也适用）\n\n"
            f"水的比热容 c水 = **4.2×10³ J/(kg·℃)** —— 这个数值很大！\n\n"
            f"c大的意义：\n"
            f"- 同样受热/冷却时，温度变化**小**（\"抗变能力强\"）\n"
            f"- 应用1：**调节气候**（沿海地区昼夜温差<内陆地区）\n"
            f"- 应用2：**冷却剂**（汽车发动机用水循环散热）\n"
            f"- 应用3：**取暖**（热水袋/暖气用水）"
        )

    if "热机" in s:
        return (
            f"【{s}——把热变成动力】\n\n"
            f"汽车发动机是怎么让车轮转动的？它把燃料燃烧产生的**内能**转化成了**机械能**——这就是**热机**的工作原理。\n\n"

            f"**四冲程汽油机的工作循环**（一个循环活塞往复2次、曲轴转2周）：\n\n"
            f"| 冲程 | 活塞运动 | 气门状态 | 能量转化 |\n"
            f"|------|---------|----------|----------|\n"
            f"| 吸气冲程 | ↓ | 进气开 排气关 | 无（靠飞轮惯性完成）|\n"
            f"| 压缩冲程 | ↑ | 都关闭 | 机械能→内能（压缩气体）|\n"
            f"| **做功冲程** | ↓ | 都关闭 | **内能→机械能**（唯一对外做功的冲程）|\n"
            f"| 排气冲程 | ↑ | 排气开 进气关 | 无（靠飞轮惯性完成）|\n\n"
            f"⚠️ 记忆口诀：\"**一开一关向下吸，都关向上压，都关向下冲，一开一关向上排**\"\n\n"
            f"**热机效率**：η = W有用/Q放 × 100%（一般汽油机25-35%，柴油机35-45%）"
        )

    if "能量转化" in s or "守恒" in s:
        return (
            f"【{s}】\n\n"
            f"**能量守恒定律**：能量既不会凭空产生，也不会凭空消失，"
            f"它只会从一种形式转化为另一种形式，或者从一个物体转移到另一个物体，而在转化和转移过程中能量的总量保持不变。\n\n"
            f"这是自然界最普遍、最重要的基本定律之一！\n\n"
            f"常见能量转化实例：\n"
            f"- 发电机：**机械能 → 电能**\n"
            f"- 电动机：**电能 → 机械能**\n"
            f"- 热机（内燃机）：**化学能 → 内能 → 机械能**\n"
            f"- 光合作用：**光能 → 化学能**（储存在有机物中）\n"
            f"- 电池放电：**化学能 → 电能**\n\n"
            f"💡 第一类永动机不可能制成——因为它违背了能量守恒定律！"
        )

    # ═══════════════════════════════════════
    #  电学基础（每个子点独立）
    # ═══════════════════════════════════════
    if ("电荷" in s or "带电" in s) and "电流" not in s:
        return (
            f"【{s}】\n\n"
            f"塑料尺子跟头发摩擦后能吸引碎纸屑——这是因为尺子**带了电荷**（俗称\"带电了\"）。\n\n"

            f"**两种电荷**（富兰克林命名）：\n"
            f"- **正电荷(+)**：用丝绸摩擦过的玻璃棒带的电荷\n"
            f"- **负电荷(−)**：用毛皮摩擦过的橡胶棒带的电荷\n\n"
            f"**电荷间相互作用规律**：\n"
            f"- 同种电荷相互**排斥**（++相斥、−−相斥）\n"
            f"- 异种电荷相互**吸引**（+−相吸）\n"
            f"- 带电体还能吸引轻小物体（即使不带电）\n\n"
            f"**原子结构与带电本质**：\n"
            f"- 得电子 → 带负电（多余电子）\n"
            f"- 失电子 → 带正电（缺少电子）\n"
            f"- 摩擦起电的本质：**电子的转移**（不是创造了电荷！）\n\n"
            f"**电荷量单位**：库仑(C)。1个电子的电荷量 e = 1.6×10⁻¹⁹ C（元电荷）"
        )

    if "电路" in s and ("串" not in s and "并" not in s and "电流表" not in s and "电压" not in s) or ("电流" in s and "基" in s):
        return (
            f"【{s}】\n\n"
            f"什么是电路？简单说就是**电流走的路径**。\n\n"
            f"**电路的四个基本组成部分**：\n"
            f"1. **电源**：提供电能（电池/发电机），把其他形式的能转化为电能\n"
            f"2. **用电器**：消耗电能（灯泡/电动机/电铃），把电能转化为其他形式\n"
            f"3. **开关**：控制电路通断\n"
            f"4. **导线**：连接各元件形成闭合回路\n\n"
            f"**三种电路状态**：\n"
            f"- **通路（闭路）**：处处连通→有电流→用电器工作\n"
            f"- **断路（开路）**：某处断开→无电流→用电器不工作\n"
            f"- **短路**：电流不经过用电器直接从电源正极回到负极→**危险！**会烧坏电源甚至引起火灾\n\n"
            f"⚠️ 电路图规定符号要记牢：电池(长+短−)、电阻(矩形)、灯泡(圆圈叉)、开关(断开的线)、交叉相连(点)"
        )

    if any(k in s for k in ("串联","并联","串并联")):
        return (
            f"【{s}】\n\n"
            f"两个灯泡怎么接？有两种基本方式——**串联**和**并联**。\n\n"
            f"**串联电路**（像一根绳上的蚂蚱，首尾顺次连接）：\n"
            f"- 电流路径：**只有一条**（电流依次通过每个用电器）\n"
            f"- 特点：一处断开→整个电路都不通（\"一损俱损\"）\n"
            f"- 电流规律：**I = I₁ = I₂**（处处相等）\n"
            f"- 电压规律：**U = U₁ + U₂**（各用电器分压）\n"
            f"- 电阻规律：**R = R₁ + R₂**（越串越大）\n"
            f"- 例：装饰小彩灯（一颗坏了全串都不亮）\n\n"
            f"**并联电路**（像并排的两条路，并列连接在两点之间）：\n"
            f"- 电流路径：**有多条**（电流分流后再汇合）\n"
            f"- 特点：各支路**互不影响**（一支断了其他照常工作）\n"
            f"- 电流规律：**I = I₁ + I₂**（干路=各支路之和）\n"
            f"- 电压规律：**U = U₁ = U₂**（各支路等压）\n"
            f"- 电阻规律：1/R = 1/R₁ + 1/R₂（越并越小）\n"
            f"- 例：家庭电路（各电器独立工作）\n\n"
            f"💡 判断方法：看电流有没有\"分叉\"→分叉就是并联，不分叉就是串联"
        )

    if any(k in s for k in ("电流","电流强度")) and "电路" not in s and "磁" not in s and "表" not in s:
        return (
            f"【{s}】\n\n"
            f"电流就像水流一样——电荷的定向移动形成电流。\n\n"
            f"**定义**：**I = Q/t**（单位时间内通过导体横截面的电荷量）\n"
            f"- I：电流，单位 **A（安培）**\n"
            f"- Q：电荷量，单位 C（库仑）\n"
            f"- t：时间，单位 s（秒）\n\n"
            f"常用单位换算：\n"
            f"1 A = 1000 mA（毫安）= 10⁶ μA（微安）\n\n"
            f"**方向规定**：把**正电荷定向移动的方向**规定为电流方向。\n"
            f"（实际金属导体中是自由电子在移动，电子带负电→实际移动方向与电流方向**相反**）\n\n"
            f"常见电流大小参考：\n"
            f"- 电子计算器：~100μA\n"
            f"- 手电筒：~0.2A\n"
            f"- 家用节能灯：~0.1A\n"
            f"- 家用空调：~5-10A\n"
            f"- 高压输电线：几百~几千A"
        )

    # ═══════════════════════════════════════
    #  浮力
    # ═══════════════════════════════════════
    if any(k in s for k in("浮力","阿基米德","沉浮条件")):
        return (
            f"【{s}】\n\n"
            f"**浮力产生原因**：上下表面的压力差。\n\n"
            f"**阿基米德原理**：F浮 = G排 = ρ液 × g × V排\n\n"
            f"**物体的浮沉条件**（比较浮力和重力）：\n"
            f"- 上浮：F浮 > G（ρ物 < ρ液）\n"
            f"- 悬浮：F浮 = G（ρ物 = ρ液）\n"
            f"- 下沉：F浮 < G（ρ物 > ρ液）\n\n"
            f"💡 轮船利用**空心增大V排**来增大浮力；潜水艇靠**改变自身重力**实现上浮下沉。"
        )
    if any(k in s for k in("功","功率","机械效率","杠杆","滑轮","简单机械")):
        return (
            f"【{s}】\n\n"
            f"**功**：$W = Fs$（力×沿力方向的位移），单位 J（焦耳）\n\n"
            f"**功率**：$P = \\frac{{W}}{{t}}$，单位 W（瓦特），表示做功快慢\n\n"
            f"**杠杆平衡条件**：$F_1 L_1 = F_2 L_2$（动力×动力臂 = 阻力×阻力臂）\n\n"
            f"三种杠杆：省力杠杆（L₁>L₂）、费力杠杆（L₁<L₂，省距离）、等臂杠杆\n\n"
            f"**机械效率**：$\\eta = \\frac{{W_{{有用}}}}{{W_{{总}}}} × 100\\%$（永远<100%，因为额外功不可避免）"
        )
    if any(k in s for k in("电","电流","电压","电阻","欧姆","电路","串联","并联")):
        return (
            f"【{s}】\n\n"
            f"**三个基本量**：\n"
            f"- 电流 $I$：电荷定向移动（单位 A 安培）\n"
            f"- 电压 $U$：推动电流的动力（单位 V 伏特）\n"
            f"- 电阻 $R$：导体对电流的阻碍（单位 Ω 欧姆）\n\n"
            f"**欧姆定律**：$I = \\frac{{U}}{{R}}$（串联分压、并联分流）\n\n"
            f"**电功**：$W = UIt = \\frac{{U^2}}{{R}}t = I^2 Rt$（单位 kW·h 度）\n\n"
            f"**电功率**：$P = UI = I^2 R = \\frac{{U^2}}{{R}}$（单位 W）\n\n"
            f"**焦耳定律**（电热）：$Q = I^2 Rt$"
        )
    if any(k in s for k in("光","反射","折射","透镜","凸透镜","成像")):
        return (
            f"【{s}】\n\n"
            f"**光的直线传播**：同种均匀介质中沿直线传播（影子、日食月食）。\n"
            f"光速：真空中 $c = 3 × 10^8$ m/s\n\n"
            f"**反射定律**：反射角 = 入射角，三线共面。\n"
            f"平面镜成像：正立、等大、虚像，像距=物距。\n\n"
            f"**折射**：光从一种介质斜射入另一种介质时传播方向发生改变。\n\n"
            f"**凸透镜成像规律**：\n"
            f"- $u > 2f$：倒立缩小实像（照相机）\n"
            f"- $f < u < 2f$：倒立放大实像（投影仪）\n"
            f"- $u < f$：正立放大虚像（放大镜）"
        )
    if any(k in s for k in("热","温度","内能","比热","热机")) and "熔" not in s and "凝" not in s and "汽" not in s and "液" not in s and "升华" not in s:
        return (
            f"【{s}】\n\n"
            f"**温度**：分子平均动能的标志（单位 ℃/K）。\n"
            f"**内能**：物体内所有分子的动能和势能总和。改变方式：做功 / 热传递。\n\n"
            f"**比热容**：$c$ —— 1kg物质升高1℃吸收的热量。\n"
            f"$Q = cm\\Delta t$（水的$c = 4.2×10^3 J/(kg·℃)$很大→调节气候）\n\n"
            f"**热机**（内燃机）：化学能→内能→机械能。四个冲程：吸气→压缩→做功→排气。\n"
            f"**热值**：$q$ —— 1kg燃料完全燃烧放出的热量。Q放 = m × q"
        )

    # ═══════════════════════════════════════
    #  物态变化（每个子点独立）
    # ═══════════════════════════════════════
    if any(k in s for k in("熔化","凝固")):
        return (
            f"【{s}——固态⇌液态】\n\n"
            f"冰变成水、铁在高温下变成铁水——这些都是**熔化**（固态→液态）。反过来叫**凝固**。\n\n"

            f"**熔化和凝固的特点**：\n\n"
            f"| | 熔化 | 凝固 |\n"
            f"|---|------|------|\n"
            f"| 过程 | 固→液 | 液→固 |\n"
            f"| 吸/放热 | **吸热** | **放热** |\n"
            f"| 温度变化 | 晶体：不变（有熔点）非晶体：逐渐升高 | 晶体：不变 非晶体：逐渐降低 |\n\n"
            f"**晶体 vs 非晶体的关键区别**：\n"
            f"- **晶体**：有固定的**熔点**（如冰0℃、海波48℃、各种金属）\n"
            f"- **非晶体**：没有固定熔点（如玻璃、石蜡、沥青——慢慢变软变稀）\n\n"
            f"📐 熔化图像（晶体）：加热过程中温度先升→到熔点后保持不变（固液共存）→全部液化后继续升温。"
        )

    if any(k in s for k in("汽化","液化","蒸发","沸腾")):
        return (
            f"【{s}——液态⇌气态】\n\n"
            f"湿衣服晾干、水烧开后冒\"白气\"——这些都与液态和气态之间的转化有关。\n\n"

            f"**汽化**（液→气）有两种方式：\n\n"
            f"① **蒸发**：只在液体表面进行的缓慢汽化\n"
            f"- 任何温度下都能发生\n"
            f"- 影响因素：温度越高/表面积越大/表面空气流动越快→蒸发越快\n"
            f"- 蒸发**吸热**→有致冷作用（夏天洒水降温、皮肤上擦酒精感觉凉）\n\n"
            f"② **沸腾**：液体内部和表面同时进行的剧烈汽化\n"
            f"- 条件：达到**沸点**且**持续吸热**（两个条件缺一不可！）\n"
            f"- 沸腾时温度**保持在沸点不变**（虽然继续吸热）\n"
            f"- 标准大气压下水的沸点=**100℃**；气压越低沸点越低（高原煮不熟饭→用高压锅）\n\n"
            f"**液化**（气→液）的两种方法：\n"
            f"1. **降低温度**（所有气体降到足够低都能液化）\n"
            f"2. **压缩体积**（常温下可液化某些气体，如液化石油气、打火机燃气）\n\n"
            f"⚠️ \"白气\"不是气体！是水蒸气遇冷**液化**成的小水滴。"
        )

    if any(k in s for k in ("升华","凝华")):
        return (
            f"【{s}——固态⇌气态】\n\n"
            f"冬天冰冻的衣服也能干（冰直接变成水蒸气）→ **升华**\n"
            f"霜的形成（水蒸气直接变成冰晶）→ **凝华**\n\n"
            f"**升华**：固态→气态，**吸热**\n"
            f"- 例：樟脑丸变小、干冰（固态CO₂）用于舞台烟雾、灯泡用久了内壁变黑（钨升华）\n\n"
            f"**凝华**：气态→固态，**放热**\n"
            f"- 例：霜、雾凇、窗户上的冰花（室内水蒸气遇到冷玻璃凝华）\n\n"
            f"💡 记忆口诀：\"升华凝华跳过液态，一吸一放要分清\""
        )

    # ═══════════════════════════════════════
    #  功/功率/机械能（每个子点独立）
    # ═══════════════════════════════════════
    if ("功" in s or "做功") and "机械效率" not in s and "杠杆" not in s and "滑轮" not in s:
        return (
            f"【{s}】\n\n"
            f"你提着水桶站在原地不动——累吗？累！但物理学说你对水桶**没有做功**。\n"
            f"为什么？因为功的两个必要条件缺一个：物体要在**力的方向上移动距离**。\n\n"

            f"**做功的两个必要条件**（缺一不可）：\n"
            f"1. 作用在物体上的**力**（F）\n"
            f"2. 物体在这个力的方向上通过的距离**（s）**\n\n"

            f"公式：**W = Fs**\n"
            f"- W：功（单位 **J 焦耳**）\n"
            f"- F：力（N）\n"
            f"- s：在力的方向上移动的距离（m）\n\n"
            f"三种不做功的情况：\n"
            f"❶ 有力无距（F≠0, s=0）：推墙没推动 → 不做功\n"
            f"❷ 有距无力（F=0, s≠0）：靠惯性运动 → 不做功\n"
            f"❸ 力与距垂直：提着水桶水平走 → 支持力不做功（支持力↑，位移⊥）\n"
            f"\n"
            f"**功率 P = W/t** —— 表示做功快慢（单位 W 瓦特），1kW = 1000W"
        )

    if "杠杆" in s and "平衡" not in s and "滑" not in s and "效" not in s:
        return (
            f"【{s}】\n\n"
            f"一根硬棒，在力的作用下能绕固定点转动——这就是**杠杆**。生活中到处都是杠杆：\n\n"
            f"杠杆的五要素：\n"
            f"- **支点O**：杠杆绕着转动的固定点\n"
            f"- **动力F₁**：使杠杆转动的力\n"
            f"- **阻力F₂**：阻碍杠杆转动的力\n"
            f"- **动力臂L₁**：从支点到动力作用线的**垂直距离**\n"
            f"- **阻力臂L₂**：从支点到阻力作用线的**垂直距离**\n\n"
            f"⚠️ 力臂**不是**支点到作用点的距离！是到**作用线**（延长线）的垂距！\n\n"
            f"三类杠杆对比：\n"
            f"| 类型 | L₁与L₂关系 | 特点 | 实例 |\n"
            f"|------|-----------|------|------|\n"
            f"| 省力杠杆 | L₁ > L₂ | 省力费距离 | 开瓶器、铡刀、羊角锤 |\n"
            f"| 费力杠杆 | L₁ < L₂ | 费力省距离 | 筷子、钓鱼竿、镊子 |\n"
            f"| 等臂杠杆 | L₁ = L₂ | 不省力不费力 | 天平、跷跷板 |"
        )

    if "平衡" in s or ("杠" in s and "平衡" in s):
        return (
            f"【{s}】\n\n"
            f"杠杆平衡条件（也叫杠杆原理）：\n\n"
            f"**F₁ × L₁ = F₂ × L₂**\n\n"
            f"(动力×动力臂 = 阻力×阻力臂)\n\n"
            f"应用：\n"
            f"1. **求未知力或力臂**：知道三个量就能算出第四个\n"
            f"   例：L₁=2m, F₁=10N, L₂=0.5m → F₂ = (10×2)/0.5 = **40N**\n\n"
            f"2. **判断杠杆状态**：\n"
            f"   - F₁L₁ > F₂L₂ → 向F₁那端倾斜（打破平衡）\n"
            f"   - F₁L₁ = F₂L₂ → 平衡\n"
            f"   - F₁L₁ < F₂L₂ → 向F₂那端倾斜\n\n"
            f"💡 杠杆平衡实验中，使杠杆在**水平位置平衡**的好处：\n"
            f"方便直接从杠杆上读出力臂（此时力臂与杆重合）"
        )

    if "滑轮" in s:
        return (
            f"【{s}】\n\n"
            f"滑轮是周边有槽、能绕轴转动的圆轮。分为两种：\n\n"
            f"**① 定滑轮**（轴固定不动）：\n"
            f"- 本质：等臂杠杆（L₁=L₂=R）\n"
            f"- 特点：**不省力也不费力**，但可以**改变力的方向**\n"
            f"- 升国旗用的就是定滑轮\n\n"
            f"**② 动滑轮**（轴随物体一起运动）：\n"
            f"- 本质：动力臂是阻力臂2倍的杠杆（L₁=2R, L₂=R）\n"
            f"- 特点：**省一半力**（忽略滑轮重和摩擦时 F=G/2），但**费一倍距离**\n"
            f"- 不能改变力的方向\n\n"
            f"**③ 滑轮组**（定+动组合）：\n"
            f"省力情况看承担物重的绳子段数 n：F = G物+G动 / n\n"
            f"绳子自由端移动的距离：s = n × h（h为物体上升高度）\n\n"
            f"⚠️ 绳子段数n怎么数：看有几段绳子**直接拉着动滑轮和物体**！"
        )

    if "机械效率" in s or "效率" in s:
        return (
            f"【{s}】\n\n"
            f"用滑轮组提起重物时，你实际做的总功总是比有用功多——因为还要克服摩擦、提升动滑轮本身……\n"
            f"这就引出了**机械效率**的概念。\n\n"
            f"三个重要概念：\n"
            f"- **有用功 W有**：对我们有用的功（对滑轮组：W有 = G×h）\n"
            f"- **额外功 W额**：不得不做但对目的无用的功（克服摩擦、提升动滑轮）\n"
            f"- **总功 W总**：W总 = W有 + W额（实际做的全部功）\n\n"
            f"**机械效率公式**：\n"
            f"$\\eta = \\frac{{W_{{有}}}}{{W_{{总}}}} × 100\\%$\n\n"
            f"⚠️ 机械效率永远**小于100%**（因为额外功不可避免！）\n"
            f"提高效率的方法：减小摩擦（加润滑油）、减轻动滑轮重量\n\n"
            f"例：用滑轮组提起200N的重物升高2m，拉力80N拉了6m\n"
            f"W有=200×2=400J, W总=80×6=480J → η=400/480×100% = **83.3%**"
        )

    if any(k in s for k in ("动能","势能","机械能")):
        return (
            f"【{s}】\n\n"
            f"飞行的子弹能击穿木板——因为它有**动能**；高处的水能推动发电机——因为它有**重力势能**。\n\n"
            f"**动能 E_k = ½mv²**：\n"
            f"- 与质量**成正比**，与速度的**平方**成正比\n"
            f"- 速度影响更大！速度翻倍→动能变4倍\n\n"
            f"**重力势能 E_p = mgh**：\n"
            f"- 与质量和高度都有关（h是相对参考平面的高度）\n\n"
            f"**弹性势能**：与形变程度有关（弓拉得越满势能越大）\n\n"
            f"**机械能守恒**（只有重力/弹力做功时）：\n"
            f"E_k + E_p = 常量（动能和势能互相转化但总量不变）\n"
            f"- 过山车：最高处势能最大动能最小→最低处动能最大势能最小\n"
            f"- 单摆/秋千：同理"
        )

    # ==================== 高中物理 ====================
    # ---- 原子物理 ----
    if any(k in s for k in ("核式",)) or s == "原子结构":
        return (
            "【" + s + "——原子结构】\n\n"
            "**α粒子散射实验（卢瑟福）**：绝大多数α粒子穿过金箔，少数大角度偏转，极少数被反弹。\n"
            "→ 结论：原子的中心有一个很小的**核**，集中了全部正电荷和几乎全部质量。\n\n"
            "**核式结构模型**：原子中心是带正电的原子核，电子在核外绕核运动（类似行星绕太阳）。\n"
            "→ 但该模型无法解释原子的稳定性（按经典理论电子会坠入原子核！）\n\n"
            "**原子的组成**：原子核由质子(正电)和中子(不带电)组成；核外电子在特定轨道/区域运动\n"
            "- 原子序数 = 质子数 = 核外电子数\n"
            "- 质量数 A = 质子数 Z + 中子数 N\n"
            "- 同位素：质子数相同、中子数不同的同一元素的不同原子（如 $^{12}C$、$^{13}C$、$^{14}C$）"
        )
    if any(k in s for k in ("玻尔", "能级", "光谱", "跃迁")):
        return (
            "【" + s + "——原子结构】\n\n"
            "**α粒子散射实验（卢瑟福）**：绝大多数α粒子穿过金箔，少数大角度偏转，极少数被反弹。\n"
            "→ 结论：原子的中心有一个很小的**核**，集中了全部正电荷和几乎全部质量。\n\n"
            "**核式结构模型**：原子中心是带正电的原子核，电子在核外绕核运动（类似行星绕太阳）。\n"
            "→ 但该模型无法解释原子的稳定性（按经典理论电子会坠入原子核！）\n\n"
            "**玻尔模型（三点假设）**：\n"
            "① 电子只能在一系列**不连续的定态轨道**上运动（轨道量子化 $r_n = n^2 r_1$）\n"
            "② 定态轨道上电子不辐射能量（能量量子化 $E_n = E_1/n^2$）\n"
            "③ 电子在轨道间**跃迁**时吸收或发射光子：$h\\nu = E_m - E_n$\n\n"
            "⚠️ 玻尔模型成功解释了氢原子光谱，但对多电子原子不适用——需要量子力学。"
        )
    if any(k in s for k in ("放射性", "衰变", "α衰变", "β衰变", "半衰期", "射线")):
        return (
            "【" + s + "——放射性】\n\n"
            "**天然放射性的三种射线**：\n"
            "- **α射线**：氦核($_{2}^{4}He$)，电离能力强，穿透力弱（纸可挡住）\n"
            "- **β射线**：高速电子流($_{-1}^{0}e$)，电离能力较弱，穿透力较强（铝板可挡）\n"
            "- **γ射线**：高频电磁波（光子），电离能力最弱，穿透力最强（需厚铅板或混凝土）\n\n"
            "**衰变规律**：\n"
            "α衰变：$_{Z}^{A} X \\to _{Z-2}^{A-4} Y + _{2}^{4} He$（质量数减4、电荷数减2）\n"
            "β衰变：$_{Z}^{A} X \\to _{Z+1}^{A} Y + _{-1}^{0} e$（质量数不变、电荷数加1）\n\n"
            "**半衰期 $T_{1/2}$**：放射性元素的原子核有半数发生衰变所需的时间。\n"
            "$N = N_0 (\\frac{1}{2})^{t/T_{1/2}}$ —— 半衰期由核内部决定，与温度/压强/化学状态无关！\n"
            "💡 应用：碳-14测年（$T_{1/2}$≈5730年）、医疗诊断、无损探伤。"
        )
    if any(k in s for k in ("核反应", "裂变", "聚变", "核电站", "质能方程", "结合能", "核能")):
        return (
            "【" + s + "——核反应与核能】\n\n"
            "**爱因斯坦质能方程**：$E = mc^2$（$c = 3×10^8$m/s）\n"
            "→ 质量亏损 $\\Delta m$ 对应释放的能量 $\\Delta E = \\Delta m · c^2$\n"
            "即使很小的质量损失也能释放巨大能量！\n\n"
            "**核裂变（Fission）**：重核分裂为中等质量的核\n"
            "- 例：$_{92}^{235}U + _{0}^{1} n \\to _{56}^{141}Ba + _{36}^{92}Kr + 3_{0}^{1} n$\n"
            "- 条件：铀块体积≥**临界体积**（链式反应可持续）\n"
            "- 应用：**核电站**（用控制棒吸收中子来控制反应速率）、原子弹（不可控）\n\n"
            "**核聚变（Fusion）**：轻核聚合成较重的核（需超高温~$10^8$K）\n"
            "- 例：$_{1}^{2}H + _{1}^{3}H \\to _{2}^{4}He + _{0}^{1} n$（氘+氚→氦+中子+能量）\n"
            "- 优势：同质量下聚变释放的能量约为裂变的**4倍**；原料（氘）来自海水，几乎取之不尽\n"
            "- 应用：**氢弹**、太阳及恒星的能源（可控聚变仍在研究中）\n\n"
            "**平均结合能曲线**：铁附近的核平均结合能最大→中等质量核最稳定\n"
            "→ 重核裂变和轻核聚变都能释放核能（都朝着更稳定的方向走）。"
        )

    # ---- 电磁学（高中）----
    if any(k in s for k in ("电场", "场强", "电势", "电容", "匀强电场", "点电荷")):
        return (
            "【" + s + "——电场】\n\n"
            "**电场强度 $E$**：描述电场力的性质的物理量，$E = F/q$（单位 N/C 或 V/m）\n"
            "点电荷：$E = kQ/r^2$（$k = 9×10^9$ N·m²/C²）\n\n"
            "**电势 $\\varphi$**：描述电场能的性质，$\\varphi = E_p/q$（单位 V 伏特）\n"
            "沿电场线方向电势降低！等势面与电场线垂直。\n\n"
            "**电势差(电压) $U_{AB}$**：$U_{AB} = \\varphi_A - \\varphi_B = W_{AB}/q$\n"
            "匀强电场中：$U = Ed$（d 为沿场方向的距离）\n\n"
            "**电容 $C$**：$C = Q/U$（单位 F 法拉），平行板电容器：$C = \\varepsilon S / (4\\pi kd)$\n"
            "💡 带电粒子在电场中的运动：加速（动能定理 $qU = \\Delta E_k$）、偏转（类平抛）"
        )
    if any(k in s for k in ("磁场", "磁感应强度", "安培力", "洛伦兹力", "左手定则")):
        return (
            "【" + s + "——磁场】\n\n"
            "**磁感应强度 B**：描述磁场强弱和方向的物理量（单位 T 特斯拉）\n"
            "定义：$B = F/(IL)$（通电导线垂直于磁场时）\n\n"
            "**安培力**：$F = BIL\\sin\\theta$（$\\theta$ 为电流方向与B的夹角）\n"
            "方向判断：**左手定则**——伸开左手，磁感线穿掌心，四指指向电流方向，拇指指向安培力方向\n\n"
            "**洛伦兹力**：$f = qvB\\sin\\theta$（电荷在磁场中受力）\n"
            "特点：**不做功！**（因为f始终⊥于v）→ 只改变速度方向，不改变速度大小\n"
            "→ 带电粒子在匀强磁场中做**匀速圆周运动**：$qvB = mv^2/r → r = mv/(qB)$\n"
            "周期 $T = 2\\pi m/(qB)$（与速度无关！）\n\n"
            "💡 应用：质谱仪（分离不同质量的离子）、回旋加速器（利用周期不变性）"
        )
    if any(k in s for k in ("电磁感应", "法拉第", "感应电流", "楞次", "自感", "互感")):
        return (
            "【" + s + "——电磁感应】\n\n"
            "**法拉第电磁感应定律**：$\\mathcal{E} = n \\frac{\\Delta \\Phi}{\\Delta t}$\n"
            "（$n$为线圈匝数，$\\Phi$为磁通量 $\\Phi = BS\\sin\\theta$）\n\n"
            "**楞次定律**：感应电流的磁场总是**阻碍**引起感应电流的磁通量变化\n"
            '口诀："增反减同"、"来拒去留"\n\n'
            "**导体切割磁感线**：$E = BLv$（B⊥L⊥v 时）\n"
            "右手定则判断感应电流方向\n\n"
            "**自感现象**：线圈自身电流变化产生的感应电动势 $\\mathcal{E}_L = L \\frac{\\Delta I}{\\Delta t}$\n"
            "通电自感（阻碍电流增大→灯泡渐亮）/ 断电自感（阻碍电流减小→闪亮后熄灭）\n"
            "💡 应用：变压器（$U_1/U_2 = n_1/n_2$）、发电机、电磁阻尼"
        )

    # ---- 力学进阶（高中）----
    if any(k in s for k in ("动量", "冲量", "动量定理", "动量守恒")):
        return (
            f"【{s}——动量】\n\n"
            f"**动量 $p = mv$**：矢量，方向与速度相同，单位 kg·m/s\n"
            f"**冲量 $I = Ft$**：力对时间的积累效应，矢量\n\n"
            f"**动量定理**：合外力的冲量等于物体动量的变化量\n"
            f"$Ft = \\Delta p = mv_2 - mv_1$ → 可求变力作用下的速度变化\n\n"
            f"**动量守恒定律**：系统不受外力或所受合外力为零时，系统总动量保持不变\n"
            f"$m_1 v_1 + m_2 v_2 = m_1 v'_1 + m_2 v'_2$\n"
            f"适用条件：①系统合外力为零 ②内力远大于外力 ③某方向合外力为零\n\n"
            f"💡 应用：碰撞（弹性/非弹性/完全非弹性）、反冲火箭、爆炸"
        )
    if any(k in s for k in ("圆周运动", "向心力", "向心加速度", "离心", "角速度")):
        return (
            f"【{s}——圆周运动】\n\n"
            f"**线速度 $v$**：沿切线方向，$v = \\Delta s / \\Delta t$\n"
            f"**角速度 $\\omega$**：$\\omega = \\Delta\\theta / \\Delta t$（rad/s），$v = \\omega r$\n\n"
            f"**向心加速度 $a_n$**：$a_n = v²/r = \\omega² r$（始终指向圆心）\n"
            f"**向心力 $F_n$**：$F_n = ma_n = mv²/r = m\\omega²r$（不是一种新力，是指向圆心的合力！）\n\n"
            f"常见向心力来源：绳拉力、摩擦力、重力+支持力的合力、万有引力\n\n"
            f"⚠️ 竖直平面内的圆周运动：最高点的临界条件（绳模型 $v ≥ \\sqrt{{gr}}$ / 杆模型 $v > 0$）"
        )
    if any(k in s for k in ("万有引力", "引力", "卫星", "环绕速度", "宇宙速度")):
        return (
            f"【{s}——万有引力】\n\n"
            f"**万有引力定律**：$F = G\\frac{{Mm}}{{r²}}$（$G = 6.67×10^{-11}$ N·m²/kg²）\n"
            f"适用于质点或均匀球体（r取球心距离）\n\n"
            f"**天体运动的向心力 = 万有引力**：\n"
            f"$G\\frac{{Mm}}{{r²}} = m\\frac{{v²}}{{r}} = m\\omega²r = m(\\frac{{2\\pi}}{{T}})²r$\n\n"
            f"**三个宇宙速度**：\n"
            f"第一宇宙速度（环绕）：$v_1 = \\sqrt{{gR}} ≈ 7.9$ km/s（近地卫星）\n"
            f"第二宇宙速度（脱离）：$v_2 ≈ 11.2$ km/s（脱离地球引力）\n"
            f"第三宇宙速度（逃逸）：$v_3 ≈ 16.7$ km/s（脱离太阳系）\n\n"
            f"💡 同步卫星：$T = 24$h，轨道在赤道平面，高度约36000km，$v ≈ 3.1$ km/s"
        )

    # ---- 光学与近代物理（高中）----
    if any(k in s for k in ("光电效应", "光子", "逸出功", "普朗克", "康普顿", "波粒二象性")):
        return (
            f"【{s}——光的本性与量子论】\n\n"
            f"**光电效应实验**（无法用波动说解释的四条现象）：\n"
            f"① 存在截止频率 $\\nu_0$（低于此频率无论多强都不产生光电子）\n"
            f"② 瞬时性（< $10^{-9}s$）\n"
            f"③ 最大初动能只与频率有关，与光强无关\n"
            f"④ 饱和光电流与光强成正比\n\n"
            f"**爱因斯坦光电效应方程**：$E_k = h\\nu - W_0$\n"
            f"（$h = 6.63×10^{-34}$ J·s 普朗克常量；$W_0$ 为逸出功；$h\\nu_0 = W_0$ 截止频率）\n\n"
            f"**光的波粒二象性**：光既有波动性（干涉/衍射/偏振）又有粒子性（光电效应）\n"
            f"$p = h/\\lambda$（德布罗意关系——实物粒子也有波动性！）\n"
            f"💡 物质波的波长 $\\lambda = h/p = h/(mv)$——宏观物体波长太短观察不到"
        )

    # 物理兜底
    return (
        f"【{s}——物理学要点】\n\n"
        f"学习{t}中的{s}时，要把握以下几点：\n\n"
        f"1. **理解物理量的含义**：不要死记公式，先弄清每个符号代表什么\n"
        f"2. **注意单位换算**：国际单位制（SI）要牢记\n"
        f"3. **画图分析**：受力分析图、光路图、电路图帮助理清思路\n"
        f"4. **联系生活现象**：惯性、浮力、光的折射在生活中随处可见\n"
        f"5. **重视实验**：亲手操作比看书印象深刻得多"
    )


def _gen_chem_content(t, s):
    """化学学科智能内容引擎 —— 每个子点独立、详细、像真人老师讲课"""
    
    # ═══════════════════════════════════════
    #  分子与原子（两个概念的区别和联系）
    # ═══════════════════════════════════════
    if any(k in s for k in("分子", "分子原子")) and "离子" not in s and "结构" not in s:
        return (
            f"【{s}——从微观世界认识物质】\n\n"
            f"想象一下，如果你把一块糖不停地切、切、切……切到不能再切为止，剩下的那个\"最小单元\"就是**糖分子**。"
            f"而如果把分子再拆开，就得到**原子**了。这就是分子和原子的第一层关系：**分子可以再分，原子是化学变化中的最小粒子**。\n\n"

            f"**📖 一、什么是分子？**\n\n"
            f"分子是**保持物质化学性质的最小粒子**。注意三个关键词：\n"
            f"- \"保持\"：分子不变，物质的化学性质就不变（液态水、冰、水蒸气的分子都是H₂O，化学性质相同）\n"
            f"- \"化学性质\"：不是物理性质！比如氧气变成液氧，分子没变→化学性质没变，但颜色/状态变了（那是物理性质）\n"
            f"- \"最小\"：再分就不是这个物质了（H₂O分子拆开→变成H和O，不再是水）\n\n"

            f"分子的特点：**质量小、体积小、不断运动、有间隔**。\n"
            f"💡 生活证据：\n"
            f"- 闻到花香 → 花香分子运动到你的鼻子里\n"
            f"- 湿衣服晾干 → 水分子运动到空气中去了\n"
            f"- 50mL水 + 50mL酒精 ≠ 100mL → 分子之间有间隔，互相\"挤\"进去了\n"
            f"- 热胀冷缩 → 温度高→分子间隔变大（分子本身大小不变！）\n\n"

            f"**📖 二、什么是原子？**\n\n"
            f"原子是**化学变化中的最小粒子**。在化学反应中，分子分裂成原子，原子重新组合成新分子。"
            f"原子本身在化学变化中不再分（否则就是核反应了，那不是普通化学反应）。\n\n"

            f"**📖 三、分子与原子的联系与区别**\n\n"
            f"| 对比项 | 分子 | 原子 |\n"
            f"|--------|------|------|\n"
            f"| 定义 | 保持物质**化学性质**的最小粒子 | 化学变化中的**最小粒子** |\n"
            f"| 能否再分 | 化学**变化**中可分 | 化学**变化**中不可分 |\n"
            f"| 构成关系 | 由原子构成 | 由质子+中子+电子构成 |\n"
            f"| 表示 | 用**化学式**（如 H₂O、O₂） | 用**元素符号**（如 Fe、He） |\n\n"

            f"⚠️ 易错提醒：不是所有物质都由分子构成！\n"
            f"- 金属（Fe、Cu）→ 直接由**原子**构成\n"
            f"- 金刚石、硅 → 直接由**原子**构成\n"
            f"- NaCl（食盐）→ 由**离子**构成（后面会学到）\n"
            f"- 只有少数非金属单质（O₂、N₂、H₂、H₂O、CO₂等）才由**分子**构成"
        )

    # ═══════════════════════════════════════
    #  原子结构（深入到电子层/核电荷）
    # ═══════════════════════════════════════
    if ("原子结构" in s) or (("原子" in s) and ("结构" in s or "核" in s or "构成" in s)):
        return (
            f"【{s}——原子的内部世界】\n\n"
            f"一个原子的直径大约是 **10⁻¹⁰ 米**（0.1纳米），小到你根本看不见。"
            f"但就是这个微小的粒子，内部却有一个完整的\"宇宙\"！让我们一层层剥开看。\n\n"

            f"**🔬 一、原子的诞生——α粒子散射实验（1909年）**\n\n"
            f"英国科学家卢瑟福做了一个著名的实验：用带正电的α粒子（氦核）去轰击一片极薄的金箔。\n"
            f"他发现了三种现象：\n"
            f"- 绝大多数α粒子**穿过金箔，方向不变**（说明原子内部大部分是空的！）\n"
            f"- 少数粒子**偏转了较大角度**（说明原子中心有一个带正电的、很小的\"核\"）\n"
            f"- **极个别**粒子被**反弹回来**（说明这个核质量很大、体积很小但集中了全部正电荷）\n\n"
            f"💡 这个实验彻底推翻了之前的\"西瓜模型\"（汤姆逊认为电子嵌在正电荷球体里），"
            f"提出了**核式结构模型**——就像太阳系：原子核=太阳，电子=行星绕着转。\n\n"

            f"**⚛️ 二、原子核的结构**\n\n"
            f"原子核由两种粒子组成：\n\n"
            f"| 粒子 | 电荷 | 质量（相对） | 位置 |\n"
            f"|------|------|-------------|------|\n"
            f"| **质子** | +1（1个单位正电荷） | ≈1 | 原子核内 |\n"
            f"| **中子** | 不带电（电中性） | ≈1 | 原子核内 |\n"
            f"| **电子** | −1（1个单位负电荷） | ≈1/1836（极轻！） | 核外空间 |\n\n"
            f"关键数字：整个原子的质量几乎全集中在原子核（99.9%以上），但核的直径只有原子直径的 **1/10万**！"
            f"如果把原子放大到一个足球场那么大，原子核只有一粒沙子那么大！\n\n"

            f"**🔢 三、三个核心数量关系（必背！）**\n\n"
            f"① **质子数 = 核外电子数 = 原子序数（= 核电荷数）**\n"
            f"   → 原子整体呈**电中性**（正负电荷抵消）\n"
            f"   → 原子序数 = 元素周期表中的序号\n\n"
            f"② **相对原子质量 ≈ 质子数 + 中子数**\n"
            f"   → 电子太轻，忽略不计\n"
            f"   例：氧原子(₈¹⁶O) → 质子数=8，相对原子质量≈16 → 中子数=16−8=**8**\n\n"
            f"③ **核外电子分层排布**：\n"
            f"   第一层最多2个电子，第二层最多8个，第三层最多18个（但最外层不超过8个）\n"
            f"   → 最外层电子数决定元素的**化学性质**！"
        )

    # ═══════════════════════════════════════
    #  元素（定义、分类、与原子的区别）
    # ═══════════════════════════════════════
    if ("元素" in s) and ("周期表" not in s) and ("结构" not in s) and ("分子" not in s):
        return (
            f"【{s}——给原子\"贴标签\"】\n\n"
            f"世界上有112种以上的已知元素（自然界94种+人工合成18种+），"
            f"但它们组成的物质却有**几千万种**！这就像26个英文字母能组成无数单词一样。\n"
            f"**元素**，就是给原子按\"身份\"分的类。\n\n"

            f"**📌 一、元素的定义（考试重点）**\n\n"
            f"**元素是具有相同质子数（即核电荷数）的一类原子的总称。**\n\n"
            f"这句话有三个关键点要理解：\n\n"
            f"1. **\"相同质子数\"**：这是唯一的分类标准！"
            f"只要质子数相同就是同一种元素，不管中子数多少、不管它是以什么形态存在。\n\n"
            f"2. **\"一类原子的总称\"**：元素是一个**宏观概念**，只讲种类不讲个数！"
            f"你可以说\"水是由氢元素和氧元素组成的\"（✅对），但不能说\"水是由两个氢元素和一个氧元素构成的\"（❌错）。"
            f"说个数的时候要用\"原子\"！\n\n"
            f"3. **元素 vs 原子的区别**（必考辨析）：\n"
            f"| | 元素 | 原子 |\n"
            f"|---|------|------|\n"
            f"| 层次 | **宏观**（物质由什么元素组成） | **微观**（分子由什么原子构成） |\n"
            f"| 有无个数 | 只讲**种**类，不讲个数 | 既讲种类也讲**数**量 |\n"
            f"| 举例 | 水由氢、氧**元素**组成 | 1个水分子含2个氢**原子**和1个氧**原子** |\n\n"

            f"**🏷️ 二、元素符号——化学的\"字母表\"**\n\n"
            f"每种元素都有一个国际通用的符号（通常1~2个字母）：\n"
            f"- 一个大写字母：H(氢)、C(碳)、O(氧)、N(氮)、S(硫)、P(磷)\n"
            f"- 两个字母（第一个大写、第二个小写）：Na(钠)、Ca(钙)、Fe(铁)、Cu(铜)、Al(铝)\n\n"
            f"⚠️ 常见错误：把\"CO\"写成\"Co\"——CO是一氧化碳（C+O两个原子），"
            f"Co是金属钴（一种元素）！第二个字母必须小写！\n\n"

            f"**📊 三、元素分类**\n\n"
            f"1. **金属元素**（汉字带\"钅\"旁，汞除外）：Fe、Cu、Zn、Al、Na…（共90多种）\n"
            f"2. **非金属元素**：\n"
            f"   - 固态非金属（\"石\"旁）：C、S、P\n"
            f"   - 气态非金属（\"气\"旁）：H、O、N、Cl（氯）\n"
            f"   - 液态非金属：Br（溴）\n"
            f"3. **稀有气体元素**（\"气\"字头）：He、Ne、Ar（最外层电子已满，一般不反应）"
        )

    # ═══════════════════════════════════════
    #  离子（形成、分类、与原子的区别）
    # ═══════════════════════════════════════
    if "离子" in s:
        return (
            f"【{s}——带电的原子/原子团】\n\n"
            f"先想一个问题：为什么NaCl（食盐）能稳定存在？钠原子最外层1个电子，"
            f"氯原子最外层7个电子——它们都不\"满足\"，都想达到稳定结构（最外层8电子）。"
            f"怎么办？**钠把电子给了氯！** 于是钠变成了带正电的**阳离子**，氯变成了带负电的**阴离子**，"
            f"正负相吸→形成了稳定的NaCl。这就是离子的由来。\n\n"

            f"**⚡ 一、离子的定义**\n\n"
            f"**离子是带电荷的原子或原子团。**\n\n"
            f"原子本来电中性（质子数=电子数），但如果**得到或失去电子**，"
            f"电子数就不等于质子数了→原子就带了电→变成了**离子**。\n\n"
            f"**⚡ 二、离子的形成规律（背下来！）**\n\n"
            f"| 原子类型 | 最外层电子数 | 趋向 | 变成的离子 | 实例 |\n"
            f"|----------|------------|------|-----------|------|\n"
            f"| 金属原子 | 一般<4 | **失去**电子 | 阳离子(+) | Na→Na⁺(失1e⁻) |\n"
            f"| 非金属原子 | 一般≥4 | **得到**电子 | 阴离子(−) | Cl→Cl⁻(得1e⁻) |\n"
            f"| 稀有气体 | 8个(或He的2个) | **不易得失** | 一般不形成离子 | He、Ne、Ar |\n\n"
            f"记忆口诀：**\"金失非得\"**——金属**失**去电子，非金属**得**到电子。\n\n"

            f"**📝 三、离子符号的书写（必考技能）**\n\n"
            f"写在元素符号**右上角**：先写数字、再写正负号（数字为1时省略）。\n\n"
            f"正确示例：\n"
            f"- Na⁺ （钠离子：失1个电子，带1个单位正电荷）\n"
            f"- Mg²⁺（镁离子：失2个电子，带2个单位正电荷）\n"
            f"- Cl⁻ （氯离子：得1个电子，带1个单位负电荷）\n"
            f"- O²⁻（氧离子：得2个电子，带2个单位负电荷）\n"
            f"- SO₄²⁻（硫酸根离子：原子团带电）\n\n"
            f"❌ 常见错误：\n"
            f"- 写成 Na⁺¹（数字应在正号**前面**）\n"
            f"- 写成 Ca²⁺（上标不能写2+，必须是²⁺）\n"
            f"- 把离子电荷写成化合价（位置不同！化合价写正上方，离子写右上角）\n\n"

            f"**🔄 四、离子与原子的转化**\n\n"
            f"阳离子 + 电子 → 原子（例：Fe³⁺ + 3e⁻ → Fe）\n"
            f"阴离子 − 电子 → 原子（例：O²⁻ − 2e⁻ → O）\n\n"
            f"💡 关系总结：**原子 ⇄ 离子**（通过得失电子相互转化），但它们的**元素种类没有变**！"
            f"Na和Na⁺都是钠元素，只是带电状态不同。"
        )

    # ═══════════════════════════════════════
    #  元素周期表（结构、规律、如何使用）
    # ═══════════════════════════════════════
    if "周期表" in s or ("周期" in s and "元素" in s):
        return (
            f"【{s}——元素的\"家族谱\"】\n\n"
            f"1869年，俄国化学家门捷列夫做了一件了不起的事：他把当时已知的63种元素"
            f"按照**原子量从小到大**排列，发现元素的性质呈**周期性变化**！"
            f"他甚至大胆地给还没发现的元素**留出了空位**并预言了它们的性质——后来这些预言全部被证实了！"
            f"这就是**元素周期表**的由来。\n\n"

            f"**📊 一、周期表的完整结构**\n\n"
            f"想象一张大表格：\n\n"
            f"**横行 = 周期（Period）**：共7个周期\n"
            f"- 第1周期：2种元素（H、He）—— 只有1个电子层\n"
            f"- 第2、3周期：各8种元素 —— 称为\"短周期\"\n"
            f"- 第4、5、6周期：各18种元素 —— 称为\"长周期\"\n"
            f"- 第7周期：未排满（人造元素还在增加中）\n\n"
            f"**规律：周期数 = 该周期元素原子的电子层数**\n"
            f"（第3周期的元素都有3个电子层）\n\n"
            f"**纵列 = 族（Group）**：共18个纵列/16个族\n"
            f"- 第1、2列：IA、IIA族（碱金属、碱土金属）\n"
            f"- 第3~7列：IIIB~VIIB族（过渡金属为主）\n"
            f"- 第8~10列：VIII族（第8、9、10三列合称）\n"
            f"- 第11、12列：IB、IIB族\n"
            f"- 第13~17列：IIIA~VIIA族\n"
            f"- 第18列：**0族**（稀有气体）\n\n"
            f"**规律：主族序数 = 最外层电子数**（主族元素）\n"
            f"(IA族最外层1个电子，VIIA族最外层7个电子)\n\n"

            f"**📈 二、元素周期律（核心规律）**\n\n"
            f"**同一周期（从左到右）**：\n"
            f"- 原子半径 **逐渐减小** ← 核电荷↑，对外层电子吸引力↑\n"
            f"- 金属性 **逐渐减弱**，非金属性 **逐渐增强**\n"
            f"- 最高正价 = 族序数（O、F除外）\n\n"
            f"**同一主族（从上到下）**：\n"
            f"- 原子半径 **逐渐增大** ← 电子层数↑\n"
            f"- 金属性 **逐渐增强**，非金属性 **逐渐减弱**\n\n"
            f"💡 记忆口诀：**\"同周期左大右小，同族上小下大\"**（指原子半径）\n\n"

            f"**🧪 三、周期表的应用（中考/高考常考）**\n\n"
            f"1. 推断元素性质：找到某元素的位置→判断它是金属还是非金属→推测它的化学性质\n"
            f"2. 寻找新物质：半导体材料(Si/Ge)在金属与非金属分界线附近\n"
            f"3. 农业施肥：根据作物需要的元素选择化肥(N/P/K肥料)\n"
            f"4. 前20号元素要背熟：H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca"
        )

    # ═══════════════════════════════════════
    #  空气/氧气
    # ═══════════════════════════════════════
    if any(k in s for k in("空气","氧气","氮气","稀有气体")):
        return (
            f"【{s}】\n\n"
            f"**空气的组成（按体积分数）**：\n"
            f"- 氮气(N₂)：**78%**\n"
            f"- 氧气(O₂)：**21%**\n"
            f"- 稀有气体(Ar等)：0.94%\n"
            f"- 二氧化碳(CO₂)：0.03%\n"
            f"- 其他气体杂质：0.03%\n\n"
            f"**氧气的性质**：\n"
            f"- 物理：无色无味气体，密度比空气略大，不易溶于水\n"
            f"- 化学：**助燃性**（支持燃烧）和**氧化性**（供给呼吸）\n"
            f"- 检验：用带火星的木条，复燃→是O₂\n\n"
            f"**制取氧气**：\n"
            f"- 实验室：$2KMnO_4 \\xrightarrow{{\\Delta}} K_2MnO_4 + MnO_2 + O_2↑$（加热高锰酸钾）\n"
            f"- 工业分离液态空气（利用沸点不同）"
        )
    if any(k in s for k in("水","电解水","氢气")):
        return (
            f"【{s}】\n\n"
            f"水的组成：$2H_2O \\xrightarrow{{通电}} 2H_2↑ + O_2↑$（电解水实验）\n\n"
            f"实验现象：\n"
            f"- 正极产生**氧气**（O₂），负极产生**氢气**（H₂）\n"
            f"- 氢气体积 : 氧气体积 = **2 : 1**\n\n"
            f"结论：水由**氢元素**和**氧元素**组成。\n\n"
            f"水的净化步骤：沉淀→过滤→吸附→蒸馏（蒸馏水是纯净水）。\n"
            f"硬水（含Ca²⁺/Mg²⁺多）vs 软水——肥皂水可区分。"
        )
    if any(k in s for k in("化学方程式","质量守恒","配平")):
        return (
            f"【{s}】\n\n"
            f"**质量守恒定律**：参加化学反应的各物质的**质量总和**等于反应后生成的各物质的**质量总和**。\n\n"
            f"微观解释：反应前后原子的**种类、数目、质量都不变**（只是重新排列组合）。\n\n"
            f"**化学方程式的书写步骤**：\n"
            f"1. 写出反应物和生成物的化学式\n"
            f"2. **配平**（两边各原子个数相等）\n"
            f"3. 注明**条件和符号**（△加热/点燃/催化剂；↑气体↓沉淀）\n\n"
            f"配平方法：最小公倍数法 / 观察法 / 奇偶配平法"
        )
    if any(k in s for k in("碳","CO₂","一氧化碳","CO","金刚石","石墨","碳酸")):
        return (
            f"【{s}】\n\n"
            f"**碳的单质**：金刚石（最硬天然矿物）、石墨（软导电）、C₆₀（足球烯）。\n"
            f"三者性质差异大的原因：**碳原子排列方式不同**！\n\n"
            f"**碳的氧化物**：\n"
            f"- **CO₂**：不燃烧也不支持灭火（干冰），温室气体\n"
            f"  验证：通入澄清石灰水→变浑浊（$Ca(OH)_2 + CO_2 = CaCO_3↓ + H_2O$）\n"
            f"- **CO**：有毒（与血红蛋白结合），可燃还原性（冶炼金属）\n\n"
            f"**碳酸钙**（大理石/石灰石主要成分）：\n"
            f"$CaCO_3 \\xrightarrow{{高温}} CaO + CO_2↑$（工业制CO₂）"
        )
    if any(k in s for k in("金属","金属活动性","合金","铁","铜","置换反应")):
        return (
            f"【{s}】\n\n"
            f"**金属活动性顺序**：K Ca Na Mg Al Zn Fe Sn Pb (H) Cu Hg Ag Pt Au\n\n"
            f"规律：\n"
            f"- 排在H前面的金属能与**酸**反应放出H₂（越靠前越剧烈）\n"
            f"- 排在前面的金属能把排在后面的金属从其**盐溶液**中置换出来\n\n"
            f"**铁的冶炼**（高炉）：$Fe_2O_3 + 3CO \\xrightarrow{{高温}} 2Fe + 3CO_2$\n\n"
            f"**铁生锈条件**：同时接触**水和氧气**。防锈方法：涂油、刷漆、镀金属。\n\n"
            f"**合金**：比纯金属硬度更高熔点更低（如钢比纯铁硬）。"
        )
    if any(k in s for k in("溶液","溶质","溶剂","溶解度","饱和","结晶","酸碱盐")):
        return (
            f"【{s}】\n\n"
            f"**溶液**：一种或几种物质分散到另一种物质里形成的**均一、稳定**的混合物。\n"
            f"溶质（被溶解的物质）+ 溶剂（溶解其他物质的物质，通常为水）。\n\n"
            f"**溶解度**：一定温度下，100g溶剂中达到饱和时所溶解的质量(g)。\n\n"
            f"影响固体溶解度的因素：主要是**温度**（多数随温升而增大，少数相反如Ca(OH)₂）。\n\n"
            f"**酸碱盐通性**：\n"
            f"- 酸 + 金属 → 盐 + H₂↑\n"
            f"- 酸 + 碱 → 盐 + 水（中和反应）\n"
            f"- 酸 + 金属氧化物 → 盐 + 水\n"
            f"- 碱 + 非金属氧化物 → 盐 + 水\n"
            f"- 盐₁ + 盐₂ → 新盐₁ + 新盐₂（需满足复分解条件：生成沉淀/气体/水）"
        )

    # 化学兜底
    return (
        f"【{s}——化学要点】\n\n"
        f"学习化学要建立「**宏观-微观-符号」」三维思维方式：\n\n"
        f"1. **宏观**：观察到什么现象（颜色变化、气泡、沉淀…）\n"
        f"2. **微观**：分子/原子/离子层面发生了什么变化\n"
        f"3. **符号**：用化学式和方程式准确表达\n\n"
        f"特别注意：化学反应**条件**（△/点燃/高温/催化剂）和**配平**不可遗漏！"
    )


def _gen_science_content(t, s):
    """小学科学智能内容引擎"""
    if any(k in s for k in("种子萌发","根","茎","叶","开花","结果","生命周期")):
        return (
            f"【{s}】\n\n"
            f"植物的一生经历：**种子萌发 → 生长 → 开花 → 结果 → 死亡**\n\n"
            f"**种子萌发条件**：\n"
            f"- 外部：适宜的温度、一定的水分、充足的空气\n"
            f"- 内部：完整的活胚、供胚发育的营养\n\n"
            f"**根的作用**：固定植株 + 吸收水分和无机盐（根毛区是主要吸收部位）\n\n"
            f"**茎的作用**：支撑 + 运输（导管运水上行，筛管运有机物下行）\n\n"
            f"**叶的作用**：光合作用制造养料 + 蒸腾作用运输水分\n\n"
            f"**花的结构**：雄蕊（花药/花粉）+ 雌蕊（柱头/子房/胚珠）\n"
            f"传粉后受精→子房发育成果实，胚珠发育成种子。"
        )
    if any(k in s for k in("蚕","昆虫","两栖","哺乳","动物","生命周期")):
        return (
            f"【{s}】\n\n"
            f"动物的分类和生命周期：\n\n"
            f"**昆虫（以蚕为例）**：卵→幼虫→蛹→成虫（**完全变态**，4个阶段）\n"
            f"蚕宝宝吃桑叶长大→吐丝结茧→化蛹→羽化为蚕蛾\n\n"
            f"**两栖动物（青蛙）**：卵→蝌蚪→幼蛙→成蛙（**变态发育**）\n"
            f"蝌蚪有尾无腿→长出四肢→尾巴消失→变成青蛙\n\n"
            f"**哺乳动物**：胎生 + 哺乳（人类、狗、猫、鲸鱼都是哺乳动物！）\n\n"
            f"💡 观察：不同动物的生命周期有什么异同？变态发育的意义是什么？"
        )
    if any(k in s for k in("温度","温度计","融化","凝固","蒸发","凝结","水循环")):
        return (
            f"【{s}】\n\n"
            f"**温度**表示物体的冷热程度，用**温度计**测量。\n\n"
            f"常用温度计原理：**液体的热胀冷缩**（酒精/煤油/水银）\n\n"
            f"**水的三态变化**：\n"
            f"- 固→液：**融化**（吸热，冰→水，0℃）\n"
            f"- 液→固：**凝固**（放热，水→冰，0℃）\n"
            f"- 液→气：**蒸发/汽化**（吸热，水→水蒸气）\n"
            f"- 气→液：**液化/凝结**（放热，水蒸气→水滴）\n\n"
            f"**自然界的水循环**：海洋/湖泊水蒸发→云→降雨→回到地面→流入江河湖海\n\n"
            f"💡 实验：观察冰融化过程中温度如何变化？"
        )
    if any(k in s for k in("磁铁","磁极","指南针","磁","吸引")):
        return (
            f"【{s}】\n\n"
            f"**磁铁的性质**：\n"
            f"1. 能吸引**铁、钴、镍**等物质（磁性）\n"
            f"2. 有两个**磁极**（磁性最强的地方）：N极（北极）和 S极（南极）\n"
            f"3. **同极相斥，异极相吸**\n"
            f"4. 能指示方向（指南针原理）\n\n"
            f"**指南针**：地球本身是一个巨大的磁体！\n"
            f"地磁北极≈地理南极，地磁南极≈地理北极（不完全重合）\n\n"
            f"💡 动手做：用磁铁的不同部位去靠近大头针，哪处吸引力最强？"
        )
    if any(k in s for k in("材料","木头","塑料","金属","溶解","沉浮","硬度")):
        return (
            f"【{s}】\n\n"
            f"**常见材料的性质对比**：\n\n"
            f"| 材料 | 优点 | 缺点 | 典型用途 |\n"
            f"|------|------|------|----------|\n"
            f"| 木材 | 易加工、环保 | 怕水怕火 | 家具 |\n"
            f"| 塑料 | 轻便防水 | 不易降解 | 日用品 |\n"
            f"| 金属 | 强度高导电导热 | 会生锈 | 工具建筑 |\n"
            f"| 纸张 | 可书写易回收 | 不耐水 | 书本包装 |\n\n"
            f"**溶解**：一种物质均匀分散到另一种液体中（糖溶于水、盐溶于水）\n"
            f"**沉浮**：取决于物体密度和液体的关系（木块浮、铁块沉）\n\n"
            f"💡 思考：为什么钢铁制造的轮船可以浮在水面上？（空心原理）"
        )
    if any(k in s for k in("太阳","月亮","地球","四季","昼夜","影","方位")):
        return (
            f"【{s}】\n\n"
            f"**太阳**是一颗恒星，自己发光发热。\n"
            f"**月球**是地球的卫星，反射太阳光。\n"
            f"**地球**自转→**昼夜交替**（自西向东转，约24小时一圈）\n\n"
            f"**四季成因**：地球**公转** + 地轴倾斜（23.5°倾斜角）\n"
            f"- 太阳直射北半球→北半球夏季（昼长夜短）\n"
            f"- 太阳直射南半球→北半球冬季（昼短夜长）\n\n"
            f"**月相变化**（一个月周期）：新月→蛾眉月→上弦月→凸月→满月→残月→下弦月→蛾眉月→新月\n\n"
            f"💡 观察记录：连续一个月每天同一时间观察月亮形状的变化。"
        )

    # 科学兜底
    return (
        f"【{s}】\n\n"
        f"科学课的核心方法是**观察、提问、实验、验证**。\n\n"
        f"关于「{s}」，我们要：\n"
        f"1. **仔细观察**：用感官和工具收集信息\n"
        f"2. **提出问题**：看到现象多问为什么\n"
        f"3. **做出猜想**：基于已有知识推测答案\n"
        f"4. **设计实验**：验证猜想是否正确\n"
        f"5. **记录分析**：整理数据得出结论\n\n"
        f"💡 科学精神：实事求是、勇于质疑、不断探索！"
    )


def _gen_chinese_content(t, s):
    """语文学科智能内容引擎"""
    if any(k in s for k in("拼音","声母","韵母","声调","识字")):
        return (
            f"【{s}】\n\n"
            f"汉语拼音是识字和学习普通话的工具。\n\n"
            f"**声母**（23个）：b p m f d t n l g k h j q x zh ch sh r z c s y w\n\n"
            f"**韵母**：单韵母(a o e i u ü) + 复韵母(ai ei ui ao ou iu ie üe er) + 鼻韵母(an en in un ün ang eng ing ong)\n\n"
            f"**四声调**：ˉ一声（阴平）/ ˊ二声（阳平）/ ˇ三声（上声）/ ˋ四声（去声）\n\n"
            f"整体认读音节（16个）：zhi chi shi ri zi ci si yi wu yu ye yue yuan yin yun ying\n\n"
            f"💡 学习技巧：拼读时声母轻短、韵母响亮，快速连读。"
        )
    if any(k in s for k in("词语","成语","近义词","反义词","词语理解")):
        return (
            f"【{s}】\n\n"
            f"词语是语言表达的最小意义单位。\n\n"
            f"**理解词语的方法**：\n"
            f"1. **拆字法**：把词语拆开分别理解再合起来\n"
            f"2. **联系上下文**：根据前后文推断词义\n"
            f"3. **找近义词替换**：用熟悉的词替换理解\n"
            f"4. **查字典**：权威的解释\n\n"
            f"**成语**的特点：形式固定、来源典故、言简意赅。\n"
            f"记忆成语要理解其**出处和寓意**，不能望文生义。\n\n"
            f"💡 积累习惯：准备一本好词好句摘抄本，随时记录。"
        )
    if any(k in s for k in("句子","句式","修辞","比喻","拟人","排比","夸张","修改病句")):
        return (
            f"【{s}】\n\n"
            f"常见的修辞手法：\n\n"
            f"**比喻**：甲像乙（本体+喻体+喻词）。「月亮像玉盘」\n\n"
            f"**拟人**：把物当人写。「小草探出了头」\n\n"
            f"**排比**：三个以上结构相同的句子增强气势。\n\n"
            f"**夸张**：故意夸大或缩小。「飞流直下三千尺」\n\n"
            f"**修改病句常见错误**：\n"
            f"- 成分残缺（缺主语/谓语/宾语）\n"
            f"- 搭配不当\n"
            f"- 语序颠倒\n"
            f"- 前后矛盾\n"
            f"- 重复啰嗦\n\n"
            f"💡 技巧：读一遍句子，看是否通顺自然。"
        )
    if any(k in s for k in("阅读","课文","理解","概括","中心思想","段落")):
        return (
            f"【{s}】\n\n"
            f"阅读理解的关键方法和步骤：\n\n"
            f"**初读**：了解文章大意（写了什么人什么事）\n\n"
            f"**精读**：逐段分析（每段讲了什么、怎么写的）\n\n"
            f"**概括主要内容**：\n"
            f"- 要素串联法：谁+在哪里+做了什么+结果怎样\n"
            f"- 段意合并法：把各段大意综合起来\n"
            f"- 标题扩展法：在标题基础上补充完整\n\n"
            f"**归纳中心思想**：\n"
            f"本文通过写了……表达了作者……的思想感情（赞美了/揭露了/说明了…）\n\n"
            f"💡 好文章至少读三遍：第一遍通读，第二遍细读，第三遍品读。"
        )
    if any(k in s for k in("作文","写作","习作","记叙文","说明文","议论文")):
        return (
            f"【{s}】\n\n"
            f"写作的基本功和技巧：\n\n"
            f"**记叙文六要素**：时间、地点、人物、起因、经过、结果\n\n"
            f"**好的开头**：开门见山 / 设置悬念 / 引用名言 / 景物描写引入\n\n"
            f"**好的结尾**：总结全文 / 点明中心 / 引人深思 / 首尾呼应\n\n"
            f"**让作文生动的方法**：\n"
            f"- 用具体的细节代替空洞的叙述\n"
            f"- 运用多种感官描写（看到的、听到的、闻到的、触到的）\n"
            f"- 恰当使用修辞手法\n"
            f"- 加入心理活动和对话\n\n"
            f"💡 写作秘诀：真情实感最重要，不要堆砌华丽辞藻。"
        )
    if any(k in s for k in("古诗","诗词","古诗文","背诵","默写")):
        return (
            f"【{s}】\n\n"
            f"古诗文学习的正确打开方式：\n\n"
            f"1. **读准字音**：注意多音字和古今音变\n\n"
            f"2. **理解词义**：逐字逐词理解（重点字词要注释）\n\n"
            f"3. **翻译全文**：用自己的话讲清楚诗句的意思\n\n"
            f"4. **体会情感**：诗人想表达什么感情？为什么这样写？\n\n"
            f"5. **背诵默写**：准确无误地写出原文（注意易错字！）\n\n"
            f"💡 方法：「诗中有画」——边读边想象画面，更容易理解和记忆。\n\n"
            f"常见题材：送别诗（依依不舍）、思乡诗（思念家乡）、边塞诗（壮志豪情）、咏物诗（托物言志）"
        )

    # 语文兜底
    return (
        f"【{s}】\n\n"
        f"语文学习重在**积累和感悟**。\n\n"
        f"对于「{s}」，建议：\n"
        f"1. 多朗读：感受语言的节奏美和韵律美\n"
        f"2. 勤积累：摘抄优美词句和精彩片段\n"
        f"3. 善思考：联系生活体验理解文本深层含义\n"
        f"4. 常练笔：仿写、改写、续写提升表达能力\n"
        f"5. 广阅读：课内外结合，扩大知识面"
    )


def _gen_english_content(t, s):
    """英语学科智能内容引擎"""
    if any(k in s for k in("phonics","音标","发音","pronunciation","字母")):
        return (
            f"【{s}】\n\n"
            f"语音是英语学习的基础。\n\n"
            f"**26个字母**：Aa Bb Cc Dd Ee Ff Gg Hh Ii Jj Kk Ll Mm Nn Oo Pp Qq Rr Ss Tt Uu Vv Ww Xx Yy Zz\n\n"
            f"**元音字母**：Aa Ee Ii Oo Uu（有时Y也是）\n\n"
            f"**48个国际音标**要逐步掌握：\n"
            f"- 元音（20）：单元音12个 + 双元音8个\n"
            f"- 辅音（28）：清辅音 + 浊辅音\n\n"
            f"💡 自然拼读法（Phonics）：见词能读，听音能写。\n"
            f"掌握字母和字母组合的发音规律，大大提高记单词效率。"
        )
    if any(k in s for k in("word","vocab","vocabulary","词汇","单词")):
        return (
            f"【{s}】\n\n"
            f"高效记单词的方法：\n\n"
            f"1. **自然拼读**：根据发音规律拼写单词\n\n"
            f"2. **词根词缀**：\n"
            f"   - un-/dis-/im-(否定) happy→unhappy\n"
            f"   - -er/-or(人) teach→teacher\n"
            f"   - -ful/-less(形容词) help→helpful\n\n"
            f"3. **联想记忆**：建立单词间的联系\n\n"
            f"4. **语境记忆**：在句子和文章中记单词（不要孤立背单词表！）\n\n"
            f"5. **循环复习**：艾宾浩斯遗忘曲线——1天、3天、7天、15天复习\n\n"
            f"💡 每天10-15个新词，坚持就是胜利！"
        )
    if any(k in s for k in("grammar","语法","时态","tense","一般现在","一般过去","一般将来","现在进行")):
        return (
            f"【{s}】\n\n"
            f"四大基础时态：\n\n"
            f"**一般现在时**：经常发生的动作/客观事实\n"
            f"标志词：always/usually/often/sometimes/every day\n"
            f"I **study** English every day. / He **studies** English.\n\n"
            f"**一般过去时**：过去发生的动作/状态\n"
            f"标志词：yesterday/last week/ago/in 2010\n"
            f"I **studied** English yesterday.\n\n"
            f"**一般将来时**：将要发生的动作\n"
            f"标志词：tomorrow/next week/soon\n"
            f"I **will study** English tomorrow. / I **am going to study**...\n\n"
            f"**现在进行时**：正在进行的动作\n"
            f"标志词：now/look/listen/right now\n"
            f"I **am studying** English **now**."
        )
    if any(k in s for k in("sentence","句型","疑问句","there be","特殊疑问")):
        return (
            f"【{s}】\n\n"
            f"重要句型结构：\n\n"
            f"**There be 句型**（某处有某物）：\n"
            f"There **is** a book on the desk.\n"
            f"There **are** many students in the classroom.\n"
            f"(就近原则：be动词取决于最近的名词)\n\n"
            f"**特殊疑问句**（Wh-questions）：\n"
            f"What/Who（问事物/人）| Where（问地点）| When（问时间）\n"
            f"Why（问原因）| How（问方式/程度）| Whose/Which（问所属）\n\n"
            f"语序：**特殊疑问词 + 一般疑问句语序**？"
        )
    if any(k in s for k in("reading","reading comprehension","阅读")):
        return (
            f"【{s}】\n\n"
            f"英语阅读技巧：\n\n"
            f"1. **略读（Skimming）**：快速浏览获取主旨（看首段、末段、每段首句）\n\n"
            f"2. **寻读（Scanning）**：带着问题找答案（定位关键词）\n\n"
            f"3. **猜词义**：根据上下文、构词法、逻辑关系猜测生词意思\n\n"
            f"4. **长难句拆解**：找主干（主谓宾）→ 剥修饰（定状补）\n\n"
            f"5. **推理判断**：注意 but/however/although 等转折词后的信息\n\n"
            f"💡 先看题目再读文章，带着问题找答案更高效！"
        )
    if any(k in s for k in("writing","writing composition","书面表达","email","letter")):
        return (
            f"【{s}】\n\n"
            f"英语写作框架（以书信为例）：\n\n"
            f"**格式**：称呼(Dear...,) → 正文 → 落款(Yours,/Love,) → 名字\n\n"
            f"**正文结构**：\n"
            f"- Opening：问候 + 点明写信目的\n"
            f"- Body：分段阐述要点（用First/Second/Finally/Also连接）\n"
            f"- Closing：总结 + 期待回复\n\n"
            f"**加分亮点**：\n"
            f"- 使用高级词汇和短语（important→significant/vital）\n"
            f"- 多样化句式（简单句+并列句+复合句混用）\n"
            f"- 恰当使用连接词使行文流畅\n\n"
            f"💡 写完后检查：拼写/时态/主谓一致/标点。"
        )

    # 英语兜底
    return (
        f"【{s}——English Learning Focus】\n\n"
        f"**Key Points for {s}**: \n\n"
        f"1. **Listen & Imitate**: Listen to standard pronunciation and imitate the intonation\n"
        f"2. **Practice Speaking**: Use new expressions in real contexts\n"
        f"3. **Learn Vocabulary**: Use words in sentences, not just memorize word lists\n"
        f"4. **Grammar in Context**: Learn grammar through reading and writing practice\n"
        f"5. **Keep Practicing**: Language learning is a marathon, not a sprint 🏃‍♂️"
    )


def _gen_history_content(t, s):
    """历史学科智能内容引擎（安全网：Ollama 懒生成失败时的话题相关兜底，绝不整科重复）"""
    return (
        f"【{s}】——「{t}」中的一环\n\n"
        f"学习「{s}」建议按这条主线梳理，避免孤立记忆：\n\n"
        f"1. **定位时空**：「{s}」所处的朝代/时期与大致时间范围是什么？\n"
        f"2. **关键人物与事件**：与之相关的代表人物、重大事件，以及它们之间的因果；\n"
        f"3. **制度与变革**：当时在政治、经济、文化方面的典型特征或转折；\n"
        f"4. **历史影响**：对当时社会与后世发展产生了什么意义。\n\n"
        f"💡 把「{s}」放在「{t}」的整体脉络里，用时间轴把前因后果串起来，"
        f"比死记硬背更有效。遇到具体年代、人物、意义拿不准时，结合课本和年代尺再巩固。"
    )


def _gen_geography_content(t, s):
    """地理学科智能内容引擎（安全网：Ollama 懒生成失败时的话题相关兜底，绝不整科重复）"""
    return (
        f"【{s}】——「{t}」中的地理现象\n\n"
        f"学习「{s}」建议用**图文结合 + 空间思维**来分析：\n\n"
        f"1. **定位**：「{s}」在地图的哪里？（经纬度、相对位置、所属区域）\n"
        f"2. **自然环境**：地形、气候、河流、土壤、植被各有什么特点？\n"
        f"3. **人文特征**：人口、城市、农业、工业、交通如何分布？\n"
        f"4. **因果分析**：自然环境怎样影响人类活动？人类活动又如何改变环境？\n\n"
        f"💡 地图是地理的第二语言——结合「{t}」相关地图（图例/方向/比例尺/注记），\n"
        f"把文字描述对应到空间位置，理解会更牢。具体数据拿不准时，回到课本地图再确认。"
    )


def _tip_for(subject):
    tips = {
        "数学": "注意书写规范与步骤完整，算完顺手验算一遍；遇到复杂题先画图帮助理解。",
        "语文": "朗读、摘抄好词好句，并尝试用自己的话复述文意。",
        "英语": "多听多读，留意发音和例句，试着用这个表达造一个自己的句子。",
        "物理": "结合生活现象理解概念，先懂物理意义再代入公式计算。",
        "化学": "记住物质的性质和反应条件，动手写方程式并注意配平。",
        "生物": "借助插图和实物观察，理解「结构决定功能」。",
        "历史": "按时间线梳理事件的起因、经过、结果和影响。",
        "地理": "多看图（地图、示意图），把文字描述和空间位置对应起来。",
        "道德与法治": "联系身边的生活与新闻事例，理解规则与价值。",
        "思想政治": "用\"是什么-为什么-怎么做\"的框架梳理观点。",
        "科学": "动手做小实验、认真观察记录，从现象中找规律。",
    }
    return tips.get(subject, "结合课本和课堂笔记，先理解再练习，遇到不懂及时提问。")


def _mistakes_for(topic_title=None, sub=None):
    """返回易错点（如果能匹配到具体知识点则更精准）"""
    if topic_title:
        specific = _MISTAKES_MAP.get((topic_title, sub or topic_title))
        # 该键可能存的是讲解内容（误置于此）而非易错点列表，需甄别
        if isinstance(specific, list):
            return specific
    return [
        "概念混淆：把名称相近的内容记串了，建议用对比表区分清楚。",
        "只背不练：看懂了不等于会做，务必独立完成几道习题再过关。",
        "跳过基础：难题往往建立在基础之上，先确保基础牢固再挑战综合题。",
    ]


# ========== 各知识点的易错点库 ==========
_MISTAKES_MAP = {
    ("比", "比的定义"): [
        "顺序错误：A:B ≠ B:A！「男生与女生的比」和「女生与男生的比」是不同的。",
        "比值忘记化简：算出 20/25 要约分为 4/5 或写成 0.8。",
        "后项为0：比的后项不能为0，和除法中除数不能为0一样。",
    ],
    ("比", "比的基本性质"): [
        "漏掉「0除外」：同时乘或除的数不能是0！",
        "混淆「比值不变」和「差不变」：比的基本性质保持比值不变，不是差不变。",
    ],
    ("比", "化简比"): [
        "化简比 ≠ 求比值：化简结果是比（如2:3），求比值结果是数（如2/3）",
        "含小数的要先变整数：0.25:1.5 先同乘100变成25:150再约分。",
        "分数比要找公分母：先乘分母的最小公倍数把分子变成整数。",
    ],
    ("比", "按比例分配"): [
        "忘记先求总份数：一定要先把各项加起来得到总份数！",
        "每份 = 总量 × 该项份数 ÷ 总份数（不要漏掉除以总份数）",
        "最后不验算：各部分之和应等于总量，养成验算习惯。",
    ],
    ("比", "比的应用"): [
        "找不到单位「1」：仔细读题，「的」「占」「是」后面通常是单位1。",
        "变化前后总量不同：有的题目中量发生变化时，总量可能改变。",
        "方程法更稳妥：复杂问题建议设未知数列方程，思路更清晰。",
    ],

    # ===== 倍的认识（三年级数学）=====
    ("倍的认识", "倍的概念"): {
        "body": (
            "【什么是「倍」？】\n"
            "「倍」表示两个数量之间的一种**比较关系**。\n"
            "如果一个数量里面包含几个另一个数量，我们就说这个数量是另一个数量的**几倍**。\n\n"
            "**关键理解**：「倍」不是具体的数，而是一种关系！\n\n"
            "【用除法理解倍】\n"
            "求 A 是 B 的几倍 → 用除法：$A \\div B = ?$\n\n"
            "【直观例子】\n\n"
            "🍎 苹果：🍎🍎🍎🍎（4个）\n"
            "🍊 橘子：🍊🍊（2个）\n\n"
            "4 里面有 2 个 2 → 苹果是橘子的 **2 倍**\n"
            "$4 \\div 2 = 2$\n\n"
            "【重要区别】\n"
            "• 「A 是 B 的几倍」→ 用**除法** ($A \\div B$)\n"
            "• 「A 的几倍是多少」→ 用**乘法** ($A \\times 倍数$)\n\n"
            "这两个完全不一样，千万不要混淆！"
        ),
        "example": (
            "【例题1】\n"
            "小明有 6 个苹果，小红有 2 个苹果。小明的苹果是小红的几倍？\n\n"
            "解：求 6 是 2 的几倍 → 用除法\n"
            "$6 \\div 2 = 3$（倍）\n\n"
            "答：小明的苹果是小红的 **3 倍**。\n\n"
            "验证：2 + 2 + 2 = 6 ✓（3个2就是6）\n\n"
            "---\n\n"
            "【例题2】\n"
            "操场上有 12 名男生在踢足球，4 名女生在跳绳。男生人数是女生的几倍？\n\n"
            "解：$12 \\div 4 = 3$（倍）\n\n"
            "答：男生人数是女生的 **3 倍**。"
        ),
    },
    ("倍的认识", "求一个数是几倍"): {
        "body": (
            "【核心方法：用除法】\n"
            "求「A 是 B 的几倍」，就是把 A 按每份 B 个来分，看能分成几份。\n\n"
            "**公式**：$A \\div B = 倍数$\n\n"
            "【解题步骤】\n"
            "**第一步：找准两个量**\n"
            "• 谁是「被比较量」（A）→ 放在被除数位置\n"
            "• 谁是「标准量」（B）→ 放在除数位置\n\n"
            "**第二步：列除法算式**\n"
            "$A \\div B = ?$\n\n"
            "**第三步：计算并写单位**\n"
            "倍数的单位是「倍」（不带其他单位名）\n\n"
            "【如何找标准量？】\n"
            "读题时注意关键词：\n"
            "• 「A 是 **B** 的几倍」→ B 是标准量\n"
            "• 「A 是 **B 的几倍**」→ B 还是标准量\n"
            "• 「**比** B **多/少** 几倍」→ B 是标准量\n\n"
            "⚠️ 顺序搞反了结果就不对！"
        ),
        "example": (
            "【例题1】\n"
            "动物园里有 15 只猴子，5 只熊猫。猴子数量是熊猫的几倍？\n\n"
            "分析：猴子是被比较量(15)，熊猫是标准量(5)\n\n"
            "解：$15 \\div 5 = 3$（倍）\n\n"
            "答：猴子数量是熊猫的 **3 倍**。\n\n"
            "---\n\n"
            "【例题2】\n"
            "一本故事书 48 页，一本漫画书 8 页。故事书的页数是漫画书的几倍？\n\n"
            "解：$48 \\div 8 = 6$（倍）\n\n"
            "答：故事书的页数是漫画书的 **6 倍**。\n\n"
            "---\n\n"
            "【例题3】\n"
            "奶奶今年 63 岁，小红今年 7 岁。奶奶的年龄是小红的几倍？\n\n"
            "解：$63 \\div 7 = 9$（倍）\n\n"
            "答：奶奶的年龄是小红的 **9 倍**。"
        ),
    },
    ("倍的认识", "求一个数的几倍"): {
        "body": (
            "【核心方法：用乘法】\n"
            "求「A 的几倍是多少」，就是求几个 A 相加的和。\n\n"
            "**公式**：$A \\times 倍数 = ?$\n\n"
            "【为什么用乘法？】\n"
            "「A 的 3 倍」= $A + A + A = A \\times 3$\n"
            "乘法就是求几个相同加数和的简便运算！\n\n"
            "【与「求一个数是几倍」的区别】\n\n"
            "| 问题类型 | 方法 | 算式示例 |\n"
            "|---------|------|---------|\n"
            "| 求 A 是 B 的几倍 | 除法 | $12 \\div 3 = 4$ 倍 |\n"
            "| 求 A 的 3 倍 | 乘法 | $7 \\times 3 = 21$ |\n\n"
            "【记忆口诀】\n"
            "「是几倍」→ **除法**来求\n"
            "「的几倍」→ **乘法**来算\n"
            "看准关键字，方法不混淆！\n\n"
            "【进阶】求「A 的几倍多（或少）几」\n"
            "公式：$A \\times 倍数 + 多出的部分$ 或 $A \\times 倍数 - 少的部分$"
        ),
        "example": (
            "【例题1】\n"
            "一本书有 8 页，3 本这样的书一共有多少页？\n"
            "（也就是求 8 的 3 倍是多少）\n\n"
            "解：$8 \\times 3 = 24$（页）\n\n"
            "答：3 本这样的书一共 **24 页**。\n\n"
            "---\n\n"
            "【例题2】\n"
            "小芳有 4 支铅笔，小丽的铅笔数是小芳的 5 倍。小丽有多少支铅笔？\n\n"
            "分析：求 4 的 5 倍 → 用乘法\n\n"
            "解：$4 \\times 5 = 20$（支）\n\n"
            "答：小丽有 **20 支**铅笔。\n\n"
            "---\n\n"
            "【例题3】\n"
            "舞蹈队有 9 名女生，男生人数比女生的 2 倍还多 3 人。男生有多少人？\n\n"
            "解：$9 \\times 2 + 3 = 18 + 3 = 21$（人）\n\n"
            "答：男生有 **21 人**。"
        ),
    },
    ("倍的认识", "画图解题"): {
        "body": (
            "【为什么要画图？】\n"
            "画图可以把抽象的「倍」的关系变成直观的线段，帮助我们理解和检验答案。\n\n"
            "【基本画法：线段图】\n\n"
            "**步骤一：画出标准量（1倍量）**\n"
            "画一条短线段代表「1份」（即标准量B），标注数量。\n\n"
            "**步骤二：画出被比较量**\n"
            "根据倍数画出等长的几段线段，标注总数。\n\n"
            "**举例**：求 12 是 4 的几倍\n\n"
            "标准量（4）：┃\n"
            "被比较量（12）：┃ ┃ ┃\n"
            "              ↑   ↑   ↑\n"
            "             4   4   4\n\n"
            "一眼看出：12 里面有 3 个 4 → **3 倍**\n\n"
            "【画图的好处】\n"
            "① 直观看到数量关系\n"
            "② 帮助发现隐蔽条件\n"
            "③ 验证计算结果是否合理\n"
            "④ 复杂问题时思路更清晰"
        ),
        "example": (
            "【例题】\n"
            "果园里种了 6 棵苹果树，梨树的棵数是苹果树的 4 倍。两种树一共有多少棵？\n\n"
            "画图分析：\n\n"
            "苹果树：▬▬（6棵）\n"
            "梨树：  ▬▬ ▬▬ ▬▬ ▬▬（4段，每段6棵）\n\n"
            "从图中可以看出：\n"
            "梨树 = $6 \\times 4 = 24$（棵）\n"
            "总共 = $6 + 24 = 30$（棵）\n\n"
            "综合算式：$6 + 6 \\times 4 = 6 + 24 = 30$（棵）\n"
            "或 $6 \\times (4+1) = 6 \\times 5 = 30$（棵）\n\n"
            "答：两种树一共有 **30 棵**。"
        ),
    },
    ("倍的认识", "应用"): {
        "body": (
            "【倍的综合应用类型】\n\n"
            "**类型一：和倍问题**\n"
            "已知两个量的和以及倍数关系，分别求出两个量。\n"
            "方法：把较小的看作 1 份，较大的看作 n 份，总共有 (n+1) 份。\n"
            "• 1份数量和 $=$ 总和 $\\div (n+1)$\n"
            "• 较大量 $=$ 小量 $\\times n$\n\n"
            "**类型二：差倍问题**\n"
            "已知两个量的差以及倍数关系，分别求出两个量。\n"
            "方法：差 $\\div (n-1) =$ 较小的量（1份）\n\n"
            "**类型三：倍数变化问题**\n"
            "\"A 比 B 多几倍\" 或 \"A 增加后变成 B 的几倍\"\n"
            "关键是抓住**不变的量**作为突破口。\n\n"
            "【解题策略】\n"
            "1. 先画线段图帮助理解\n"
            "2. 找准 1 倍量（标准量）\n"
            "3. 区分用乘法还是除法\n"
            "4. 写完整单位和答句"
        ),
        "example": (
            "【例题1 — 和倍问题】\n"
            "哥哥和弟弟一共有 36 张卡片，哥哥的卡片数是弟弟的 2 倍。兄弟俩各有多少张？\n\n"
            "画图：\n"
            "弟弟：▬（1份）\n"
            "哥哥：▬ ▬（2份）\n"
            "总共：▬ ▬ ▬ = 36 张（3份）\n\n"
            "解：\n"
            "总份数 = $2 + 1 = 3$（份）\n"
            "弟弟（1份）：$36 \\div 3 = 12$（张）\n"
            "哥哥（2份）：$12 \\times 2 = 24$（张）\n"
            "验算：$12 + 24 = 36$ ✓\n\n"
            "答：弟弟有 **12 张**，哥哥有 **24 张**。\n\n"
            "---\n\n"
            "【例题2 — 差倍问题】\n"
            "爸爸今年 35 岁，儿子今年 5 岁。几年后爸爸的年龄是儿子的 3 倍？\n\n"
            "分析：无论过几年，父子**年龄差不变**（始终是 $35 - 5 = 30$ 岁）\n\n"
            "当爸爸年龄是儿子的 3 倍时，年龄差相当于儿子的 $(3-1)=2$ 倍\n\n"
            "解：那时儿子的年龄 = $30 \\div (3-1) = 30 \\div 2 = 15$（岁）\n"
            "经过的年数 = $15 - 5 = 10$（年）\n\n"
            "验算：10年后爸爸45岁，儿子15岁，$45 \\div 15 = 3$ ✓\n\n"
            "答：**10 年后**爸爸的年龄是儿子的 3 倍。"
        ),
    },

    # ===== 测量（三年级数学）=====
    ("测量", "毫米分米"): {
        "body": (
            "【长度单位大家庭】\n"
            "我们学过的长度单位从小到大排列：\n"
            "**毫米(mm) < 厘米(cm) < 分米(dm) < 米(m) < 千米(km)**\n\n"
            "【毫米(mm)】\n"
            "• 很短的长度用毫米计量\n"
            "• 1厘米 = **10毫米**（cm = 10 mm）\n"
            "• 生活中：硬币厚度约2mm，身份证厚度约1mm\n\n"
            "【分米(dm)】\n"
            "• 介于厘米和米之间的单位\n"
            "• 1分米 = **10厘米** = **100毫米**（dm = 10 cm = 100 mm）\n"
            "• 1米 = **10分米**（m = 10 dm）\n"
            "• 生活中：粉笔长度约1dm，手机宽度约7dm\n\n"
            "【换算规律】\n"
            "相邻两个单位的进率都是 **10**！\n"
            "毫米 → 厘米 → 分米 → 米 → 千米\n"
            " ×10    ×10     ×10    ×1000"
        ),
        "example": (
            "【例题1】\n"
            "一把尺子长 2 分米，合多少厘米？合多少毫米？\n\n"
            "解：2 dm = 2 × 10 = **20 cm**\n"
            "20 cm = 20 × 10 = **200 mm**\n\n"
            "---\n\n"
            "【例题2】\n"
            "一枚5角硬币厚约 2 毫米，10 枚这样的硬币叠在一起，厚约多少毫米？合多少厘米？\n\n"
            "解：2 × 10 = **20 mm**\n"
            "20 mm = 20 ÷ 10 = **2 cm**"
        ),
    },
    ("测量", "千米"): {
        "body": (
            "【千米(km) —— 计量很长的距离】\n"
            "千米也叫「公里」，用于计量城市之间、公路等较长的距离。\n\n"
            "**1千米(km) = 1000米(m)**\n\n"
            "【千米的实际感受】\n"
            "• 学校操场跑道1圈通常是 400 米 → 跑 **2 圈半** 约 1 km\n"
            "• 成人步行约 **15~20 分钟** 走 1 km\n"
            "• 汽车行驶约 **1 分钟** 走 1 km\n\n"
            "【常见距离参考】\n"
            "• 北京到天津约 **120 km**\n"
            "• 长江全长约 **6300 km**\n"
            "• 地球赤道周长约 **40000 km**\n\n"
            "【换算】\n"
            "• km → m：**× 1000**（如 3 km = 3000 m）\n"
            "• m → km：**÷ 1000**（如 5000 m = 5 km）"
        ),
        "example": (
            "【例题1】\n"
            "高速公路上汽车每小时行 80 千米，2 小时行多少千米？合多少米？\n\n"
            "解：80 × 2 = **160 km**\n"
            "160 km = 160 × 1000 = **160000 m**\n\n"
            "---\n\n"
            "【例题2】\n"
            "从家到学校有 2 km，小明每天往返两次（去学校一次、回家算一次为一次往返）。他一天走多少千米？合多少米？\n\n"
            "分析：1次往返 = 去 + 回 = 2 km × 2 = 4 km\n"
            "2次往返 = 4 km × 2 = **8 km** = **8000 m**"
        ),
    },
    ("测量", "吨"): {
        "body": (
            "【质量单位大家庭】\n"
            "**克(g) < 千克(kg) < 吨(t)**\n\n"
            "【吨(t) —— 计量很重的物体】\n"
            "用于计量大宗物品的质量，如车辆载重、货物重量等。\n\n"
            "**1吨(t) = 1000千克(kg)**\n\n"
            "【实际感受 1 吨有多重】\n"
            "• 1袋大米约 25 kg → **40袋大米**约 1 吨\n"
            "• 一头大象约 **3~5 吨**\n"
            "• 一辆小型轿车约 **1~2 吨**\n"
            "• 一个小学生约 35 kg → 约 **29 个同学**体重之和 ≈ 1 吨\n\n"
            "【换算】\n"
            "• t → kg：**× 1000**（如 3 t = 3000 kg）\n"
            "• kg → t：**÷ 1000**（如 5000 kg = 5 t）\n\n"
            "⚠️ 注意：长度单位和质量单位要分开记，不要混淆！"
        ),
        "example": (
            "【例题1】\n"
            "一辆卡车最多装载 5 吨货物。如果每袋水泥重 50 千克，这辆卡车最多能装多少袋水泥？\n\n"
            "解：5 t = 5000 kg\n"
            "5000 ÷ 50 = **100（袋）**\n\n"
            "---\n\n"
            "【例题2】\n"
            "一头蓝鲸重 150 吨，是大象体重的 30 倍。一头大象重多少吨？合多少千克？\n\n"
            "解：150 ÷ 30 = **5（t）**\n"
            "5 t = 5 × 1000 = **5000 kg**"
        ),
    },
    ("测量", "单位换算"): {
        "body": (
            "【单位换算的核心方法】\n\n"
            "**大单位 → 小单位：乘以进率**\n"
            "**小单位 → 大单位：除以进率**\n\n"
            "【长度单位换算表】\n\n"
            "| 单位 | 与米的关系 | 相邻进率 |\n"
            "|-----|----------|--------|\n"
            "| 千米 | 1km = 1000m | 1000 |\n"
            "| 米 | 1m | — |\n"
            "| 分米 | 1dm = 0.1m | 10 |\n"
            "| 厘米 | 1cm = 0.01m | 10 |\n"
            "| 毫米 | 1mm = 0.001m | 10 |\n\n"
            "【质量单位换算表】\n\n"
            "| 单位 | 与千克的关系 | 进率 |\n"
            "|-----|-----------|-----|\n"
            "| 吨 | 1t = 1000kg | 1000 |\n"
            "| 千克 | 1kg | — |\n"
            "| 克 | 1g = 0.001kg | 1000 |\n\n"
            "【换算技巧】\n"
            "• 两级单位之间的换算：连续乘或除（如 km→cm 要 ×1000×10）\n"
            "• 先统一单位再计算（如 2km + 300m = 2000m + 300m = 2300m）"
        ),
        "example": (
            "【例题1】在括号里填上合适的数\n"
            "(1) 5 km = ( ) m          → 5 × 1000 = **5000**\n"
            "(2) 4000 g = ( ) kg       → 4000 ÷ 1000 = **4**\n"
            "(3) 3 dm 5 cm = ( ) cm    → 3×10 + 5 = **35**\n"
            "(4) 2 t 50 kg = ( ) kg    → 2×1000 + 50 = **2050**\n\n"
            "【例题2】比较大小\n"
            "4 km ○ 3800 m  → 4 km = 4000 m > 3800 m → 填 **>**\n"
            "3 t ○ 3000 kg   → 3 t = 3000 kg → 填 **=**\n"
            "5 kg ○ 6000 g   → 5 kg = 5000 g < 6000 g → 填 **<**"
        ),
    },
    ("测量", "估测"): {
        "body": (
            "【什么是估测？】\n"
            "不用精确测量工具，通过观察、对比、参照来估计长度或质量的大小。\n\n"
            "【常用的身体「尺子」】\n"
            "• 一拃（拇指到中指张开）：约 **15~20 cm**\n"
            "• 一庹（两臂平伸）：约 **身高相近**（成人约 1.5~1.8 m）\n"
            "• 一步：约 **50~60 cm**\n"
            "• 指甲宽度：约 **1 cm**\n"
            "• 铅笔长度：约 **15~18 cm**\n\n"
            "【估测步骤】\n"
            "1. 选择合适的参照物（如一拃、一步）\n"
            "2. 数一数有几个参照物\n"
            "3. 估算总量\n"
            "4. 如果可能，再用工具精确测量对比\n\n"
            "【估测质量的方法】\n"
            "• 用手掂一掂，跟已知质量的物体对比\n"
            "• 参照常见物品：一袋盐 500g、一瓶水约 500g、一个鸡蛋约 50g"
        ),
        "example": (
            "【例题1】\n"
            "估一估：教室黑板的长大约有几米？宽呢？\n\n"
            "方法：用「一庹」来量，成人一庹约 1.5m\n"
            "黑板长约 3 庹 → 约 4.5 m\n"
            "黑板宽约 1 庼多一点 → 约 1.8 m\n\n"
            "---\n\n"
            "【例题2】\n"
            "选择合适的单位填空：\n"
            "(1) 一支粉笔长约 15 (**cm**)\n"
            "(2) 一辆卡车可载货 5 (**t**)\n"
            "(3) 小明身高 145 (**cm**)\n"
            "(4) 武汉到北京铁路长约 1200 (**km**)"
        ),
    },

    # ===== 万以内的加法和减法（三年级）=====
    ("万以内的加法和减法", "加法"): {
        "body": (
            "【万以内加法法则】\n\n"
            "相同数位对齐，从个位加起，哪一位满十就向前一位进 1。\n\n"
            "【竖式格式】\n"
            "  4 5 6\n"
            "+ 3 7 8\n"
            "-------\n"
            "  8 3 4\n\n"
            "【计算过程详解】\n"
            "• 个位：$6 + 8 = 14$ → 写 4，向十位**进 1**\n"
            "• 十位：$5 + 7 + 1$(进位) = 13 → 写 3，向百位**进 1**\n"
            "• 百位：$4 + 3 + 1$(进位) = 8 → 写 8\n"
            "• 结果：**834**\n\n"
            "【易错点提醒】\n"
            "① 忘记加进位的数字！进位标记要写清楚\n"
            "② 相同数位没有对齐（尤其是末尾有 0 时）\n"
            "③ 连续进位时漏算某一位的进位"
        ),
        "example": (
            "【例题1】计算 $385 + 476$\n"
            "  ³¹ \n"
            "  3 8 5\n"
            "+ 4 7 6\n"
            "-------\n"
            "  8 6 1\n\n"
            "讲解：个位 $5+6=11$ 进1；十位 $8+7+1=16$ 进1；百位 $3+4+1=8$\n\n"
            "答：$385 + 476 = $ **861**\n\n"
            "【例题2】计算 $708 + 2935$\n"
            "注意：位数不同时要右对齐！\n"
            "    ²¹\n"
            "  2 9 3 5\n"
            "+   7 0 8\n"
            "---------\n"
            "  3 6 4 3\n\n"
            "答：$708 + 2935 =$ **3643**"
        ),
    },
    ("万以内的加法和减法", "减法"): {
        "body": (
            "【万以内减法法则】\n\n"
            "相同数位对齐，从个位减起，哪一位不够减就从前一位退 1 当 10 再减。\n\n"
            "【退位（借位）的关键】\n"
            "前一位退 1 后，那一位上的数字要**减 1** 再参与计算！\n\n"
            "【竖式示例】$532 - 276$\n"
            "  ⁵³¹² \n"
            "  5 3 2\n"
            "- 2 7 6\n"
            "-------\n"
            "  2 5 6\n\n"
            "【逐位解析】\n"
            "• 个位：$2$ 不够减 $6$ → 从十位退 1 → $12 - 6 = 6$\n"
            "• 十位：3 被退走 1 剩 2，$2$ 不够减 7 → 从百位退 1 → $12 - 7 = 5$\n"
            "• 百位：5 被退走 1 剩 4 → $4 - 2 = 2$\n\n"
            "【中间/末尾有 0 的退位】\n"
            "这是最容易错的情况！\n"
            "$500 - 234$：个位 $0$不够→十位借，但十位也是 $0$ → 要从百位连退"
        ),
        "example": (
            "【例题1】$800 - 456 = ?$\n"
            "连续退位！\n"
            "  ⁷⁹⁹¹⁰\n"
            "  8 0 0\n"
            "- 4 5 6\n"
            "-------\n"
            "  3 4 4\n\n"
            "讲解：百位8退1变7→十位得10再退1变9→个位得10\n"
            "个位：$10-6=6$；十位：$9-5=4$；百位：$7-4=3$\n\n"
            "答：**344**\n\n"
            "【例题2】$1023 - 587 = ?$\n"
            "  ¹⁰¹²¹³\n"
            " 1 0 2 3\n"
            "-   5 8 7\n"
            "-------\n"
            "    4 3 6\n\n"
            "答：**436**"
        ),
    },
    ("万以内的加法和减法", "验算"): {
        "body": (
            "【为什么要验算？】\n"
            "验算是确认计算是否正确的有效方法，养成验算习惯可以大大减少错误。\n\n"
            "【加法的验算方法】\n"
            "方法一：**交换加数位置**再加一遍\n"
            "$a + b = b + a$（利用加法交换律）\n\n"
            "方法二：**和 − 一个加数 = 另一个加数**\n"
            "$(a+b) - a$ 应该等于 $b$\n\n"
            "【减法的验算方法】\n"
            "方法一：**差 + 减数 = 被减数**\n"
            "$(a-b) + b$ 应该等于 $a$\n\n"
            "方法二：**被减数 − 差 = 减数**\n"
            "$a - (a-b)$ 应该等于 $b$\n\n"
            "【验算习惯】\n"
            "做完一道计算题后，快速心算或笔算验算一遍，特别是考试时！"
        ),
        "example": (
            "【例题】计算 $567 + 389$ 并验算\n\n"
            "原计算：$567 + 389 = 956$\n\n"
            "验算方法一（交换加数）：\n"
            "$389 + 567 = 956$ ✓ 结果一致！\n\n"
            "验算方法二（和−加数）：\n"
            "$956 - 567 = 389$ ✓ 结果一致！\n\n"
            "结论：计算**正确**。"
        ),
    },
    ("万以内的加法和减法", "解决问题"): {
        "body": (
            "【加减法应用题的基本步骤】\n\n"
            "**第一步：认真读题**\n"
            "圈出已知条件和要求的问题。\n\n"
            "**第二步：分析关系**\n"
            "• 求总和 → 加法\n"
            "• 求剩余/相差 → 减法\n"
            "• 求比谁多多少/少多少 → 减法（大数减小数）\n\n"
            "**第三步：列式计算**\n"
            "写出算式，带上单位名称。\n\n"
            "**第四步：作答检查**\n"
            "写答句，检查答案是否合理。\n\n"
            "【常见题型】\n"
            "① 已知两部分求整体 → 合起来用加法\n"
            "② 已知整体和一部分求另一部分 → 用减法\n"
            "③ 比较两个量的大小差 → 大减小"
        ),
        "example": (
            "【例题1】\n"
            "图书馆原有图书 2450 本，又新买了 680 本。现在图书馆有多少本图书？\n\n"
            "分析：求整体 → 加法\n"
            "$2450 + 680 = 3130$（本）\n\n"
            "答：现在图书馆有 **3130 本**图书。\n\n"
            "---\n\n"
            "【例题2】\n"
            "超市运来 1000 千克苹果，第一天卖出 328 千克，第二天卖出 465 千克。还剩多少千克？\n\n"
            "方法一：$1000 - 328 - 465 = 207$（千克）\n"
            "方法二：先算卖出的总数 $328 + 465 = 793$（千克）\n"
            "$1000 - 793 = 207$（千克）\n\n"
            "答：还剩 **207 千克**。"
        ),
    },
    ("万以内的加法和减法", "估算"): {
        "body": (
            "【什么是估算？】\n"
            "不需要算出精确值，而是根据需要对数字进行近似处理后再计算，得到一个接近的结果。\n\n"
            "【估算方法】\n"
            "**四舍五入法**：把每个数看成接近的整百或整十数\n"
            "• 看十位：≥5 则往百位进1（舍去尾数）\n"
            "• 看个位：≥5 则往十位进1\n\n"
            "【估算的应用场景】\n"
            "① 快速判断答案的大致范围（检验计算是否离谱）\n"
            "② 买东西带够钱了吗？（往大估算更保险）\n"
            "③ 生活中不需要精确值的场合\n\n"
            "【估算原则】\n"
            "• 往大估（进一法）：买东西、装东西时确保足够\n"
            "• 往小估（去尾法）：时间安排等宁可保守\n"
            "• 一般情况：四舍五入最准确"
        ),
        "example": (
            "【例题1】\n"
            "估算 $398 + 215$ 约等于多少？\n\n"
            "$398 ≈ 400$，$215 ≈ 200$ 或 $220$\n"
            "$400 + 200 = 600$（或 $400 + 220 = 620$）\n\n"
            "精确值：$398 + 215 = 613$，估算 **600 左右** ✓\n\n"
            "---\n\n"
            "【例题2】\n"
            "妈妈带了 500 元去买东西：一件衣服 218 元，一条裤子 189 元。钱够吗？\n\n"
            "往大估：$218 ≈ 220$，$189 ≈ 190$（或都≈200）\n"
            "$220 + 190 = 410$ 元 < 500 元 → **够了**\n\n"
            "或者更粗略：$200 + 200 = 400 < 500$ → **肯定够**"
        ),
    },

    # ===== 多位数乘一位数（三年级）=====
    ("多位数乘一位数", "口算乘法"): {
        "body": (
            "【口算乘法基础】\n"
            "多位数乘一位数的口算，核心是把多位数拆成整十、整百数加上余数。\n\n"
            "【基本方法：拆分法】\n"
            "$23 \\times 4 = (20 + 3) \\times 4 = 20 \\times 4 + 3 \\times 4 = 80 + 12 = 92$\n\n"
            "【整十、整百数乘一位数】\n"
            "• $20 \\times 3 = 60$（想：2个十×3=6个十=60）\n"
            "• $200 \\times 3 = 600$（想：2个百×3=6个百=600）\n"
            "• 规律：末尾有几个 0，积的末尾就有几个 0\n\n"
            "【混合口算】\n"
            "$120 \\times 4 = ?$\n"
            "方法：先算 $12 \\times 4 = 48$，再在末尾添 1 个 0 → **480**\n\n"
            "⚠️ 注意：不要先丢掉 0 算，最后忘记添回去！"
        ),
        "example": (
            "【例题1】口算 $14 \\times 3$\n"
            "$14 \\times 3 = (10 + 4) \\times 3 = 10 \\times 3 + 4 \\times 3 = 30 + 12 = $ **42**\n\n"
            "【例题2】口算 $210 \\times 4$\n"
            "先算 $21 \\times 4 = 84$，末尾添 0 → **840**\n\n"
            "【例题3】口算 $320 \\times 3$\n"
            "$32 \\times 3 = 96$ → **960**"
        ),
    },
    ("多位数乘一位数", "笔算乘法"): {
        "body": (
            "【竖式乘法法则】\n"
            "相同数位对齐，从个位乘起，哪一位满几十就向前一位进几。\n\n"
            "【竖式示例】$123 \\times 4$\n"
            "    ¹ ²\n"
            "  1 2 3\n"
            "×   4\n"
            "-------\n"
            "  4 9 2\n\n"
            "【逐位解析】\n"
            "• 个位：$3 \\times 4 = 12$ → 写 2，向十位**进 1**\n"
            "• 十位：$2 \\times 4 = 8$，加进位 1 得 9\n"
            "• 百位：$1 \\times 4 = 4$\n"
            "• 结果：**492**\n\n"
            "【要点】\n"
            "① 每次都要乘遍每一位\n"
            "② 不要忘记加进位的数\n"
            "③ 书写要整齐，数位对齐"
        ),
        "example": (
            "【例题1】$214 \\times 3 = ?$\n"
            "  ¹\n"
            "  2 1 4\n"
            "×   3\n"
            "-------\n"
            "  6 4 2\n\n"
            "讲解：$4×3=12$进1；$1×3=3+1=4$；$2×3=6$\n\n"
            "答：**642**\n\n"
            "【例题2】$182 \\times 5 = ?$\n"
            "  ⁴¹\n"
            " 1 8 2\n"
            "×   5\n"
            "-------\n"
            " 9 1 0\n\n"
            "讲解：$2×5=10$写0进1；$8×5=40+1=41$写1进4；$1×5=5+4=9$\n\n"
            "答：**910**"
        ),
    },
    ("多位数乘一位数", "进位乘法"): {
        "body": (
            "【进位乘法的难点】\n"
            "当某一位相乘的结果 ≥ 10 时就需要进位，有时还需要**连续进位**。\n\n"
            "【进位规则】\n"
            "• 个位满十 → 向十位进\n"
            "• 十位满十（含来自个位的进位）→ 向百位进\n"
            "• 百位同理\n\n"
            "【连续进位的处理】\n"
            "$278 \\times 6$：\n"
            "• 个位：$8 \\times 6 = 48$ → 写 8，**进 4**\n"
            "• 十位：$7 \\times 6 = 42$，加进位 4 = 46 → 写 6，**进 4**\n"
            "• 百位：$2 \\times 6 = 12$，加进位 4 = 16 → 写 6，**进 1**\n"
            "• 千位：写进位 1\n"
            "• 结果：**1668**\n\n"
            "⚠️ 最容易出错的地方：只顾着乘，忘了加上一位进过来的数！"
        ),
        "example": (
            "【例题1】$467 \\times 3 = ?$\n"
            "  ¹²\n"
            "  4 6 7\n"
            "×   3\n"
            "-------\n"
            " 1 4 0 1\n\n"
            "讲解：$7×3=21$进2；$6×3=18+2=20$写0进2；$4×3=12+2=14$\n\n"
            "答：**1401**\n\n"
            "【例题2】$685 \\times 7 = ?$\n"
            "  ⁵⁵⁴\n"
            "  6 8 5\n"
            "×   7\n"
            "-------\n"
            " 4 7 9 5\n\n"
            "答：**4795**"
        ),
    },
    ("多位数乘一位数", "中间末尾有0"): {
        "body": (
            "【因数中间有 0 的情况】\n"
            "$102 \\times 4$：\n"
            "• 个位：$2 \\times 4 = 8$\n"
            "• **十位**：$0 \\times 4 = 0$（必须乘！不能跳过！）\n"
            "• 百位：$1 \\times 4 = 4$\n"
            "• 结果：**408**\n\n"
            "⚠️ **0 也要乘！** 不能因为 0 乘任何数都得 0 就跳过这一步！\n\n"
            "【因数末尾有 0 的情况】\n"
            "$260 \\times 3$：\n"
            "简便算法：先算 $26 \\times 3 = 78$，再在末尾添一个 0 → **780**\n\n"
            "也可以用竖式正常算（0 占位）：\n"
            "  2 6 0\n"
            "×   3\n"
            "-------\n"
            "  7 8 0"
        ),
        "example": (
            "【例题1】$105 \\times 6 = ?$\n"
            "  ³\n"
            " 1 0 5\n"
            "×   6\n"
            "-------\n"
            " 6 3 0\n\n"
            "讲解：$5×6=30$进3；$0×6=0+3=3$（0不能跳过）；$1×6=6$\n\n"
            "答：**630**\n\n"
            "【例题2】$480 \\times 5 = ?$\n"
            "$48 × 5 = 240$ → 末尾添 0 → **2400**"
        ),
    },
    ("多位数乘一位数", "解决问题"): {
        "body": (
            "【乘法应用题的类型】\n\n"
            "**类型一：求几个相同加数的和**\n"
            "「每盒有 6 支铅笔，买了 4 盒，共多少支？」\n"
            "→ $6 \\times 4 = 24$（支）\n\n"
            "**类型二：倍数问题**\n"
            "「小王有 5 本书，小李的书是小王的 3 倍」\n"
            "→ $5 \\times 3 = 15$（本）\n\n"
            "**类型三：单价×数量 = 总价**\n"
            "「每支钢笔 8 元，买 5 支多少钱？」\n"
            "→ $8 \\times 5 = 40$（元）\n\n"
            "**类型四：速度×时间 = 路程**\n"
            "「汽车每小时行 75 km，3 小时行多少？」\n"
            "→ $75 \\times 3 = 225$（km）"
        ),
        "example": (
            "【例题1】\n"
            "学校买了 3 台同样的电脑，每台 4208 元。一共花了多少钱？\n\n"
            "解：$4208 \\times 3 = 12624$（元）\n\n"
            "答：一共花了 **12624 元**。\n\n"
            "---\n\n"
            "【例题2】\n"
            "一场电影票价 35 元，3 个老师带 45 名学生去看电影。买票一共要花多少钱？\n\n"
            "分析：(老师人数 + 学生人数) × 票价\n"
            "$(3 + 45) \\times 35 = 48 \\times 35 = 1680$（元）\n\n"
            "答：买票一共要花 **1680 元**。"
        ),
    },

    # ===== 长方形和正方形（三年级）=====
    ("长方形和正方形", "四边形"): {
        "body": (
            "【什么是四边形？】\n"
            "由 **4 条直的边** 围成的封闭图形叫做四边形。\n\n"
            "【四边形的特征】\n"
            "① 有 **4 条边**\n"
            "② 有 **4 个角**\n"
            "③ 是**封闭图形**（首尾相连）\n\n"
            "【常见的四边形】\n"
            "• **长方形**：对边相等，4 个角都是直角\n"
            "• **正方形**：4条边都相等，4个角都是直角\n"
            "• **平行四边形**：对边平行且相等\n"
            "• **梯形**：只有一组对边平行\n"
            "• 一般四边形：不规则的四边形\n\n"
            "【不是四边形的例子】\n"
            "• 三角形（只有3条边）\n"
            "• 五边形（有5条边）\n"
            "• 有曲线边的图形（圆形、扇形等）"
        ),
        "example": (
            "【例题1】下面哪些图形是四边形？\n"
            "(A) 三角形 ✗（3条边）\n"
            "(B) 正方形 ✓（4条直边）\n"
            "(C) 圆 ✗（有曲线）\n"
            "(D) 平行四边形 ✓（4条直边）\n\n"
            "答：**(B) 和 (D)** 是四边形。\n\n"
            "【例题2】\n"
            "一个四边形的四条边分别是 5cm、3cm、5cm、3cm，四个角都是直角。这是什么图形？\n\n"
            "答：对边相等且有直角 → **长方形**。"
        ),
    },
    ("长方形和正方形", "长方形正方形特征"): {
        "body": (
            "【长方形的特征】\n"
            "• **边**：对边平行且相等（两条长相等，两条宽相等）\n"
            "• **角**：4个角都是**直角**($90°$)\n"
            "• **对角线**：相等且互相平分\n\n"
            "【正方形的特征】\n"
            "• **边**：**4条边都相等**\n"
            "• **角**：4个角都是**直角**($90°$)\n"
            "• 对角线：相等、互相垂直平分\n\n"
            "【长方形与正方形的关系】\n"
            "**正方形是特殊的长方形！**\n"
            "当长方形的「长 = 宽」时，它就成了正方形。\n\n"
            "分类关系：\n"
            "四边形 ⊃ 长方形 ⊃ 正方形\n"
            "（正方形属于长方形的一种特殊情况）\n\n"
            "【各部分名称】\n"
            "长方形：较长的边叫**长(a)**，较短的边叫**宽(b)**\n"
            "正方形：4条边都叫**边长(a)**"
        ),
        "example": (
            "【例题1】\n"
            "一个长方形的长是 8 cm，宽是 5 cm。它的对边各是多长？\n\n"
            "答：两条长都是 **8 cm**，两条宽都是 **5 cm**。\n\n"
            "---\n\n"
            "【例题2】\n"
            "用一根铁丝围成一个正方形，边长是 6 dm。如果改围成一个长 10 dm 的长方形，宽是多少？\n\n"
            "分析：铁丝长度不变（即周长相等）\n"
            "正方形周长 = $6 \\times 4 = 24$ dm\n"
            "长方形周长 = $(10 + 宽) \\times 2 = 24$\n"
            "$10 + 宽 = 12$ → 宽 = **2 dm**"
        ),
    },
    ("长方形和正方形", "周长"): {
        "body": (
            "【什么是周长？】\n"
            "封闭图形**一周的长度**叫做这个图形的周长。\n\n"
            "【周长的直观理解】\n"
            "想象沿着图形的边缘走一圈，走过的总路程就是周长。\n\n"
            "【长方形的周长公式】\n"
            "周长 = $($长 $+$ 宽$) \\times 2$\n"
            "$$C = (a + b) \\times 2$$\n\n"
            "也可以写成：$C = a + b + a + b = 2a + 2b$\n\n"
            "【正方形的周长公式】\n"
            "周长 = 边长 $\\times 4$\n"
            "$$C = 4a$$\n\n"
            "【为什么这样算？】\n"
            "• 长方形：2条长 + 2条宽 = 长+宽+长+宽 = (长+宽)×2\n"
            "• 正方形：4条相等的边 = 边长×4"
        ),
        "example": (
            "【例题1】\n"
            "一个长方形花坛，长 12 米，宽 8 米。这个花坛的周长是多少米？\n\n"
            "解：$(12 + 8) \\times 2 = 20 \\times 2 = 40$（米）\n\n"
            "答：周长是 **40 米**。\n\n"
            "---\n\n"
            "【例题2】\n"
            "一个正方形手帕，边长 25 厘米。给它缝上一圈花边，需要多长的花边？\n\n"
            "解：$25 \\times 4 = 100$（厘米）\n\n"
            "答：需要 **100 厘米**（即 1 米）长的花边。"
        ),
    },
    ("长方形和正方形", "周长计算"): {
        "body": (
            "【已知周长求边长】\n\n"
            "**长方形**：已知周长和长（或宽），求另一边\n"
            "• 宽 = 周长 ÷ 2 − 长\n"
            "• 长 = 周长 ÷ 2 − 宽\n\n"
            "**正方形**：已知周长求边长\n"
            "• 边长 = 周长 ÷ 4\n\n"
            "【巧算周长的技巧】\n\n"
            "**技巧一：利用平移法**\n"
            "有些凹凸图形可以通过平移线段转化成长方形来求周长。\n\n"
            "**技巧二：利用对称性**\n"
            "利用对边相等简化计算。\n\n"
            "**技巧三：拼接与分割**\n"
            "• 两个相同长方形拼成长方形：周长会减少 2 条拼接的边\n"
            "• 一个长方形剪成两个小长方形：周长会增加 2 条切口"
        ),
        "example": (
            "【例题1】\n"
            "一个长方形的周长是 36 厘米，长是 12 厘米。宽是多少厘米？\n\n"
            "解：$36 \\div 2 - 12 = 18 - 12 = 6$（厘米）\n\n"
            "验算：$(12 + 6) \\times 2 = 36$ ✓\n\n"
            "答：宽是 **6 厘米**。\n\n"
            "---\n\n"
            "【例题2】\n"
            "一个正方形的周长是 64 分米，边长是多少分米？\n\n"
            "解：$64 \\div 4 = 16$（分米）\n\n"
            "答：边长是 **16 分米**。"
        ),
    },
    ("长方形和正方形", "拼图求周长"): {
        "body": (
            "【图形拼接后的周长变化】\n\n"
            "**两个相同的长方形拼在一起**\n"
            "假设每个长方形长 a、宽 b：\n\n"
            "沿**长边**拼接（短边重合）：\n"
            "新长方形：长 = a，宽 = 2b\n"
            "新周长 = $(a + 2b) \\times 2 = 2a + 4b$\n"
            "原来总周长 = $2(a+b) \\times 2 = 4a + 4b$\n"
            "**周长减少了 2b**（少了 2 条重合的宽边）\n\n"
            "沿**宽边**拼接（长边重合）：\n"
            "新长方形：长 = 2a，宽 = b\n"
            "新周长 = $(2a + b) \\times 2 = 4a + 2b$\n"
            "**周长减少了 2a**（少了 2 条重合的长边）\n\n"
            "【分割图形】\n"
            "一个大长方形剪成两个小长方形：\n"
            "周长增加 2 条切口的边长"
        ),
        "example": (
            "【例题1】\n"
            "两个完全相同的长方形，长 6 厘米，宽 3 厘米。把它们拼成一个大长方形，周长最大是多少？最小是多少？\n\n"
            "分析有两种拼法：\n\n"
            "拼法一（沿宽边拼）：新尺寸 $12 \\times 3$\n"
            "周长 = $(12 + 3) \\times 2 = 30$ cm\n\n"
            "拼法二（沿长边拼）：新尺寸 $6 \\times 6$（变成正方形！）\n"
            "周长 = $6 \\times 4 = 24$ cm\n\n"
            "答：周长最大 **30 cm**，最小 **24 cm**。\n\n"
            "---\n\n"
            "【例题2】\n"
            "用 3 个边长 2 cm 的正方形拼成一排（一字排开），拼成的长方形周长是多少？\n\n"
            "新长方形：长 $2 \\times 3 = 6$ cm，宽 2 cm\n"
            "周长 = $(6 + 2) \\times 2 = 16$ cm\n\n"
            "答：**16 厘米**。"
        ),
    },

    # ===== 分数的初步认识（三年级）=====
    ("分数的初步认识", "分数的意义"): {
        "body": (
            "【什么是分数？】\n"
            "把一个整体**平均分成**若干份，表示这样的**一份或几份**的数，叫做分数。\n\n"
            "【分数的各部分名称】\n"
            "$\\frac{3}{4}$ 读作「四分之一」…不对！读作「**四分之三**」\n\n"
            "• **分子(3)**：取了多少份\n"
            "• **分数线(—)**：表示平均分\n"
            "• **分母(4)**：平均分成了几份\n\n"
            "【关键理解】\n"
            "① 必须是「**平均分**」！（不是随便切）\n"
            "② 分母表示分的总份数\n"
            "③ 分子表示取的份数\n\n"
            "【生活中的分数】\n"
            "• 半个月 = $\\frac{1}{2}$ 个月\n"
            "• 一节课用了 $\\frac{1}{3}$ 在讲新课\n"
            "• 吃了一个西瓜的 $\\frac{3}{8}$"
        ),
        "example": (
            "【例题1】\n"
            "把一张长方形纸平均分成 5 份，每份是这张纸的几分之几？取了 3 份呢？\n\n"
            "答：每份是 $\\frac{1}{5}$，3 份是 $\\frac{3}{5}$。\n\n"
            "---\n\n"
            "【例题2】\n"
            "用分数表示下面的涂色部分：\n"
            "一个圆被平均分成了 8 份，其中 5 份涂色\n\n"
            "答：$\\frac{5}{8}$（八分之五）\n\n"
            "---\n\n"
            "【例题3】判断对错】\n"
            "「把一块蛋糕分成 4 份，每份是 $\\frac{1}{4}$」✗\n\n"
            "原因：没有说**平均分**！如果切得大小不一，每份就不是 $\\frac{1}{4}$。"
        ),
    },
    ("分数的初步认识", "几分之一"): {
        "body": (
            "【几分之一的含义】\n"
            "分子为 1 的分数（如 $\\frac{1}{2}, \\frac{1}{3}, \\frac{1}{4}...$）表示其中的**一份**。\n\n"
            "【几分之一的大小比较】\n"
            "**分母越大，分数反而越小！**\n\n"
            "这是因为分母越大，表示平均分的份数越多，每一份就越小。\n\n"
            "$\\frac{1}{2} > \\frac{1}{3} > \\frac{1}{4} > \\frac{1}{5}$\n\n"
            "【直观理解】\n"
            "同样大的蛋糕：\n"
            "• 平均分给 2 人 →每人得到 $\\frac{1}{2}$（较多）\n"
            "• 平均分给 4 人 →每人得到 $\\frac{1}{4}$（较少）\n\n"
            "人越多，每个人分到的越少！"
        ),
        "example": (
            "【例题1】比较大小\n"
            "(1) $\\frac{1}{4}$ ○ $\\frac{1}{6}$ → **>**（4<6，所以1/4更大）\n"
            "(2) $\\frac{1}{8}$ ○ $\\frac{1}{3}$ → **<**（8>3，所以1/8更小）\n\n"
            "---\n\n"
            "【例题2】\n"
            "有三根同样长的绳子，第一根用去 $\\frac{1}{2}$，第二根用去 $\\frac{1}{3}$，第三根用去 $\\frac{1}{6}$。哪根剩下的最长？\n\n"
            "分析：用去的越少，剩下的越多\n"
            "$\\frac{1}{6} < \\frac{1}{3} < \\frac{1}{2}$ → 第三根用去最少\n\n"
            "答：**第三根**剩下的最长。"
        ),
    },
    ("分数的初步认识", "几分之几"): {
        "body": (
            "【几分之几的含义】\n"
            "分子大于 1 的分数（如 $\\frac{3}{4}, \\frac{5}{8}...$）表示其中的**几份**。\n\n"
            "$\\frac{3}{4}$ = 3 个 $\\frac{1}{4}$ = $\\frac{1}{4} + \\frac{1}{4} + \\frac{1}{4}$\n\n"
            "【同分母分数的大小比较】\n"
            "分母相同（即每一份一样大）时，**分子越大，分数越大**。\n\n"
            "$\\frac{2}{5} < \\frac{3}{5} < \\frac{4}{5}$\n\n"
            "理由：每一份都是 $\\frac{1}{5}$，2份 < 3份 < 4份\n\n"
            "【真分数 vs 假分数】（初步了解）\n"
            "• **真分数**：分子 < 分母（值小于1）\n"
            "• **假分数**：分子 ≥ 分母（值大于或等于1）\n\n"
            "三年级主要学习真分数。"
        ),
        "example": (
            "【例题1】比较大小\n"
            "(1) $\\frac{3}{7}$ ○ $\\frac{5}{7}$ → **<**（3份<5份）\n"
            "(2) $\\frac{6}{9}$ ○ $\\frac{2}{9}$ → **>**（6份>2份）\n\n"
            "---\n\n"
            "【例题2】\n"
            "一本书，小明第一天看了全书的 $\\frac{2}{7}$，第二天看了全书的 $\\frac{4}{7}$。两天一共看了几分之几？还剩几分之几？\n\n"
            "已看：$\\frac{2}{7} + \\frac{4}{7} = \\frac{6}{7}$\n"
            "还剩：$1 - \\frac{6}{7} = \\frac{1}{7}$（把全书看成 $\\frac{7}{7}$）\n\n"
            "答：两天看了 **$\\frac{6}{7}$**，还剩 **$\\frac{1}{7}$**。"
        ),
    },
    ("分数的初步认识", "大小比较"): {
        "body": (
            "【分数大小比较总结】\n\n"
            "**情况一：同分母分数**\n"
            "分母相同 → 每份大小相同 → 直接比分子\n"
            "分子大的分数大\n"
            "$\\frac{3}{5} > \\frac{2}{5}$ ✓\n\n"
            "**情况二：同分子分数（分子都是1）**\n"
            "分子相同（都是1份）→ 分母越大每份越小\n"
            "分母大的反而小\n"
            "$\\frac{1}{3} > \\frac{1}{5}$ ✓\n\n"
            "**情况三：一般情况**（三年级暂不需掌握）\n"
            "通分后再比较（以后会学到）\n\n"
            "【记忆口诀】\n"
            "同分母，比分子（分子大的大）\n"
            "同分子（都是1），比分母（分母大的反而小）"
        ),
        "example": (
            "【例题】把下面各组分数按从小到大排列\n\n"
            "(1) $\\frac{1}{3}, \\frac{1}{5}, \\frac{1}{2}$\n"
            "分母：5 > 3 > 2 → 分数：$\\frac{1}{5} < \\frac{1}{3} < \\frac{1}{2}$\n\n"
            "(2) $\\frac{4}{9}, \\frac{2}{9}, \\frac{7}{9}$\n"
            "分子：2 < 4 < 7 → 分数：$\\frac{2}{9} < \\frac{4}{9} < \\frac{7}{9}$\n\n"
            "(3) $\\frac{1}{4}, \\frac{3}{4}, \\frac{1}{6}$\n"
            "先分组：$\\frac{1}{6} < \\frac{1}{4} < \\frac{3}{4}$"
        ),
    },
    ("分数的初步认识", "简单加减"): {
        "body": (
            "【同分母分数加减法】\n\n"
            "**加法**：分母不变，分子相加\n"
            "$$\\frac{a}{c} + \\frac{b}{c} = \\frac{a+b}{c}$$\n\n"
            "**减法**：分母不变，分子相减\n"
            "$$\\frac{a}{c} - \\frac{b}{c} = \\frac{a-b}{c}$$\n\n"
            "【为什么分母不变？】\n"
            "分母表示「每一份的大小」，既然每份大小相同（都是 $\\frac{1}{c}$），加减的时候只需要数「有几份」就行。\n\n"
            "就像：3个苹果 + 2个苹果 = 5个苹果（「苹果」这个单位没变）\n\n"
            "【计算步骤】\n"
            "1. 确认分母相同\n"
            "2. 分子做加减\n"
            "3. 分母照抄\n"
            "4. 能约分的要约分（最简形式）"
        ),
        "example": (
            "【例题1】$\\frac{2}{7} + \\frac{3}{7} = ?$\n"
            "解：$\\frac{2+3}{7} = \\frac{5}{7}$\n\n"
            "【例题2】$\\frac{5}{8} - \\frac{3}{8} = ?$\n"
            "解：$\\frac{5-3}{8} = \\frac{2}{8} = \\frac{1}{4}$（约分！）\n\n"
            "【例题3】一块蛋糕，爸爸吃了 $\\frac{3}{8}$，妈妈吃了 $\\frac{2}{8}$。两人一共吃了几分之几？还剩几分之几？\n\n"
            "共吃：$\\frac{3}{8} + \\frac{2}{8} = \\frac{5}{8}$\n"
            "还剩：$1 - \\frac{5}{8} = \\frac{8}{8} - \\frac{5}{8} = \\frac{3}{8}$\n\n"
            "答：两人吃了 **$\\frac{5}{8}$**，还剩 **$\\frac{3}{8}$**。"
        ),
    },

    # ===== 数学广角·集合（三年级）=====
    ("数学广角·集合", "韦恩图"): {
        "body": (
            "【什么是韦恩图？】\n"
            "韦恩图（也叫维恩图）是用**重叠的圆圈**来表示不同集合之间关系的图形。\n\n"
            "【基本结构】\n\n"
            "  A 圆         B 圆\n"
            " ┌─────┐   ┌─────┐\n"
            " │ 只A │   │ 只B │\n"
            " │     ├───┤     │ ← 重叠区域（既A又B）\n"
            " └─────┘   └─────┘\n"
            "   外面 = 既非A也非B\n\n"
            "【各区域的含义】\n"
            "• 左边月牙形：只在 A 中（不在 B 中）\n"
            "• 右边月牙形：只在 B 中（不在 A 中）\n"
            "• 中间交集：既在 A 中又在 B 中\n"
            "• 外面：既不在 A 中也不在 B 中\n\n"
            "【韦恩图的用途】\n"
            "解决「重复计数」问题——避免同一个元素被算了两遍！"
        ),
        "example": (
            "【例题】\n"
            "三(1)班参加语文小组的有 8 人，参加数学小组的有 9 人，两个小组都参加的有 4 人。全班参加课外小组的一共有多少人？\n\n"
            "画韦恩图：\n"
            "• 只语文：$8 - 4 = 4$ 人\n"
            "• 只数学：$9 - 4 = 5$ 人\n"
            "• 都参加：4 人\n\n"
            "总计：$4 + 5 + 4 = 13$（人）\n\n"
            "或者用容斥原理：$8 + 9 - 4 = 13$（人）\n"
            "（语文人数 + 数学人数 - 重复计算的）\n\n"
            "答：一共有 **13 人**参加课外小组。"
        ),
    },
    ("数学广角·集合", "重叠问题"): {
        "body": (
            "【重叠问题的本质】\n"
            "两个集合有公共元素时，直接相加会把公共元素**重复计算了一次**，需要减去重复的部分。\n\n"
            "【容斥原理公式】\n"
            "$$A ∪ B 的总个数 = A的个数 + B的个数 - 重叠的个数$$\n\n"
            "通俗记忆：「加起来，减去多算的」\n\n"
            "【三种情况的计算】\n\n"
            "**① 求总人数**\n"
            "总数 = 只A + 只B + 两者都\n"
            "或 总数 = A组人数 + B组人数 - 重叠人数\n\n"
            "**② 求只属于某一组的人数**\n"
            "只A = A组人数 - 重叠人数\n"
            "只B = B组人数 - 重叠人数\n\n"
            "**③ 求重叠人数**\n"
            "重叠 = A组人数 + B组人数 - 总人数"
        ),
        "example": (
            "【例题1】\n"
            "班里同学喜欢唱歌的有 20 人，喜欢跳舞的有 18 人，两项都喜欢的有 8 人。每人都至少喜欢一项。全班多少人？\n\n"
            "解：$20 + 18 - 8 = 30$（人）\n\n"
            "答：全班 **30 人**。\n\n"
            "---\n\n"
            "【例题2】\n"
            "同学们去春游，带水的有 25 人，带面包的有 20 人，两样都没带的 2 人，两样都带的有 10 人。一共多少人？\n\n"
            "解：至少带一样的 = $25 + 20 - 10 = 35$（人）\n"
            "总人数 = $35 + 2 = 37$（人）\n\n"
            "答：一共 **37 人**。"
        ),
    },
    ("数学广角·集合", "只A"): {
        "body": (
            "【什么叫做「只A」？】\n"
            "在韦恩图中，「只 A」指的是**属于 A 但不属于 B** 的元素，即左边月牙形的区域。\n\n"
            "【计算方法】\n"
            "**只 A = A 的总个数 − A 和 B 重叠的个数**\n\n"
            "【生活实例】\n"
            "「参加美术组但不参加音乐组的人数」\n"
            "= 美术组总人数 - 两组都参加的人数\n\n"
            "【理解关键】\n"
            "A 组的人数包含了「只 A」和「两者都」两部分。\n"
            "所以要得到纯的「只 A」，就要从 A 组中扣除重叠部分。"
        ),
        "example": (
            "【例题】\n"
            "三(2)班有 45 人，喜欢足球的有 28 人，喜欢篮球的有 24 人，两项都喜欢的有 12 人。\n"
            "(1) 只喜欢足球的有几人？\n"
            "(2) 只喜欢篮球的有几人？\n"
            "(3) 两项都不喜欢的有几人？\n\n"
            "解：\n"
            "(1) 只足球 = $28 - 12 = 16$（人）\n"
            "(2) 只篮球 = $24 - 12 = 12$（人）\n"
            "(3) 都不喜欢 = $45 - (16 + 12 + 12) = 45 - 40 = 5$（人）\n\n"
            "答：只喜欢足球 **16 人**，只喜欢篮球 **12 人**，都不喜欢 **5 人**。"
        ),
    },
    ("数学广角·集合", "只B"): {
        "body": (
            "【什么叫做「只B」？】\n"
            "与「只 A」类似，「只 B」指的是**属于 B 但不属于 A** 的元素，即右边月牙形区域。\n\n"
            "【计算方法】\n"
            "**只 B = B 的总个数 − A 和 B 重叠的个数**\n\n"
            "【与「只A」的对称性】\n"
            "韦恩图左右两边是对称的，计算方法完全对应：\n"
            "• 只 A = A总数 − 重叠\n"
            "• 只 B = B总数 − 重叠\n\n"
            "【实用价值】\n"
            "知道「只 A」和「只 B」的人数可以帮助我们精确定位各类人群，做出更有针对性的安排。"
        ),
        "example": (
            "【例题】\n"
            "学校组织兴趣小组报名：科技组报了 30 人，绘画组报了 25 人，两组都报的有 10 人。\n"
            "(1) 只报了科技组的几人？\n"
            "(2) 只报了绘画组的几人？\n"
            "(3) 两组一共多少人参加？\n\n"
            "解：\n"
            "(1) 只科技组 = $30 - 10 = 20$（人）\n"
            "(2) 只绘画组 = $25 - 10 = 15$（人）\n"
            "(3) 总计 = $20 + 15 + 10 = 45$（人）\n"
            "或 $30 + 25 - 10 = 45$（人）\n\n"
            "答：只科技组 **20 人**，只绘画组 **15 人**，共 **45 人**。"
        ),
    },
    ("数学广角·集合", "应用"): {
        "body": (
            "【集合思想在实际中的应用】\n\n"
            "**应用一：统计调查**\n"
            "统计班级同学的爱好分布，避免重复计数。\n\n"
            "**应用二：商品推荐**\n"
            "电商网站分析用户的购买行为：买过 A 类商品的用户中有多少也买了 B 类商品。\n\n"
            "**应用三：排课/排班**\n"
            "安排选修课教室时，需要知道选了这两门课的总人数（排除重复的人）。\n\n"
            "**应用四：信息检索**\n"
            "搜索引擎查找包含关键词 A 或 B 的网页数。\n\n"
            "【解题通用步骤】\n"
            "1. 识别题目中的两个集合是什么\n"
            "2. 找出各自的总数和重叠数\n"
            "3. 画简单的韦恩草图辅助理解\n"
            "4. 选择合适公式计算\n"
            "5. 验证答案合理性"
        ),
        "example": (
            "【例题】\n"
            "四年级 100 名学生中：\n"
            "• 会游泳的有 65 人\n"
            "• 会骑自行车的有 73 人\n"
            "• 两项都不会的有 6 人\n\n"
            "问：两项都会的有多少人？\n\n"
            "分析：\n"
            "至少会一项的 = $100 - 6 = 94$（人）\n"
            "根据容斥原理：\n"
            "$94 = 65 + 73 - x$\n"
            "$x = 65 + 73 - 94 = 138 - 94 = 44$（人）\n\n"
            "验证：只游泳 = $65-44=21$；只骑车 = $73-44=29$\n"
            "$21 + 29 + 44 + 6 = 100$ ✓\n\n"
            "答：两项都会的有 **44 人**。"
        ),
    },

    # ===== 圆（六年级）——补充剩余条目 =====
    ("圆", "扇形"): {
        "body": (
            "【什么是扇形？】\n"
            "由圆的两条半径和它们所夹的一段弧组成的图形叫做**扇形**。\n\n"
            "【扇形的组成】\n"
            "• **圆心角(n°)**：两条半径之间的夹角\n"
            "• **弧**：圆周的一部分\n"
            "• **两条半径**：从圆心到弧的两个端点\n\n"
            "【扇形的面积公式】\n"
            "扇形面积 = 整圆面积 × (圆心角度数 / 360°)\n"
            "$$S_{扇形} = \\frac{n}{360} \\times \\pi r^2$$\n\n"
            "【扇形的弧长公式】\n"
            "弧长 = 整圆周长 × (圆心角度数 / 360°)\n"
            "$$l_{弧} = \\frac{n}{360} \\times 2\\pi r = \\frac{n\\pi r}{180}$$\n\n"
            "【常见扇形】\n"
            "• 90° 扇形 = 四分之一圆（$\\frac{1}{4}$圆）\n"
            "• 180° 扇形 = 半圆（$\\frac{1}{2}$圆）\n"
            "• 270° 扇形 = 四分之三圆（$\\frac{3}{4}$圆）"
        ),
        "example": (
            "【例题】\n"
            "一个扇形的圆心角是 120°，所在圆的半径是 6 cm。求这个扇形的面积和弧长。\n\n"
            "解面积：\n"
            "$S = \\frac{120}{360} \\times 3.14 \\times 6^2$\n"
            "$= \\frac{1}{3} \\times 3.14 \\times 36 = 37.68$ cm²\n\n"
            "解弧长：\n"
            "$l = \\frac{120}{360} \\times 2 \\times 3.14 \\times 6$\n"
            "$= \\frac{1}{3} \\times 37.68 = 12.56$ cm\n\n"
            "答：面积 **37.68 cm²**，弧长 **12.56 cm**。"
        ),
    },
    ("圆", "组合图形"): {
        "body": (
            "【圆与其他图形的组合】\n"
            "在实际问题中，经常遇到圆与长方形、正方形或其他图形的组合。\n\n"
            "【常见组合类型】\n\n"
            "**类型一：外方内圆**（正方形内有一个最大的圆）\n"
            "圆的直径 = 正方形的边长\n"
            "圆的半径 = 边长 ÷ 2\n\n"
            "**类型二：外圆内方**（圆内有一个最大的正方形）\n"
            "正方形的对角线 = 圆的直径\n"
            "正方形面积 = 对角线² ÷ 2 = (2r)² ÷ 2 = 2r²\n\n"
            "**类型三：半圆组合**\n"
            "两个半圆可以拼成一个整圆\n"
            "半圆面积 = $\\frac{1}{2}\\pi r^2$\n\n"
            "**类型四：圆环（同心圆）**\n"
            "大圆内部挖去一个小圆\n"
            "圆环面积 = $\\pi R^2 - \\pi r^2 = \\pi(R^2 - r^2)$"
        ),
        "example": (
            "【例题1】\n"
            "在一个边长 10 cm 的正方形纸片上剪一个最大的圆，这个圆的面积是多少？剩下部分的面积是多少？\n\n"
            "解：最大圆的直径 = 正方形边长 = 10 cm\n"
            "半径 r = 5 cm\n"
            "圆面积 = $3.14 \\times 5^2 = 78.5$ cm²\n"
            "剩余面积 = $10^2 - 78.5 = 100 - 78.5 = 21.5$ cm²\n\n"
            "---\n\n"
            "【例题2】\n"
            "一个圆形花坛的周围铺了一条 2 米宽的小路（圆环形），花坛半径 5 米。小路的面积是多少？\n\n"
            "解：外圆 R = $5 + 2 = 7$ m\n"
            "内圆 r = 5 m\n"
            "圆环面积 = $3.14 \\times (7^2 - 5^2) = 3.14 \\times (49 - 25) = 3.14 \\times 24 = 75.36$ m²\n\n"
            "答：小路面积 **75.36 m²**。"
        ),
    },

    # ===== 分数乘法（六年级）——补充剩余条目 =====
    ("分数乘法", "小数乘分数"): {
        "body": (
            "【小数乘分数的计算方法】\n\n"
            "**方法一：把小数化成分数再乘**\n"
            "$0.5 \\times \\frac{2}{3} = \\frac{1}{2} \\times \\frac{2}{3} = \\frac{1}{3}$\n\n"
            "**方法二：把分数化成小数再乘**（适用于能化成有限小数的）\n"
            "$\\frac{1}{4} \\times 0.8 = 0.25 \\times 0.8 = 0.2$\n\n"
            "**方法三：直接约分（推荐！）**\n"
            "$0.75 \\times \\frac{4}{5} = \\frac{3}{4} \\times \\frac{4}{5} = \\frac{3}{5}$\n"
            "先把小数化成分数，然后按分数乘法计算\n\n"
            "【选择方法的建议】\n"
            "• 小数能简单化为分数时 → 化成分数再乘\n"
            "• 分数能简单化为有限小数时 → 化为小数再乘\n"
            "• 都不太方便时 → 直接按小数×分数算"
        ),
        "example": (
            "【例题1】$1.2 \\times \\frac{3}{4} = ?$\n"
            "解：$1.2 = \\frac{6}{5}$\n"
            "$$\\frac{6}{5} \\times \\frac{3}{4} = \\frac{18}{20} = \\frac{9}{10} = 0.9$$\n\n"
            "【例题2】一根绳子长 $\\frac{4}{5}$ 米，$2.5$ 根这样的绳子长多少米？\n"
            "解：$\\frac{4}{5} \\times 2.5 = \\frac{4}{5} \\times \\frac{5}{2} = 2$（米）\n\n"
            "答：长 **2 米**。"
        ),
    },
    ("分数乘法", "整数乘法运算律"): {
        "body": (
            "【整数乘法运算律对分数同样适用！】\n\n"
            "**乘法交换律**：$a \\times b = b \\times a$\n"
            "$$\\frac{3}{4} \\times \\frac{5}{7} = \\frac{5}{7} \\times \\frac{3}{4}$$\n\n"
            "**乘法结合律**：$(a \\times b) \\times c = a \\times (b \\times c)$\n"
            "$$(\\frac{2}{3} \\times \\frac{5}{6}) \\times \\frac{3}{5} = \\frac{2}{3} \\times (\\frac{5}{6} \\times \\frac{3}{5})$$\n\n"
            "**乘法分配律**：$(a + b) \\times c = a \\times c + b \\times c$\n"
            "$$(\\frac{3}{5} + \\frac{1}{2}) \\times \\frac{2}{3} = \\frac{3}{5} \\times \\frac{2}{3} + \\frac{1}{2} \\times \\frac{2}{3}$$\n\n"
            "【运用分配律进行简便计算】\n"
            "提取公因数：$\\frac{5}{9} \\times \\frac{3}{4} + \\frac{5}{9} \\times \\frac{1}{4} = \\frac{5}{9} \\times (\\frac{3}{4} + \\frac{1}{4}) = \\frac{5}{9} \\times 1 = \\frac{5}{9}$"
        ),
        "example": (
            "【例题1】简便计算：$\\frac{5}{9} \\times \\frac{3}{4} + \\frac{5}{9} \\times \\frac{1}{4}$\n"
            "解：提取公因数 $\\frac{5}{9}$\n"
            "$$\\frac{5}{9} \\times (\\frac{3}{4} + \\frac{1}{4}) = \\frac{5}{9} \\times 1 = \\frac{5}{9}$$\n\n"
            "【例题2】简便计算：$\\frac{7}{8} \\times 99 + \\frac{7}{8}$\n"
            "解：$\\frac{7}{8} \\times (99 + 1) = \\frac{7}{8} \\times 100 = \\frac{700}{8} = 87.5$"
        ),
    },
    ("分数乘法", "解决问题"): {
        "body": (
            "【分数乘法应用题的主要类型】\n\n"
            "**类型一：求一个数的几分之几是多少**\n"
            "「修路队修了一条 $\\frac{4}{5}$ km 长的路，已经修了全长的 $\\frac{3}{4}$，修了多少 km？」\n"
            "→ $\\frac{4}{5} \\times \\frac{3}{4} = \\frac{3}{5}$（km）\n\n"
            "**类型二：连续求几分之几**\n"
            "「一班有 45 人，其中 $\\frac{4}{9}$ 是女生，女生中有 $\\frac{1}{5}$ 戴眼镜。戴眼镜的女生有多少人？」\n"
            "→ $45 \\times \\frac{4}{9} \\times \\frac{1}{5} = 4$（人）\n\n"
            "**类型三：比一个数多（少）几分之几**\n"
            "「今年的产量比去年多 $\\frac{1}{5}$」\n"
            "→ 今年 = 去年 × $(1 + \\frac{1}{5})$"
        ),
        "example": (
            "【例题1】\n"
            "六年级有 150 人参加体育活动，其中参加跑步的占 $\\frac{2}{5}$，参加跳绳的是跑步人数的 $\\frac{1}{2}$。参加跳绳的有多少人？\n\n"
            "解：$150 \\times \\frac{2}{5} \\times \\frac{1}{2} = 60 \\times \\frac{1}{2} = 30$（人）\n\n"
            "答：参加跳绳的有 **30 人**。\n\n"
            "---\n\n"
            "【例题2】\n"
            "食堂买来 $\\frac{4}{5}$ 吨大米，第一周吃了总数的 $\\frac{1}{4}$，第二周吃了总数的 $\\frac{2}{5}$。还剩多少吨？\n\n"
            "解：吃了：$\\frac{4}{5} \\times (\\frac{1}{4} + \\frac{2}{5}) = \\frac{4}{5} \\times \\frac{13}{20} = \\frac{13}{25}$（吨）\n"
            "还剩：$\\frac{4}{5} - \\frac{13}{25} = \\frac{20}{25} - \\frac{13}{25} = \\frac{7}{25}$（吨）\n\n"
            "答：还剩 **$\\frac{7}{25}$ 吨**。"
        ),
    },

    # ===== 倍的认识 =====
    ("倍的认识", "倍的概念"): [
        "倍是关系不是具体数字：「A是B的3倍」表示比较关系，不要把倍当成单位",
        "0不能做标准量：求谁是谁的几倍时，除数（标准量）不能为0",
        "倍可以是非整数：6是14的几倍？6÷14=3/7（不一定是整倍数）",
    ],
    ("倍的认识", "求一个数是几倍"): [
        "顺序搞反：A是B的几倍 → A÷B（被除数是「是」前面的那个数）",
        "找错标准量：「A比B多几倍」的标准量还是B，不是多出来的部分",
        "忘记写单位：倍数的单位写「倍」，不带其他单位名",
    ],
    ("倍的认识", "求一个数的几倍"): [
        "混淆乘除法：「求几倍」用乘法，「是几倍」用除法，看准关键字",
        "漏算多几少几：A的n倍多b → A×n + b，别忘了最后加或减",
    ],
    ("倍的认识", "画图解题"): [
        "线段长度要大致反映比例：如果A是B的3倍，A的线段大约画成B的3倍长",
        "忘记标注份数和具体数量：画图后要在每段上标清楚代表多少",
    ],
    ("倍的认识", "应用"): [
        "和倍问题忘记加1：总份数 = 倍数 + 1，不要只按倍数来分",
        "差倍问题忘记减1：差的对应份数 = 倍数 - 1",
        "年龄问题中差不变：无论过多少年，两人的年龄差始终不变",
    ],

    # ===== 测量 =====
    ("测量", "毫米分米"): [
        "进率记错：相邻长度单位进率都是10，但km→m是1000",
        "单位名称写错：mm/cm/dm 不要混用符号",
    ],
    ("测量", "千米"): [
        "千米与米之间进率是1000不是100！这是最常见的错误",
        "估算距离时偏差大：记住操场一圈约400m，2圈半≈1km",
    ],
    ("测量", "吨"): [
        "吨与千克进率1000，跟km→m一样",
        "质量单位和长度单位混淆：t/kg/g 是重量，km/m/cm/mm 是长度",
    ],
    ("测量", "单位换算"): [
        "高级转低级要乘、低级转高级要除，方向反了结果差很远",
        "复合单位拆开算：如 3dm5cm = 3×10+5 = 35cm",
    ],

    # ===== 万以内加减法 =====
    ("万以内的加法和减法", "加法"): [
        "忘记进位：哪一位满十就要向前一位进1，标记要写上",
        "连续进位漏算：个位进的十位没加，十位又向百位进了",
        "位数不对齐：末尾有0的数相加时要右对齐",
    ],
    ("万以内的加法和减法", "减法"): [
        "退位后前一位没减1：退位后那一位要先减1再参与计算",
        "连续退位出错：中间有0的退位最容易错（如500-234）",
    ],

    # ===== 多位数乘一位数 =====
    ("多位数乘一位数", "口算乘法"): [
        "末尾有0漏掉：120×4 先算12×4=48 别忘了添0 → 480",
    ],
    ("多位数乘一位数", "进位乘法"): [
        "进位漏加：前一位进过来的数要加上，这是最常见错误！",
        "中间的0跳过不乘：102×4 中间的0也要乘（0×4=0再加进位）",
    ],

    # ===== 长方形和正方形 =====
    ("长方形和正方形", "周长"): [
        "公式记混：周长=(长+宽)×2 不是 长×宽（那是面积）",
        "正方形周长=边长×4 不是 边长×边长（也是面积）",
    ],

    # ===== 分数的初步认识 =====
    ("分数的初步认识", "分数的意义"): [
        "忘记强调「平均分」：必须平均分才能产生分数",
        "分子分母搞反：分母在下（总份数），分子在上（取的份数）",
    ],
    ("分数的初步认识", "几分之一"): [
        "大小比较直觉相反：分母越大每一份越小（分的人越多每人越少）",
    ],
    ("分数的初步认识", "简单加减"): [
        "异分母不能直接加减：三年级只学同分母加减，分母要相同才能直接相加减",
        "忘记约分：2/8 要化简为 1/4，养成约分习惯",
    ],

    # ===== 数学广角·集合 =====
    ("数学广角·集合", "重叠问题"): [
        "重复计算：两组人数直接相加会把重叠的人算两次，要减去一次",
        "韦恩图画错：重叠区域的人数不要重复写在两边月牙里",
    ],
}


def _selfcheck_for(title, subs):
    qs = [f"用自己的话说说：「{title}」主要讲了什么？"]
    if subs:
        qs.append(f"「{subs[0]}」是什么意思？请举一个生活中的例子。")
        if len(subs) > 1:
            qs.append(f"你觉得「{subs[-1]}」和前面的内容有什么联系？")
    qs.append("学完这部分后，你还有哪里不太明白？可以记下来问老师或同学。")
    return qs


def get_lesson(course_id):
    """返回一个结构化的详细课程讲义（离线生成，无需模型）。
    字段：id/title/stage/subject/grade/lang/goals/sections/selfcheck/summary
    sections: [{no, heading, body, tip}]
    """
    t = TOPIC_INDEX.get(course_id)
    if not t:
        return None
    title = t.get("title", "")
    stage = t.get("stage", "")
    subject = t.get("subject", "")
    grade = t.get("grade", "")
    lang = t.get("lang", "zh")
    goals = t.get("goals", "")
    subs = t.get("sub") or []

    sections = []
    for i, s in enumerate(subs, 1):
        sections.append({
            "no": i,
            "heading": s,
            "body": _explain_sub(title, subject, s, course_id=course_id),
            "tip": _tip_for(subject),
        })

    summary = (
        f"「{title}」是{stage}{grade}{subject}的重要内容。"
        f"建议先看“学习目标”知道自己要学到什么，再逐点理解“核心讲解”，"
        f"最后用“想一想”自测巩固；有疑问就点“AI 深度讲解”或直接在对话里问老师，"
        f"用你自己的话复述一遍，效果最好。"
    )
    # 收集各子知识点的易错点（去重合并）
    all_mistakes = set()
    for s in subs:
        for m in _mistakes_for(title, s):
            all_mistakes.add(m)
    mistakes = list(all_mistakes) if all_mistakes else _mistakes_for(subject)

    # ---- 自主测验题：汇集 Ollama 生成内容里的练习题 + 自测题 ----
    quiz = []
    for s in subs:
        gc = _find_gen_content(title, s)
        if gc:
            for q in (gc.get("questions") or []):
                item = {
                    "type": q.get("type", "choice"),
                    "stem": q.get("stem", ""),
                    "options": q.get("options") or [],
                    "answer": q.get("answer", ""),
                    "explanation": q.get("explanation", ""),
                    "sub": s,
                }
                quiz.append(item)
    # 若生成内容里没题，则用「想一想」自测题作为开放式测验
    if not quiz:
        for q in (_selfcheck_for(title, subs) or []):
            quiz.append({
                "type": "open",
                "stem": q,
                "options": [],
                "answer": "",
                "explanation": "",
                "sub": "",
            })

    return {
        "id": t["id"],
        "title": title,
        "stage": stage,
        "subject": subject,
        "grade": grade,
        "lang": lang,
        "goals": goals,
        "sections": sections,
        "mistakes": mistakes,
        "selfcheck": _selfcheck_for(title, subs),
        "quiz": quiz,
        "summary": summary,
    }


def mock_lesson_explain(topic, lang="zh"):
    """演示模式（无密钥）下，生成高质量结构化分步讲解：{title, points:[{key,explain,example}], summary}。
    数据优先级：GEN_CONTENT(Ollama) > 学科智能引擎(_gen_*_content) > 种子题库例题 > 智能兜底。
    """
    if not topic:
        return {"title": "", "points": [], "summary": ""}
    tid = topic.get("id", "") if isinstance(topic, dict) else ""
    title = topic.get("title", "")
    subs = (topic.get("sub") or []) if isinstance(topic, dict) else []
    subject = topic.get("subject", "") or ""

    # ---- 1. 尝试从 Ollama 生成内容(GEN_CONTENT)提取 ----
    gen_points = []
    for s in subs:
        gc = _find_gen_content(title, s)
        if gc:
            # gc 有 content(讲解文本) + questions(题库)
            explain = gc.get("content", "")
            qs = gc.get("questions", [])
            example = _build_example_from_qs(qs, s)
            if not explain:
                explain = _explain_sub(title, subject, s, course_id=tid)
            gen_points.append({"key": s, "explain": explain, "example": example})

    # 如果 Ollama 内容覆盖了大部分子点，直接返回
    if len(gen_points) >= max(1, len(subs) * 3 // 5):
        return {
            "title": title,
            "points": gen_points,
            "summary": _build_summary(title, subs),
        }

    # ---- 2. 用学科引擎补全/替代 ----
    points = []
    for i, s in enumerate(subs):
        # 优先用已收集的 Ollama 内容
        existing = [p for p in gen_points if p["key"] == s]
        if existing:
            points.append(existing[0])
            continue

        # 用学科智能引擎生成讲解
        explain = _explain_sub(title, subject, s, course_id=tid)

        # 从种子题库找对应真题作为例题
        example = _find_seed_example(tid, s, subject)
        if not example:
            example = _make_generic_example(s, subject, explain)

        points.append({"key": s, "explain": explain, "example": example})

    # 确保至少有 3 个要点（如果子点太少就拆分）
    if len(points) < 3 and points:
        points = _expand_points(points, min_points=3)

    return {
        "title": title,
        "points": points,
        "summary": _build_summary(title, subs),
    }


def _find_gen_content(topic_title, sub_name):
    """从 GEN_CONTENT / GEN_BY_TS 或 LAZY_CONTENT / LAZY_BY_TS 中查找 Ollama 生成的子点内容。"""
    # 直接查索引（懒生成优先，因为是更新更近的真实内容）
    entry = LAZY_BY_TS.get((topic_title, sub_name)) or GEN_BY_TS.get((topic_title, sub_name))
    if entry:
        all_subs = entry.get("subs", [])
        for s in all_subs:
            if s.get("sub") == sub_name:
                return s
    # 遍历兜底
    for gid, gdata in list(LAZY_CONTENT.items()) + list(GEN_CONTENT.items()):
        for s in gdata.get("subs", []):
            if s.get("sub") == sub_name:
                return s
    return None


def _build_example_from_qs(questions, sub_name):
    """从题目列表中构建带完整解答的例题字符串。"""
    if not questions:
        return ""
    parts = []
    for q in questions[:2]:  # 取最多2道题
        stem = q.get("stem", "")
        opts = q.get("options", [])
        ans = q.get("answer", "")
        exp = q.get("explanation", "")
        qtype = q.get("type", "")

        ex = f"【{sub_name}练习】{stem}"
        if opts and qtype == "choice":
            ex += "\n" + "\n".join(str(o) for o in opts)
        ex += f"\n答案：{ans}"
        if exp:
            ex += f"\n解析：{exp}"
        parts.append(ex)

    return "\n\n".join(parts)


def _find_seed_example(course_id, sub_name, subject):
    """从种子题库中搜索与当前子知识点相关的真题。严格按学科搜索，不跨科。"""
    try:
        import server as S
    except ImportError:
        return ""
    # 按学科映射到对应的题库（只搜本学科，不跨科！）
    subject_bank_map = {
        "数学": ["_MATH_BANK"],
        "物理": ["_PHYS_BANK"],
        "化学": ["_CHEM_BANK"],
        "英语": ["_ENG_BANK"],
        "历史": ["_HIST_BANK"],
        "生物": ["_BIO_BANK"],
        "地理": ["_GEO_BANK", "_GEO_REGION_BANK"],
        "科学": ["_SCI_BANK"],
        "语文": ["_CN_TEXT_BANK"],
    }
    bank_names = subject_bank_map.get(subject, [])
    if not bank_names:
        return ""

    for bn in bank_names:
        bank = getattr(S, bn, None)
        if not bank or not isinstance(bank, list):
            continue
        for item in bank[:50]:
            # 支持两种格式：dict 或 tuple(5元素)
            if isinstance(item, dict):
                stem = str(item.get("stem", ""))
                opts = item.get("options", [])
                ans = item.get("answer", item.get("正确答案", ""))
                exp = item.get("explanation", item.get("解析", ""))
            elif isinstance(item, (list, tuple)) and len(item) >= 5:
                tags = item[0]
                stem = str(item[1])
                opts = item[2] if isinstance(item[2], list) else []
                ans = item[3]
                exp = str(item[4]) if len(item) > 4 else ""
            else:
                continue

            # 关键词匹配（子名中的每个2字以上片段）
            keywords = [sub_name[i:i+2] for i in range(len(sub_name)-1)]
            match_count = sum(1 for kw in keywords if kw in stem)
            # 也匹配 tags
            tag_str = str(tags) if not isinstance(tags, str) else tags
            for kw in keywords:
                if kw in tag_str:
                    match_count += 0.5
            if match_count >= max(1, len(keywords)//2):
                ex = f"【真题】{stem}"
                if opts:
                    ex += "\n" + "\n".join(str(o) for o in opts)
                if ans is not None:
                    ex += f"\n答案：{ans}"
                if exp:
                    ex += f"\n解析：{exp}"
                return ex
    return ""


def _make_generic_example(sub_name, subject, explain):
    """当没有找到现成例题时，从讲解内容中提炼一个思考练习。"""
    # 尝试从讲解中抽取公式或关键概念来出题
    if "公式" in explain or "=" in explain:
        return (
            f"【{sub_name}巩固练习】\n"
            f"请根据上面的讲解完成以下练习：\n"
            f"1. 写出 {sub_name} 的核心公式\n"
            f"2. 说明这个公式的适用条件\n"
            f"3. 自己编一道类似的计算题并求解\n\n"
            f"做完后可以对照课本答案检查。"
        )
    return (
        f"【{sub_name}理解检测】\n"
        f"请用自己的话回答：什么是 {sub_name}？它和前面学的知识有什么联系？\n"
        f"试着举一个生活中的例子来说明。"
    )


def _expand_points(points, min_points=3):
    """当子点不足3个时，将已有要点拆分/补充到至少min_points个。"""
    result = list(points)
    while len(result) < min_points:
        last = result[-1]
        key = last["key"]
        exp = last["explain"]
        # 补充一个「易错提醒」或「拓展」要点
        if len(result) <= len(points):
            new_key = key + "·易错点"
            new_exp = (
                f"**学习{key}时常见的错误：**\n"
                f"1. 公式记混或用错条件\n"
                f"2. 计算过程中符号出错（尤其是负数）\n"
                f"3. 忘记检验结果是否符合实际意义\n\n"
                f"💡 建议：每做完一道题都回头检查一遍！"
            )
        else:
            new_key = key + "·拓展应用"
            new_exp = (
                f"**{key}的进阶思考：**\n"
                f"把学到的知识迁移到新情境中。\n"
                f"想想看：这个知识在生活中还有哪些应用？\n"
                f"和其他学科的知识有什么联系？"
            )
        result.append({"key": new_key, "explain": new_exp, "example": ""})
    return result


def _build_summary(topic_title, subs):
    """生成分步讲解的总结段落。"""
    if not subs:
        return f"学习了「{topic_title}」，继续加油！"
    names = "、".join(subs[:4])
    if len(subs) > 4:
        names += f"等共{len(subs)}个核心要点"
    return (
        f"今天我们学习了「{topic_title}」的{names}。\n"
        f"记住核心公式和方法，多做题巩固，遇到问题随时问老师！"
    )


def mock_lesson_reexplain(topic, key="", lang="zh"):
    """演示模式：针对某个没听懂的要点，返回一种换表述的讲法（用学科引擎+种子题重新生成）。"""
    if not topic:
        return {"explain": "（演示模式暂无更多讲法）", "example": ""}
    subject = topic.get("subject", "")
    title = topic.get("title", "")
    subs = (topic.get("sub") or []) if isinstance(topic, dict) else []

    new_explain = ""
    for s in subs:
        if key and key in s:
            new_explain = _explain_sub(title, subject, s)
            break
    if not new_explain or len(new_explain) < 30:
        new_explain = (
            f"我们换个方式来理解「{key}」：\n\n"
            f"第一步——画图理解：先在纸上把这个概念画出来，图形往往比文字更直观。\n\n"
            f"第二步——找生活例子：想一想你身边有没有类似的情况？\n"
            f"比如走路的速度、买东西的价格变化、手机电池的消耗……很多数学概念都能在生活中找到对应。\n\n"
            f"第三步——自己出一道题：模仿课本例题，把数字换成你喜欢的数，自己做一遍。能出题并做对，说明你真的懂了！"
        )

    example = _find_seed_example(topic.get("id", ""), key, subject)
    if not example:
        example = (
            f"【换讲法练习】\n"
            f"用刚才的新思路重新思考：{key}的核心是什么？\n"
            f"试着讲给同学或家长听，如果你能让他们听懂，说明你真掌握了！"
        )
    return {"explain": new_explain, "example": example}


def list_units():
    """返回按 (学段, 学科, 年级) 分组的单元列表，供「精准学」诊断与图谱使用。

    每项: {"stage": 学段, "subject": 学科, "grade": 年级,
           "topics": [{"id","title","sub","goals"}]}
    """
    units = []
    for st in CURRICULUM:
        stage = st.get("stage")
        for subj in st.get("subjects", []):
            name = subj.get("name")
            for g in subj.get("grades", []):
                grade = g.get("grade")
                topics = [{"id": t["id"], "title": t["title"],
                           "sub": t.get("sub", []), "goals": t.get("goals", "")}
                          for t in g.get("topics", [])]
                if topics:
                    units.append({"stage": stage, "subject": name,
                                  "grade": grade, "topics": topics})
    return units


# ===== 由本地 Ollama 批量生成的课件内容+题目（全学科全量覆盖）=====
# 批量预生成内容写入 curriculum_gen.json（由 _gen_content.py 生成）；
# 运行期按需 Ollama 生成的真实内容写入 curriculum_lazy.json（避免与批量文件互相覆盖）。
# 两者均支持热重载，无需重启服务。
import json as _json, os as _os
GEN_CONTENT = {}          # 批量生成（curriculum_gen.json）
GEN_BY_TS = {}
LAZY_CONTENT = {}         # 按需生成（curriculum_lazy.json）
LAZY_BY_TS = {}
_GEN_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "curriculum_gen.json")
_LAZY_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "curriculum_lazy.json")
_GEN_MTIME = 0
_LAZY_MTIME = 0

def _index_gen(data):
    idx = {}
    for _cid, _g in data.items():
        for _s in (_g.get("subs") or []):
            idx[(_g.get("title"), _s.get("sub"))] = _g
    return idx

def reload_gen():
    """若批量/懒生成文件有更新则重新加载（支持生成任务边跑边用）。"""
    global GEN_CONTENT, GEN_BY_TS, LAZY_CONTENT, LAZY_BY_TS, _GEN_MTIME, _LAZY_MTIME
    changed = False
    try:
        mt = _os.path.getmtime(_GEN_PATH)
        if mt > _GEN_MTIME:
            with open(_GEN_PATH, "r", encoding="utf-8") as _f:
                GEN_CONTENT = _json.load(_f)
            _GEN_MTIME = mt
            changed = True
    except OSError:
        pass
    try:
        lmt = _os.path.getmtime(_LAZY_PATH)
        if lmt > _LAZY_MTIME:
            with open(_LAZY_PATH, "r", encoding="utf-8") as _f:
                LAZY_CONTENT = _json.load(_f)
            _LAZY_MTIME = lmt
            changed = True
    except OSError:
        pass
    if changed:
        GEN_BY_TS = _index_gen(GEN_CONTENT)
        LAZY_BY_TS = _index_gen(LAZY_CONTENT)

reload_gen()

# ───────────────────────────────────────────────────────────
# 按需懒生成：对覆盖薄弱、易出「整科重复模板」的学科（历史/地理/道法/思政），
# 在用户首次学习该知识点时，用本地 Ollama(qwen2.5:3b) 实时生成真人级讲解+题目，
# 缓存到 curriculum_lazy.json 并热加载。之后再次学习即时命中，永不重复。
# ───────────────────────────────────────────────────────────
_LAZY_FAILED = {}   # course_id -> 上次失败时间戳（防抖：失败5分钟内不重试，避免Ollama异常时反复打满）
_LAZY_SUBJECTS = {"历史", "地理", "道德与法治", "思想政治"}

def _lazy_ollama_explain(course_id, topic_title, subject, subs):
    """按需用本地 Ollama(qwen2.5:3b) 为单个知识点实时生成真实内容并缓存。
    返回 True 表示已生成并缓存；False 表示失败（调用方回退到话题相关兜底）。
    注意：失败仅短期防抖，不永久拉黑——Ollama 空闲后下次访问会重生富内容。"""
    if course_id in LAZY_CONTENT:
        return True
    import time as _time
    _now = _time.time()
    if course_id in _LAZY_FAILED and (_now - _LAZY_FAILED[course_id]) < 300:
        return False
    try:
        import importlib
        G = importlib.import_module("_gen_content")
        G.MODEL = "qwen2.5:3b"
        prompt = G.build_prompt(subject, topic_title, subs)
        raw = G.call_ollama(prompt, timeout=120)
        obj = _json.loads(raw)
        valid = G.validate(obj, subject, subs)
        if not valid:
            _LAZY_FAILED[course_id] = _now
            return False
        existing = {}
        try:
            if _os.path.exists(_LAZY_PATH):
                with open(_LAZY_PATH, "r", encoding="utf-8") as _f:
                    existing = _json.load(_f)
        except Exception:
            existing = {}
        existing[course_id] = {"title": topic_title, "subject": subject, "subs": valid}
        with open(_LAZY_PATH, "w", encoding="utf-8") as _f:
            _json.dump(existing, _f, ensure_ascii=False)
        reload_gen()
        return True
    except Exception:
        _LAZY_FAILED[course_id] = _now
        return False


if __name__ == "__main__":
    print(f"共 {len(TOPIC_INDEX)} 个知识点")
    for st in CURRICULUM:
        n = sum(len(g["topics"]) for subj in st["subjects"] for g in subj["grades"])
        print(f"  {st['stage']}: {len(st['subjects'])} 门学科，{n} 个知识点")
