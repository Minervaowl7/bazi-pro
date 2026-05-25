#!/usr/bin/env python3
"""从古籍语料库提取案例创建 Golden 测试用例"""
import json
import os

new_cases = [
    {
        "id": "classical_zhengcaige_yhzwang",
        "description": "古籍案例·正印格透财—辛酉 丙申 壬申 辛亥（汪侍郎命）",
        "source": "ZPZ_00120",
        "scenario": "壬水日主申月，印重身强透财",
        "input": {
            "day_master": "壬", "bazi": "辛酉 丙申 壬申 辛亥",
            "month_branch": "申",
            "expected_pattern": "正印格",
            "expected_wangshuai": "中和",
            "expected_yongshen_wx": "土",
        },
        "must_include": ["正印格"],
        "must_not_include": ["从格"],
        "classical_support": ["ZPZ_00120"],
        "notes": "《子平真诠》：印重身强，透财以抑太过"
    },
    {
        "id": "classical_congqiang_wuwu",
        "description": "古籍案例·从强格—戊午 戊午 戊午 甲寅",
        "source": "YHZ_00115",
        "scenario": "戊土日主午月，三戊午一甲寅",
        "input": {
            "day_master": "戊", "bazi": "戊午 戊午 戊午 甲寅",
            "month_branch": "午",
            "expected_pattern": "从强格",
            "expected_wangshuai": "偏旺",
            "expected_yongshen_wx": "火",
        },
        "must_include": ["从强格"],
        "must_not_include": ["羊刃格"],
        "classical_support": ["YHZ_00115"],
        "notes": "《渊海子平》：戊日午月勿作刃看，岁时火多却为印绶"
    },
    {
        "id": "classical_shangguan_peiyin",
        "description": "古籍案例·伤官用煞印—己未 丙子 庚子 丙子（蔡贵妃）",
        "source": "ZPZ_00141",
        "scenario": "庚金日主子月，伤官用煞印",
        "input": {
            "day_master": "庚", "bazi": "己未 丙子 庚子 丙子",
            "month_branch": "子",
            "expected_pattern": "暗伤官格",
            "expected_wangshuai": "中和",
            "expected_yongshen_wx": "土",
        },
        "must_include": ["伤官"],
        "must_not_include": ["从格", "七杀格"],
        "classical_support": ["ZPZ_00141"],
        "notes": "《子平真诠》：伤多身弱，赖煞生印以帮身制伤"
    },
    {
        "id": "classical_shishen_shengcai",
        "description": "古籍案例·食神生财—戊子 丁巳 甲辰 丙寅",
        "source": "YHZ_00068",
        "scenario": "甲木日主巳月，食伤生财归禄",
        "input": {
            "day_master": "甲", "bazi": "戊子 丁巳 甲辰 丙寅",
            "month_branch": "巳",
            "expected_pattern": "食神格",
            "expected_wangshuai": "中和",
            "expected_yongshen_wx": "木",
        },
        "must_include": ["食神格"],
        "must_not_include": ["从格", "伤官格"],
        "classical_support": ["YHZ_00068"],
        "notes": "《渊海子平》：食伤生财格，归禄于寅，早年食伤运发"
    },
    {
        "id": "classical_caiwang_shenruo",
        "description": "古籍案例·财旺身弱—庚申 乙酉 丙申 丙申",
        "source": "YHZ_00066",
        "scenario": "丙火日主酉月，三申一酉财旺身弱",
        "input": {
            "day_master": "丙", "bazi": "庚申 乙酉 丙申 丙申",
            "month_branch": "酉",
            "expected_pattern": "暗正财格",
            "expected_wangshuai": "中和",
            "expected_yongshen_wx": "土",
        },
        "must_include": ["财"],
        "must_not_include": ["从财格", "身旺"],
        "classical_support": ["YHZ_00066"],
        "notes": "《渊海子平》：日弱财旺，不能胜其财，所以贫也"
    },
    {
        "id": "classical_shishen_zhengcai_ju",
        "description": "古籍案例·食神生财巨富—辛丑 丁酉 丁巳 丁未",
        "source": "YHZ_00065",
        "scenario": "丁火日主酉月，巳酉丑金局财旺",
        "input": {
            "day_master": "丁", "bazi": "辛丑 丁酉 丁巳 丁未",
            "month_branch": "酉",
            "expected_pattern": "偏财格",
            "expected_wangshuai": "偏旺",
            "expected_yongshen_wx": "土",
        },
        "must_include": ["偏财格"],
        "must_not_include": ["从格"],
        "classical_support": ["YHZ_00065"],
        "notes": "《渊海子平》：巳酉丑金局，身旺能任，巨富"
    },
    {
        "id": "classical_jianlu_zhengcai",
        "description": "古籍案例·建禄透官印—庚戌 戊子 癸酉 癸亥（金丞相）",
        "source": "ZPZ_00151",
        "scenario": "癸水日主子月，建禄官印相随",
        "input": {
            "day_master": "癸", "bazi": "庚戌 戊子 癸酉 癸亥",
            "month_branch": "子",
            "expected_pattern": "建禄格，透正官",
            "expected_wangshuai": "偏旺",
            "expected_yongshen_wx": "土",
        },
        "must_include": ["建禄格", "正官"],
        "must_not_include": ["从格", "羊刃格"],
        "classical_support": ["ZPZ_00151"],
        "notes": "《子平真诠》：建禄用官而印护，金丞相命"
    },
    {
        "id": "classical_qisha_shenwang",
        "description": "古籍案例·时上七杀有制—辛丑 乙未 乙卯 丙子",
        "source": "YHZ_00091",
        "scenario": "乙木日主未月，时上七杀丙合为制",
        "input": {
            "day_master": "乙", "bazi": "辛丑 乙未 乙卯 丙子",
            "month_branch": "未",
            "expected_pattern": "暗偏财格",
            "expected_wangshuai": "中和",
            "expected_yongshen_wx": "火",
        },
        "must_include": ["偏财"],
        "must_not_include": ["从格", "建禄"],
        "classical_support": ["YHZ_00091"],
        "notes": "《渊海子平》：身旺，丙合辛杀，贵而有权"
    },
    {
        "id": "classical_shangguanshengcai",
        "description": "古籍案例·伤官生财—丙申 己亥 辛未 己亥（郑丞相）",
        "source": "ZPZ_00142",
        "scenario": "辛金日主亥月，金水伤官化财",
        "input": {
            "day_master": "辛", "bazi": "丙申 己亥 辛未 己亥",
            "month_branch": "亥",
            "expected_pattern": "暗伤官格",
            "expected_wangshuai": "中和",
            "expected_yongshen_wx": "土",
        },
        "must_include": ["伤官"],
        "must_not_include": ["从格", "建禄"],
        "classical_support": ["ZPZ_00142"],
        "notes": "《子平真诠》：冬金用官化伤为财，极秀极贵"
    },
    {
        "id": "classical_guan_yin_shuangquan",
        "description": "古籍案例·官印双全—戊戌 庚申 癸酉 庚申",
        "source": "YHZ_00100",
        "scenario": "癸水日主申月，庚申重重官印双全",
        "input": {
            "day_master": "癸", "bazi": "戊戌 庚申 癸酉 庚申",
            "month_branch": "申",
            "expected_pattern": "正印格",
            "expected_wangshuai": "中和",
            "expected_yongshen_wx": "土",
        },
        "must_include": ["正印格"],
        "must_not_include": ["从格", "建禄"],
        "classical_support": ["YHZ_00100"],
        "notes": "《渊海子平》：官印两全，极为贵命"
    },
    {
        "id": "classical_yangren_yinzhong",
        "description": "古籍案例·四戊午稼穑—戊午 戊午 戊午 戊午",
        "source": "ZPZ_00161",
        "scenario": "四戊午，全局火土一气",
        "input": {
            "day_master": "戊", "bazi": "戊午 戊午 戊午 戊午",
            "month_branch": "午",
            "expected_pattern": "稼穑格",
            "expected_wangshuai": "偏旺",
            "expected_yongshen_wx": "火",
        },
        "must_include": ["稼穑"],
        "must_not_include": ["羊刃格", "建禄"],
        "classical_support": ["ZPZ_00161"],
        "notes": "四戊午火土一气，稼穑格（土专旺）"
    },
    {
        "id": "classical_jianlu_wucai",
        "description": "古籍案例·建禄无可用—戊子 庚申 庚申 庚申（郭统制）",
        "source": "ZPZ_00164",
        "scenario": "庚金日主申月建禄，无财官透出",
        "input": {
            "day_master": "庚", "bazi": "戊子 庚申 庚申 庚申",
            "month_branch": "申",
            "expected_pattern": "建禄格，无财官煞食透出",
            "expected_wangshuai": "身旺",
            "expected_yongshen_wx": "火",
        },
        "must_include": ["建禄格", "无财官煞食透出"],
        "must_not_include": ["从强", "从革", "暗比肩格"],
        "classical_support": ["ZPZ_00164"],
        "notes": "《子平真诠》：庚生申月建禄，三庚申无财官"
    },
    {
        "id": "classical_yuejie_shishen",
        "description": "古籍案例·月劫透食神—己未 己巳 丁未 辛丑",
        "source": "YHZ_00057",
        "scenario": "丁火日主巳月，巳丑合金局",
        "input": {
            "day_master": "丁", "bazi": "己未 己巳 丁未 辛丑",
            "month_branch": "巳",
            "expected_pattern": "月劫格，透食神",
            "expected_wangshuai": "中和偏旺",
            "expected_yongshen_wx": "水",
        },
        "must_include": ["月劫格"],
        "must_not_include": ["从格", "建禄", "羊刃"],
        "classical_support": ["YHZ_00057"],
        "notes": "《渊海子平》：巳丑合金为财，身旺喜财"
    },
    {
        "id": "classical_zhengyin_shenqiang",
        "description": "古籍案例·正印身强透官—丙寅 戊戌 辛酉 戊子（张参政）",
        "source": "ZPZ_00117",
        "scenario": "辛金日主戌月，戊土正印双透",
        "input": {
            "day_master": "辛", "bazi": "丙寅 戊戌 辛酉 戊子",
            "month_branch": "戌",
            "expected_pattern": "正印格",
            "expected_wangshuai": "中和",
            "expected_yongshen_wx": "火",
        },
        "must_include": ["正印格"],
        "must_not_include": ["从格", "暗印格"],
        "classical_support": ["ZPZ_00117"],
        "notes": "《子平真诠》：身旺印强，只要官星清纯"
    },
    {
        "id": "classical_shangjie_shengcai",
        "description": "古籍案例·伤官化劫生财—甲子 辛未 辛酉 壬辰（汪学士）",
        "source": "ZPZ_00112",
        "scenario": "辛金日主未月，伤官化劫生财",
        "input": {
            "day_master": "辛", "bazi": "甲子 辛未 辛酉 壬辰",
            "month_branch": "未",
            "expected_pattern": "偏印格",
            "expected_wangshuai": "中和",
            "expected_yongshen_wx": "木",
        },
        "must_include": ["印"],
        "must_not_include": ["从格", "正官格"],
        "classical_support": ["ZPZ_00112"],
        "notes": "《子平真诠》：财不甚旺而比强，露伤官化劫生财"
    },
]

test_dir = 'tests/golden_cases'
for case in new_cases:
    fname = os.path.join(test_dir, f'{case["id"]}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(case, f, ensure_ascii=False, indent=2)
    print(f'已创建: {fname}')

print(f'\n共创建 {len(new_cases)} 个古籍案例测试文件')
