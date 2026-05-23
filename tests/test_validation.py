
from bazi_pro.core import full_analysis
from bazi_pro.validation import (
    TIANGAN,
    VALID_GENDERS,
    validate_bazi_input,
    validate_bazi_string,
    validate_day_master,
    validate_gender,
)


class TestValidateBaziInput:

    def test_valid_input(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': '女'}
        result = validate_bazi_input(data)
        assert result['valid'] is True
        assert result['errors'] == []

    def test_missing_bazi(self):
        data = {'日主': '丁', '性别': '女'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('八字' in e for e in result['errors'])

    def test_missing_day_master(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '性别': '女'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('日主' in e for e in result['errors'])

    def test_missing_gender(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('性别' in e for e in result['errors'])

    def test_empty_bazi(self):
        data = {'八字': '', '日主': '丁', '性别': '女'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('八字' in e for e in result['errors'])

    def test_empty_day_master(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '', '性别': '女'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('日主' in e for e in result['errors'])

    def test_empty_gender(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': ''}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('性别' in e for e in result['errors'])

    def test_invalid_bazi_format(self):
        data = {'八字': '壬午 乙巳', '日主': '丁', '性别': '女'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('八字' in e for e in result['errors'])

    def test_invalid_bazi_wrong_gan(self):
        data = {'八字': 'X午 乙巳 丁亥 癸卯', '日主': '丁', '性别': '女'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('八字' in e for e in result['errors'])

    def test_invalid_day_master(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': 'X', '性别': '女'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('日主' in e for e in result['errors'])

    def test_invalid_gender(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': 'unknown'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('性别' in e for e in result['errors'])

    def test_invalid_detail_level(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': '女', 'detail_level': 'ultra'}
        result = validate_bazi_input(data)
        assert result['valid'] is False
        assert any('detail_level' in e for e in result['errors'])

    def test_valid_detail_levels(self):
        for level in ('standard', 'detailed', 'brief'):
            data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': '女', 'detail_level': level}
            result = validate_bazi_input(data)
            assert result['valid'] is True, f'detail_level={level} should be valid'

    def test_default_detail_level(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': '女'}
        result = validate_bazi_input(data)
        assert result['valid'] is True

    def test_gender_optional_when_not_required(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'}
        result = validate_bazi_input(data, require_gender=False)
        assert result['valid'] is True

    def test_gender_required_by_default(self):
        data = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'}
        result = validate_bazi_input(data)
        assert result['valid'] is False


class TestValidateBaziString:

    def test_valid(self):
        valid, msg = validate_bazi_string('壬午 乙巳 丁亥 癸卯')
        assert valid is True
        assert msg == ''

    def test_invalid_format(self):
        valid, msg = validate_bazi_string('壬午 乙巳')
        assert valid is False
        assert msg != ''

    def test_empty(self):
        valid, msg = validate_bazi_string('')
        assert valid is False
        assert msg != ''


class TestValidateDayMaster:

    def test_valid(self):
        for gan in sorted(TIANGAN):
            valid, msg = validate_day_master(gan)
            assert valid is True, f'{gan} should be a valid day master'
            assert msg == ''

    def test_invalid(self):
        valid, msg = validate_day_master('X')
        assert valid is False
        assert msg != ''


class TestValidateGender:

    def test_valid(self):
        for gender in VALID_GENDERS:
            valid, msg = validate_gender(gender)
            assert valid is True, f'{gender} should be a valid gender'
            assert msg == ''

    def test_invalid(self):
        valid, msg = validate_gender('alien')
        assert valid is False
        assert msg != ''


class TestAPISDKConsistency:

    def test_sdk_invalid_bazi_rejected(self):
        result = full_analysis({'八字': 'bad', '日主': '丁', '性别': '女'})
        assert result['status'] == 'invalid_input'
        assert 'errors' in result

    def test_sdk_invalid_day_master_rejected(self):
        result = full_analysis({'八字': '壬午 乙巳 丁亥 癸卯', '日主': 'X', '性别': '女'})
        assert result['status'] == 'invalid_input'

    def test_sdk_invalid_gender_rejected(self):
        result = full_analysis({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': 'unknown'})
        assert result['status'] == 'invalid_input'

    def test_sdk_missing_fields_rejected(self):
        result = full_analysis({})
        assert result['status'] == 'invalid_input'

    def test_api_and_sdk_same_invalid_input(self):
        from server.analysis import _validate_input
        invalid = {'八字': 'bad', '日主': 'X', '性别': 'unknown'}
        sdk_result = full_analysis(invalid)
        api_validation = _validate_input(invalid)
        assert sdk_result['status'] == 'invalid_input'
        assert api_validation['valid'] is False
