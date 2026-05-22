#!/usr/bin/env python3
"""
bazi-pro 异步分析编排 v5.0
包装现有的同步 bazi_pro 模块，通过 asyncio.to_thread() 执行
"""

import asyncio
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

from server.cache import get_cache
from server.ws import manager


async def run_analysis(mcp_json: dict, run_id: str,
                       detail_level: str = 'standard') -> dict:
    cache = get_cache()

    cache_key = _make_cache_key(mcp_json, detail_level)
    cached = cache.get(cache_key)
    if cached:
        await manager.send_progress(run_id, 'cache', 'done',
                                     '命中缓存，直接返回结果')
        return cached

    result = {
        'run_id': run_id,
        'status': 'completed',
        'detail_level': detail_level,
        'started_at': datetime.now(timezone.utc).isoformat(),
    }

    try:
        await manager.send_progress(run_id, '0', 'running', '古籍条文检索中...')
        retrieval = await _do_retrieve(mcp_json)
        await manager.send_progress(run_id, '0', 'done',
                                     f'检索完成，命中 {len(retrieval.get("results", []))} 条',
                                     retrieval)
        result['retrieval'] = retrieval

        await manager.send_progress(run_id, '1', 'running', '数据校验中...')
        await asyncio.sleep(0.05)
        validation = _validate_input(mcp_json)
        await manager.send_progress(run_id, '1', 'done', '数据校验完成', validation)
        result['validation'] = validation

        if not validation['valid']:
            result['status'] = 'invalid_input'
            result['missing'] = validation['missing_fields']
            await manager.send_progress(run_id, 'error', 'failed',
                                         f'输入数据缺失: {validation["missing_fields"]}')
            return result

        await manager.send_progress(run_id, '2', 'running', '日主旺衰判断中...')
        await asyncio.sleep(0.05)
        strength = _estimate_strength(mcp_json)
        await manager.send_progress(run_id, '2', 'done',
                                     f'旺衰倾向: {strength.get("wuxing_quick", {}).get("tendency", "未知")}',
                                     strength)
        result['strength'] = strength

        await manager.send_progress(run_id, '3', 'running', '格局判定中...')
        await asyncio.sleep(0.05)
        pattern = _estimate_pattern(mcp_json, strength)
        await manager.send_progress(run_id, '3', 'done',
                                     f'格局: {pattern.get("name", "未知")}',
                                     pattern)
        result['pattern'] = pattern

        await manager.send_progress(run_id, '4', 'running', '十神推导中...')
        shishen = _derive_shishen(mcp_json)
        await manager.send_progress(run_id, '4', 'done', '十神推导完成', shishen)
        result['shishen'] = shishen

        await manager.send_progress(run_id, '5', 'running', '五行力量分析中...')
        elements = _estimate_elements(mcp_json)
        await manager.send_progress(run_id, '5', 'done', '五行力量分析完成', elements)
        result['elements'] = elements

        await manager.send_progress(run_id, '9', 'done', '全部分析步骤完成')

        result['completed_at'] = datetime.now(timezone.utc).isoformat()
        cache.set(cache_key, result, ttl=3600)

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        await manager.send_progress(run_id, 'error', 'failed', str(e))

    return result


async def _do_retrieve(mcp_json: dict) -> dict:
    def _sync():
        try:
            from bazi_pro.retrieve_classical import retrieve
            day_master = mcp_json.get('日主', '')
            bazi = mcp_json.get('八字', '')
            query = f'{day_master} {bazi} 格局 旺衰'
            corpus = str(Path(__file__).resolve().parent.parent /
                         'references' / 'classical_corpus.md')
            return retrieve(corpus, query, k=5)
        except Exception as e:
            return {'mode': 'fallback', 'error': str(e), 'results': []}
    return await asyncio.to_thread(_sync)


def _validate_input(mcp_json: dict) -> dict:
    required = ['八字', '日主', '性别']
    missing = [f for f in required if f not in mcp_json]
    bazi = mcp_json.get('八字', '')
    day_master = mcp_json.get('日主', '')
    empty_fields = [f for f, v in [('八字', bazi), ('日主', day_master), ('性别', mcp_json.get('性别', ''))] if not v]
    return {
        'valid': len(missing) == 0 and len(empty_fields) == 0,
        'missing_fields': missing,
        'empty_fields': empty_fields,
        'bazi': bazi,
        'day_master': day_master,
        'gender': mcp_json.get('性别', ''),
    }


def _estimate_strength(mcp_json: dict) -> dict:
    from bazi_pro import GAN_WUXING, count_wuxing_from_bazi, wuxing_pct

    day_master = mcp_json.get('日主', '')
    bazi = mcp_json.get('八字', '')
    dm_wx = GAN_WUXING.get(day_master, '')

    if not dm_wx or not bazi:
        return {
            'day_master': day_master,
            'level': '待分析',
            'note': '旺衰分析需由 LLM 按照 SKILL.md 第二步量化三要素完成',
        }

    wuxing_counts = count_wuxing_from_bazi(bazi)
    sheng_map = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
    sheng_wo = sheng_map.get(dm_wx, '')
    tong_wo = dm_wx

    yin_bi = wuxing_counts.get(sheng_wo, 0) + wuxing_counts.get(tong_wo, 0)
    total = max(1, sum(wuxing_counts.values()))
    yin_bi_pct = round(yin_bi / total * 100, 1)

    if yin_bi_pct >= 75:
        tendency = '极偏·印比主导'
    elif yin_bi_pct >= 60:
        tendency = '偏旺·印比偏重'
    elif yin_bi_pct <= 25:
        tendency = '极偏·克泄耗主导'
    elif yin_bi_pct <= 40:
        tendency = '偏弱·克泄耗偏重'
    else:
        tendency = '相对平衡'

    return {
        'day_master': day_master,
        'wuxing_quick': {
            'tendency': tendency,
            'yin_bi_pct': yin_bi_pct,
            'ke_xie_hao_pct': round(100 - yin_bi_pct, 1),
            'day_master_wuxing': dm_wx,
            'sheng_wo_wuxing': sheng_wo,
        },
        'note': '⚠️ 粗略预检，忽略藏干中余气/合化修正，精确值见第五步',
    }


def _estimate_pattern(mcp_json: dict, strength: dict) -> dict:
    wuxing_quick = strength.get('wuxing_quick', {})
    tendency = wuxing_quick.get('tendency', '')
    return {
        'name': '待LLM分析',
        'wuxing_hint': tendency,
        'note': '格局判定需由 LLM 按照 SKILL.md 第三步六层筛查完成',
    }


def _derive_shishen(mcp_json: dict) -> dict:
    from bazi_pro import derive_shishen

    day_master = mcp_json.get('日主', '')
    bazi = mcp_json.get('八字', '')
    if not day_master or not bazi:
        return {'pillars': [], 'note': '日主或八字数据缺失'}

    parts = bazi.split()
    positions = ['年', '月', '日', '时']
    pillars = []
    for i, token in enumerate(parts):
        if len(token) >= 1:
            gan = token[0]
            pillars.append({
                'position': positions[i] if i < 4 else '',
                'gan': gan,
                'shishen': derive_shishen(day_master, gan),
            })
    return {'pillars': pillars, 'note': '十神推导为确定性计算，无需LLM'}


def _estimate_elements(mcp_json: dict) -> dict:
    from bazi_pro import count_wuxing_from_bazi, wuxing_pct

    bazi = mcp_json.get('八字', '')
    if not bazi:
        return {
            '木': 0, '火': 0, '土': 0, '金': 0, '水': 0,
            'note': '八字数据缺失',
        }

    counts = count_wuxing_from_bazi(bazi)
    pct = wuxing_pct(counts)
    return {
        'counts': counts,
        'percent': pct,
        'note': '⚠️ 基于天干地支本气的粗略统计，精确力量需含藏干中余气加权',
    }


def _make_cache_key(mcp_json: dict, detail_level: str) -> str:
    raw = f'{mcp_json.get("八字", "")}|{detail_level}'
    return f'bazi:{hashlib.md5(raw.encode()).hexdigest()[:12]}'
