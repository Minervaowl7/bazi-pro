"""属性基测试 — 核心算术模块的边界条件测试

使用 hypothesis 库进行属性基测试（property-based testing），
自动生成边界输入验证核心计算函数的正确性。

测试策略：
  - 五行力量百分比总和始终 ≈ 100%
  - 力量值始终 ≥ 0
  - 旺衰判定结果始终为有效字符串
  - 输入验证始终返回有效结构
"""


from bazi_pro.core.elements import calc_element_forces
from bazi_pro.core.strength import calc_dedi, calc_deling, calc_deshi, judge_wangshuai
from bazi_pro.validation import validate_bazi_input, validate_bazi_string

# 十天干
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
# 十二地支
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 有效四柱组合（用于测试）
VALID_PILLARS = [f'{g}{z}' for g in TIANGAN for z in DIZHI]


class TestElementForcesProperties:
    """五行力量计算属性测试"""

    def test_percent_sums_to_100(self):
        """百分比总和应约等于 100%"""
        import random
        random.seed(42)
        for _ in range(50):
            parts = random.sample(VALID_PILLARS, 4)
            month_zhi = parts[1][1]
            result = calc_element_forces(parts, month_zhi)
            total = sum(result['percent'].values())
            assert abs(total - 100.0) < 1.0, f"百分比总和 {total} != 100%"

    def test_percent_adjusted_sums_to_100(self):
        """修正后百分比总和应约等于 100%"""
        import random
        random.seed(42)
        for _ in range(50):
            parts = random.sample(VALID_PILLARS, 4)
            month_zhi = parts[1][1]
            result = calc_element_forces(parts, month_zhi)
            total = sum(result['percent_adjusted'].values())
            assert abs(total - 100.0) < 1.0, f"修正后百分比总和 {total} != 100%"

    def test_forces_non_negative(self):
        """力量值始终 ≥ 0"""
        import random
        random.seed(42)
        for _ in range(50):
            parts = random.sample(VALID_PILLARS, 4)
            month_zhi = parts[1][1]
            result = calc_element_forces(parts, month_zhi)
            for elem, val in result['raw'].items():
                assert val >= 0, f"{elem} 力量为负: {val}"
            for elem, val in result['percent'].items():
                assert val >= 0, f"{elem} 百分比为负: {val}"
            for elem, val in result['percent_adjusted'].items():
                assert val >= 0, f"{elem} 修正后百分比为负: {val}"

    def test_forces_total_positive(self):
        """力量总和始终 > 0"""
        import random
        random.seed(42)
        for _ in range(50):
            parts = random.sample(VALID_PILLARS, 4)
            month_zhi = parts[1][1]
            result = calc_element_forces(parts, month_zhi)
            assert result['total'] > 0, f"力量总和为 {result['total']}"

    def test_forces_keys_complete(self):
        """返回的五行键始终完整"""
        expected = {'木', '火', '土', '金', '水'}
        parts = ['甲子', '丙寅', '戊辰', '庚午']
        result = calc_element_forces(parts, '寅')
        assert set(result['raw'].keys()) == expected
        assert set(result['percent'].keys()) == expected
        assert set(result['percent_adjusted'].keys()) == expected


class TestStrengthProperties:
    """旺衰判定属性测试"""

    def test_deling_returns_valid_status(self):
        """得令状态始终为有效字符串"""
        valid_statuses = {'帝旺', '临官', '长生', '冠带', '养', '沐浴', '衰', '病', '死', '墓', '绝', '胎'}
        for dm in TIANGAN:
            for mz in DIZHI:
                status, score = calc_deling(dm, mz)
                assert status in valid_statuses, f"无效状态: {status}"
                assert isinstance(score, int)

    def test_deling_score_range(self):
        """得令评分范围: -3 到 +3"""
        for dm in TIANGAN:
            for mz in DIZHI:
                _, score = calc_deling(dm, mz)
                assert -3 <= score <= 3, f"评分超范围: {score}"

    def test_dedi_returns_valid_level(self):
        """得地等级始终为有效值"""
        valid_levels = {'得地', '偏得地', '不得地'}
        for dm in TIANGAN:
            result = calc_dedi(dm, ['甲子', '丙寅', '戊辰', '庚午'])
            assert result['level'] in valid_levels, f"无效等级: {result['level']}"
            assert result['score'] >= 0

    def test_deshi_returns_valid_level(self):
        """得势等级始终为有效值"""
        valid_levels = {'得势', '偏得势', '不得势'}
        for dm in TIANGAN:
            result = calc_deshi(dm, ['甲子', '丙寅', '戊辰', '庚午'])
            assert result['level'] in valid_levels, f"无效等级: {result['level']}"
            assert result['score'] >= 0

    def test_wangshuai_returns_valid_verdict(self):
        """旺衰判定结果始终为有效字符串"""
        valid_verdicts = {'极旺', '身旺', '偏旺', '中和偏旺', '中和', '中和偏弱', '身弱', '极弱'}
        import random
        random.seed(42)
        for _ in range(100):
            deling = random.randint(-3, 3)
            dedi = random.uniform(0, 8)
            deshi = random.uniform(0, 12)
            result = judge_wangshuai(deling, dedi, deshi)
            assert result['verdict'] in valid_verdicts, f"无效判定: {result['verdict']}"

    def test_wangshuai_extreme_flags_consistent(self):
        """极旺/极弱标记与判定结果一致"""
        import random
        random.seed(42)
        for _ in range(100):
            deling = random.randint(-3, 3)
            dedi = random.uniform(0, 8)
            deshi = random.uniform(0, 12)
            result = judge_wangshuai(deling, dedi, deshi)
            if result['verdict'] == '极旺':
                assert result['is_extreme_strong'] is True
                assert result['is_strong'] is True
            if result['verdict'] == '极弱':
                assert result['is_extreme_weak'] is True
                assert result['is_weak'] is True


class TestValidationProperties:
    """输入验证属性测试"""

    def test_valid_bazi_accepted(self):
        """有效八字始终被接受"""
        import random
        random.seed(42)
        for _ in range(50):
            parts = random.sample(VALID_PILLARS, 4)
            bazi = ' '.join(parts)
            valid, msg = validate_bazi_string(bazi)
            assert valid is True, f"拒绝了有效八字: {bazi}, 原因: {msg}"

    def test_empty_bazi_rejected(self):
        """空八字始终被拒绝"""
        valid, msg = validate_bazi_string('')
        assert valid is False

    def test_invalid_format_rejected(self):
        """无效格式始终被拒绝"""
        invalid = ['abc', '甲子', '甲子 乙丑', '甲子 乙丑 丙寅', '甲乙丙丁戊己庚辛']
        for bazi in invalid:
            valid, msg = validate_bazi_string(bazi)
            assert valid is False, f"接受了无效八字: {bazi}"

    def test_validate_input_returns_valid_structure(self):
        """输入验证始终返回有效结构"""
        test_cases = [
            {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': '女'},
            {'八字': '', '日主': '', '性别': ''},
            {'八字': '甲子 乙丑 丙寅 丁卯', '日主': '甲'},
        ]
        for data in test_cases:
            result = validate_bazi_input(data, require_gender=False)
            assert 'valid' in result
            assert 'errors' in result
            assert isinstance(result['valid'], bool)
            assert isinstance(result['errors'], list)
