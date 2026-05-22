#!/usr/bin/env python3
"""
bazi-pro 历史校准追踪器 v5.0
用户反馈记录 + 准确率统计 + 证据权重动态调整（文件锁保护并发写入）
"""

import json
import threading
from collections import defaultdict
from pathlib import Path


class CalibrationTracker:

    def __init__(self, db_path: str = ''):
        self.db_path = db_path or str(Path.home() / '.bazi-pro' / 'calibration.json')
        self._lock = threading.Lock()
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
        tmp_path = self.db_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        Path(tmp_path).replace(self.db_path)

    def record_feedback(self, analysis_id: str, claim: str,
                        accurate: bool, note: str = '') -> None:
        import datetime
        with self._lock:
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
        return self._data.get('stats', {})

    def apply_calibration_weights(self) -> dict[str, float]:
        stats = self._data.get('stats', {})
        if not stats:
            return {'wangshuai': 1.0, 'pattern': 1.0, 'yongshen': 1.0, 'dayun': 1.0}

        weights = {}
        for claim_type, s in stats.items():
            accuracy = s['accuracy']
            weights[claim_type] = min(1.5, max(0.3, (accuracy - 0.5) * 2.0 + 0.5))

        for key in ['wangshuai', 'pattern', 'yongshen', 'dayun']:
            if key not in weights:
                weights[key] = 1.0

        return weights

    @property
    def total_feedback(self) -> int:
        return len(self._data.get('feedback', []))
