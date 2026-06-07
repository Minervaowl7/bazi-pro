"""四维度分析模块测试 — 婚姻/健康/财运/六亲"""
import pytest
from bazi_pro.core.marriage import analyze_marriage
from bazi_pro.core.health import analyze_health
from bazi_pro.core.wealth import analyze_wealth
from bazi_pro.core.family import analyze_family

BAZI_MALE = ['甲子', '丙寅', '戊午', '庚申']
BAZI_FEMALE = ['乙丑', '丁卯', '己巳', '辛未']

class TestMarriage:
    def test_basic_male(self):
        result = analyze_marriage('戊', '男', BAZI_MALE)
        assert 'spouse_star' in result
        assert 'spouse_palace' in result
        assert 'spouse_star_strength' in result
        assert 'marriage_risks' in result
    
    def test_basic_female(self):
        result = analyze_marriage('己', '女', BAZI_FEMALE)
        assert result['spouse_star']['name'] in ('正官', '七杀', '')

class TestHealth:
    def test_basic(self):
        result = analyze_health('戊', '男', BAZI_MALE)
        assert 'organ_risks' in result
        assert 'constitution' in result
        assert 'health_score' in result
    
    def test_health_score_range(self):
        result = analyze_health('戊', '男', BAZI_MALE)
        assert 0 <= result['health_score'] <= 100

class TestWealth:
    def test_basic(self):
        result = analyze_wealth('戊', '男', BAZI_MALE)
        assert 'wealth_stars' in result
        assert 'wealth_patterns' in result
        assert 'wealth_score' in result
    
    def test_wealth_score_range(self):
        result = analyze_wealth('戊', '男', BAZI_MALE)
        assert 0 <= result['wealth_score'] <= 100

class TestFamily:
    def test_basic_male(self):
        result = analyze_family('戊', '男', BAZI_MALE)
        assert 'father' in result
        assert 'mother' in result
        assert 'siblings' in result
        assert 'children' in result
    
    def test_basic_female(self):
        result = analyze_family('己', '女', BAZI_FEMALE)
        assert 'father' in result
        assert result['father']['star'] == '偏财'  # Fixed: both genders use 偏财 for father
