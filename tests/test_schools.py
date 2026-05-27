import pytest
from bazi_pro.core.schools import school_analyze, SCHOOL_REGISTRY, _ensure_schools_loaded
from bazi_pro.core import full_analysis


class TestSchools:
    def test_school_registry_has_all(self):
        _ensure_schools_loaded()
        assert 'ziping' in SCHOOL_REGISTRY
        assert 'mangpai' in SCHOOL_REGISTRY
        assert 'xinpai' in SCHOOL_REGISTRY

    def test_ziping_analyzer(self):
        mcp = {
            '八字': '壬子 壬子 壬子 壬子',
            '日主': '壬',
            '性别': '男',
            '出生年': 1984,
            '出生月': 1,
            '出生日': 15,
        }
        result = school_analyze(mcp, 'ziping')
        assert result.get('pattern', {}).get('pattern') in ['从强格', '润下格', '身旺', '从强']
        assert 'wangshuai' in result
        assert 'yongshen' in result

    def test_mangpai_analyzer(self):
        mcp = {
            '八字': '壬子 壬子 壬子 壬子',
            '日主': '壬',
            '性别': '男',
            '出生年': 1984,
            '出生月': 1,
            '出生日': 15,
        }
        result = school_analyze(mcp, 'mangpai')
        assert 'binzhu' in result
        assert 'tiyong' in result
        assert 'zuogong' in result
        assert 'gongli' in result

    def test_xinpai_analyzer(self):
        mcp = {
            '八字': '壬子 壬子 壬子 壬子',
            '日主': '壬',
            '性别': '男',
            '出生年': 1984,
            '出生月': 1,
            '出生日': 15,
        }
        result = school_analyze(mcp, 'xinpai')
        assert 'yong_ji' in result
        assert 'baishen' in result
        assert 'kongwang' in result
        assert 'fanduan' in result

    def test_school_all(self):
        mcp = {
            '八字': '壬子 壬子 壬子 壬子',
            '日主': '壬',
            '性别': '男',
            '出生年': 1984,
            '出生月': 1,
            '出生日': 15,
        }
        result = school_analyze(mcp, 'all')
        assert 'ziping' in result
        assert 'mangpai' in result
        assert 'xinpai' in result

    def test_unknown_school(self):
        mcp = {
            '八字': '壬子 壬子 壬子 壬子',
            '日主': '壬',
            '性别': '男',
            '出生年': 1984,
            '出生月': 1,
            '出生日': 15,
        }
        result = school_analyze(mcp, 'unknown')
        assert result.get('status') == 'error'
