import re

TIANGAN = set('甲乙丙丁戊己庚辛壬癸')
DIZHI = set('子丑寅卯辰巳午未申酉戌亥')
VALID_GENDERS = ('男', '女', '其他')
VALID_DETAIL_LEVELS = ('standard', 'detailed', 'brief')

_TIANGAN_STR = '甲乙丙丁戊己庚辛壬癸'
_DIZHI_STR = '子丑寅卯辰巳午未申酉戌亥'
_PILLAR = f'[{_TIANGAN_STR}][{_DIZHI_STR}]'
BAZI_PATTERN = re.compile(rf'^{_PILLAR} {_PILLAR} {_PILLAR} {_PILLAR}$')


def validate_bazi_string(bazi: str) -> tuple[bool, str]:
    if not bazi:
        return False, '八字不能为空'
    if not BAZI_PATTERN.match(bazi):
        return False, f'八字格式无效，应为4组天干地支以空格分隔，如"甲子 乙丑 丙寅 丁卯"，实际值: {bazi}'
    return True, ''


def validate_day_master(day_master: str) -> tuple[bool, str]:
    if not day_master:
        return False, '日主不能为空'
    if day_master not in TIANGAN:
        return False, f'日主无效，必须为十天干之一({"".join(sorted(TIANGAN))})，实际值: {day_master}'
    return True, ''


def validate_gender(gender: str) -> tuple[bool, str]:
    if not gender:
        return False, '性别不能为空'
    if gender not in VALID_GENDERS:
        return False, f'性别无效，必须为{VALID_GENDERS}之一，实际值: {gender}'
    return True, ''


def validate_day_master_consistency(bazi: str, day_master: str) -> tuple[bool, str]:
    try:
        bazi_parts = bazi.split()
        if len(bazi_parts) >= 3 and len(bazi_parts[2]) >= 1:
            day_stem = bazi_parts[2][0]
            if day_stem != day_master:
                return False, f'日主与日柱天干不一致！八字日柱天干为"{day_stem}"，但输入日主为"{day_master}"'
        return True, ''
    except Exception:
        return True, ''


def validate_bazi_input(data: dict, require_gender: bool = True) -> dict:
    errors = []

    bazi = data.get('八字')
    if bazi is None:
        errors.append('八字字段缺失')
    elif not bazi:
        errors.append('八字不能为空')
    else:
        valid, msg = validate_bazi_string(bazi)
        if not valid:
            errors.append(msg)

    day_master = data.get('日主')
    if day_master is None:
        errors.append('日主字段缺失')
    elif not day_master:
        errors.append('日主不能为空')
    else:
        valid, msg = validate_day_master(day_master)
        if not valid:
            errors.append(msg)
        # 检查日主与八字日柱天干一致性
        if bazi and valid:
            consistent, consistency_msg = validate_day_master_consistency(bazi, day_master)
            if not consistent:
                errors.append(consistency_msg)

    gender = data.get('性别')
    if gender is None:
        if require_gender:
            errors.append('性别字段缺失')
    elif not gender:
        if require_gender:
            errors.append('性别不能为空')
    else:
        valid, msg = validate_gender(gender)
        if not valid:
            errors.append(msg)

    detail_level = data.get('detail_level')
    if detail_level is not None and detail_level not in VALID_DETAIL_LEVELS:
        errors.append(f'detail_level无效，必须为{VALID_DETAIL_LEVELS}之一，实际值: {detail_level}')

    return {'valid': len(errors) == 0, 'errors': errors}
