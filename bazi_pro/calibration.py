#!/usr/bin/env python3
"""
bazi-pro 历史校准追踪器 v4.8
用户反馈记录 + 准确率统计 + 证据权重动态调整
"""

import json
from collections import defaultdict
from pathlib import Path


class CalibrationTracker:
    """校准反馈追踪器

    记录用户对分析判断的准确性反馈，统计各类判断的准确率，
    并据此调整证据权重
    """

    def __init__(self, db_path: str = ''):
        self.db_path = db_path or str(Path.home() / '.bazi-pro' / 'calibration.json')
        self._data = self._load()

    def _load(self) -> dict:
        if Path(self.db_path).exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {'feedback': [], 'stats': {}}

    def _save(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def record_feedback(self, analysis_id: str, claim: str,
                        accurate: bool, note: str = '') -> None:
        """记录一条用户反馈"""
        import datetime
        self._data['feedback'].append({
            'analysis_id': analysis_id,
            'claim': claim,
            'accurate': accurate,
            'note': note,
            'timestamp': datetime.datetime.now().isoformat(),
        })
        self._update_stats()
        self._save()

    def _update_stats(self) -> None:
        """更新准确率统计"""
        feedback = self._data['feedback']
        if not feedback:
            return

        claim_stats = defaultdict(lambda: {'accurate': 0, 'total': 0})
        for fb in feedback:
            claim_type = self._classify_claim(fb['claim'])
            claim_stats[claim_type]['total'] += 1
            if fb['accurate']:
                claim_stats[claim_type]['accurate'] += 1

        self._data['stats'] = {}
        for claim_type, counts in claim_stats.items():
            accuracy = counts['accurate'] / counts['total'] if counts['total'] > 0 else 0
            self._data['stats'][claim_type] = {
                'accuracy': round(accuracy, 3),
                'total': counts['total'],
                'accurate': counts['accurate'],
            }

    @staticmethod
    def _classify_claim(claim: str) -> str:
        """将 claim 分类"""
        if any(kw in claim for kw in ['旺衰', '身强', '身弱', '从格', '从强']):
            return 'wangshuai'
        if any(kw in claim for kw in ['格局', '正官', '七杀', '建禄', '羊刃', '从格']):
            return 'pattern'
        if any(kw in claim for kw in ['用神', '喜神', '忌神', '调候']):
            return 'yongshen'
        if any(kw in claim for kw in ['大运', '流年']):
            return 'dayun'
        return 'other'

    def get_calibration_stats(self) -> dict:
        """获取各类型判断准确率统计"""
        return self._data.get('stats', {})

    def apply_calibration_weights(self) -> dict[str, float]:
        """根据历史反馈调整证据权重

        准确率高的判断类型 → 当前分析中权重提升
        准确率低的判断类型 → 权重降低，更依赖古籍证据
        """
        stats = self._data.get('stats', {})
        if not stats:
            return {'wangshuai': 1.0, 'pattern': 1.0, 'yongshen': 1.0, 'dayun': 1.0}

        weights = {}
        for claim_type, s in stats.items():
            accuracy = s['accuracy']
            # 准确率映射到权重：50%→0.5, 75%→1.0, 100%→1.5
            weights[claim_type] = min(1.5, max(0.3, (accuracy - 0.5) * 2.0 + 0.5))

        # 补充默认值
        for key in ['wangshuai', 'pattern', 'yongshen', 'dayun']:
            if key not in weights:
                weights[key] = 1.0

        return weights

    @property
    def total_feedback(self) -> int:
        return len(self._data.get('feedback', []))
