from bazi_pro.core.constants import derive_shishen

SHISHEN_WUXING_REL = {
    '比肩': '同我', '劫财': '同我', '比劫': '同我',
    '食神': '我生', '伤官': '我生', '食伤': '我生',
    '偏财': '我克', '正财': '我克', '财星': '我克',
    '七杀': '克我', '正官': '克我', '官杀': '克我', '官星': '克我',
    '偏印': '生我', '正印': '生我', '印星': '生我', '印比': '生我',
}


def _count_shishen_categories(day_master, gans, bazi_parts):
    counts = {'官杀': 0, '财星': 0, '食伤': 0, '印星': 0, '比劫': 0}
    for g in gans:
        ss = derive_shishen(day_master, g)
        if ss in ('正官', '七杀'):
            counts['官杀'] += 1
        elif ss in ('正财', '偏财'):
            counts['财星'] += 1
        elif ss in ('食神', '伤官'):
            counts['食伤'] += 1
        elif ss in ('正印', '偏印'):
            counts['印星'] += 1
        elif ss in ('比肩', '劫财'):
            counts['比劫'] += 1
    return counts


def _get_yongshen_direction(shishen: str) -> str:
    direction_map = {
        '正官': '财印', '七杀': '食印', '正财': '食官', '偏财': '食官',
        '正印': '官比', '偏印': '财官', '食神': '比财', '伤官': '印财',
        '比肩': '官食', '劫财': '官杀',
    }
    return direction_map.get(shishen, '待定')
