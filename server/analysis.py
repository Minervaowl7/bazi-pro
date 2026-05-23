#!/usr/bin/env python3
"""
bazi-pro 异步分析编排 v5.0
包装现有的同步 bazi_pro 模块，通过 asyncio.to_thread() 执行
"""

import asyncio
import hashlib
import json
from datetime import datetime, timezone

from bazi_pro import GAN_WUXING, ZHI_WUXING, derive_shishen
from bazi_pro.core_rules import (
    calc_dedi,
    calc_deling,
    calc_deshi,
    calc_element_forces,
    derive_yongshen,
    detect_relations,
    get_canggan,
    judge_wangshuai,
    screen_pattern,
)
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
        'disclaimer': '本分析仅供传统文化学习与参考，不构成任何决策依据。',
        'source_attribution': {
            '规则推导': '十神、藏干、旺衰、格局筛查(L0-3)、喜用神、刑冲合害',
            '古籍检索': 'BM25 检索 6 部经典 2964 条条文',
            'LLM辅助解释': '调候用神、多候选格局裁决、分维度解读（需外部 LLM）',
        },
    }

    try:
        await manager.send_progress(run_id, '1', 'running', '数据校验中...')
        await asyncio.sleep(0.05)
        validation = _validate_input(mcp_json)
        await manager.send_progress(run_id, '1', 'done', '数据校验完成', validation)
        result['validation'] = validation

        if not validation['valid']:
            result['status'] = 'invalid_input'
            result['errors'] = validation.get('errors', [])
            await manager.send_progress(run_id, 'error', 'failed',
                                         f'输入数据校验失败: {validation.get("errors", [])}')
            return result

        bazi = mcp_json.get('八字', '')
        day_master = mcp_json.get('日主', '')
        bazi_parts = bazi.split()
        month_zhi = bazi_parts[1][1] if len(bazi_parts) >= 2 and len(bazi_parts[1]) >= 2 else ''

        await manager.send_progress(run_id, '0', 'running', '古籍条文检索中...')
        retrieval = await _do_retrieve(mcp_json)
        await manager.send_progress(run_id, '0', 'done',
                                     f'检索完成，命中 {len(retrieval.get("results", []))} 条',
                                     retrieval)
        result['retrieval'] = retrieval

        await manager.send_progress(run_id, '2', 'running', '日主旺衰判断中...')
        await asyncio.sleep(0.05)
        strength = _estimate_strength(mcp_json, bazi_parts, month_zhi)
        await manager.send_progress(run_id, '2', 'done',
                                     f'旺衰: {strength.get("wangshuai", {}).get("verdict", "未知")}',
                                     strength)
        result['strength'] = strength

        element_forces = _estimate_elements(mcp_json, bazi_parts, month_zhi)

        await manager.send_progress(run_id, '3', 'running', '格局判定中...')
        await asyncio.sleep(0.05)
        pattern = _estimate_pattern(mcp_json, bazi_parts,
                                     strength.get('wangshuai', {}),
                                     element_forces)
        await manager.send_progress(run_id, '3', 'done',
                                     f'格局: {pattern.get("pattern", "未知")}',
                                     pattern)
        result['pattern'] = pattern

        await manager.send_progress(run_id, '4', 'running', '十神推导中...')
        await asyncio.sleep(0.05)
        shishen = _derive_shishen(mcp_json, bazi_parts)
        await manager.send_progress(run_id, '4', 'done', '十神推导完成', shishen)
        result['shishen'] = shishen

        await manager.send_progress(run_id, '4b', 'running', '喜用神候选推导中...')
        await asyncio.sleep(0.05)
        yongshen = _derive_yongshen(day_master, bazi_parts,
                                     pattern, strength.get('wangshuai', {}),
                                     element_forces)
        await manager.send_progress(run_id, '4b', 'done',
                                     f'用神: {yongshen.get("yongshen", "待定")}',
                                     yongshen)
        result['yongshen'] = yongshen

        await manager.send_progress(run_id, '5', 'running', '五行力量分析中...')
        await asyncio.sleep(0.05)
        await manager.send_progress(run_id, '5', 'done', '五行力量分析完成', element_forces)
        result['elements'] = element_forces

        await manager.send_progress(run_id, '7', 'running', '刑冲合害检测中...')
        await asyncio.sleep(0.05)
        relations = _detect_relations(bazi_parts)
        await manager.send_progress(run_id, '7', 'done',
                                     f'检测到 {len(relations)} 条刑冲合害关系',
                                     relations)
        result['relations'] = relations

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
            from bazi_pro.retrieve_classical import _resolve_corpus, retrieve
            day_master = mcp_json.get('日主', '')
            bazi = mcp_json.get('八字', '')
            query = f'{day_master} {bazi} 格局 旺衰'
            corpus = _resolve_corpus()
            return retrieve(corpus, query, k=5)
        except Exception as e:
            return {'mode': 'fallback', 'error': str(e), 'results': []}
    return await asyncio.to_thread(_sync)


def _validate_input(mcp_json: dict) -> dict:
    from bazi_pro.validation import validate_bazi_input
    result = validate_bazi_input(mcp_json)
    result['bazi'] = mcp_json.get('八字', '')
    result['day_master'] = mcp_json.get('日主', '')
    result['gender'] = mcp_json.get('性别', '')
    return result


def _estimate_strength(mcp_json: dict, bazi_parts: list[str],
                       month_zhi: str) -> dict:
    day_master = mcp_json.get('日主', '')

    if not day_master or not month_zhi or len(bazi_parts) < 2:
        return {
            'day_master': day_master,
            'deling': {'status': '', 'score': 0},
            'dedi': {'score': 0.0, 'details': [], 'level': '不得地'},
            'deshi': {'score': 0.0, 'details': [], 'level': '不得势'},
            'wangshuai': {'verdict': '数据不足', 'deling_score': 0,
                          'dedi_score': 0.0, 'deshi_score': 0.0,
                          'is_weak': False, 'is_strong': False,
                          'is_extreme_weak': False, 'is_extreme_strong': False},
        }

    deling_status, deling_score = calc_deling(day_master, month_zhi)
    dedi = calc_dedi(day_master, bazi_parts)
    deshi = calc_deshi(day_master, bazi_parts)
    wangshuai = judge_wangshuai(deling_score, dedi['score'], deshi['score'])

    return {
        'day_master': day_master,
        'deling': {'status': deling_status, 'score': deling_score},
        'dedi': dedi,
        'deshi': deshi,
        'wangshuai': wangshuai,
    }


def _estimate_pattern(mcp_json: dict, bazi_parts: list[str],
                      wangshuai: dict, element_forces: dict) -> dict:
    day_master = mcp_json.get('日主', '')
    return screen_pattern(day_master, bazi_parts, wangshuai, element_forces)


def _derive_shishen(mcp_json: dict, bazi_parts: list[str]) -> dict:
    day_master = mcp_json.get('日主', '')
    if not day_master or not bazi_parts:
        return {'pillars': [], 'note': '日主或八字数据缺失'}

    positions = ['年', '月', '日', '时']
    pillars = []
    for i, token in enumerate(bazi_parts):
        if len(token) < 2:
            continue
        gan, zhi = token[0], token[1]
        canggan = get_canggan(zhi)
        pillars.append({
            'position': positions[i] if i < 4 else '',
            'gan': gan,
            'zhi': zhi,
            'wuxing_gan': GAN_WUXING.get(gan, ''),
            'wuxing_zhi': ZHI_WUXING.get(zhi, ''),
            'shishen': derive_shishen(day_master, gan),
            'canggan': [{'gan': cg, 'qi': ql,
                          'wuxing': GAN_WUXING.get(cg, ''),
                          'shishen': derive_shishen(day_master, cg)}
                         for cg, ql in canggan],
        })
    return {'pillars': pillars}


def _estimate_elements(mcp_json: dict, bazi_parts: list[str],
                       month_zhi: str) -> dict:
    if not bazi_parts or not month_zhi:
        return {
            'raw': {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0},
            'percent': {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0},
            'total': 0,
            'note': '八字数据缺失',
        }

    return calc_element_forces(bazi_parts, month_zhi)


def _derive_yongshen(day_master: str, bazi_parts: list[str],
                     pattern: dict, wangshuai: dict,
                     element_forces: dict) -> dict:
    if not day_master or not bazi_parts:
        return {'yongshen': '待定', 'xishen': [], 'jishen': [], 'confidence': 0}

    return derive_yongshen(day_master, bazi_parts, pattern,
                           wangshuai, element_forces)


def _detect_relations(bazi_parts: list[str]) -> list[dict]:
    if not bazi_parts:
        return []

    return detect_relations(bazi_parts)


_ANALYSIS_VERSION = "v2"


def _make_cache_key(mcp_json: dict, detail_level: str) -> str:
    key_data = {
        "八字": mcp_json.get("八字", ""),
        "日主": mcp_json.get("日主", ""),
        "性别": mcp_json.get("性别", ""),
        "阳历": mcp_json.get("阳历", ""),
        "农历": mcp_json.get("农历", ""),
        "大运": mcp_json.get("大运", []),
        "detail_level": detail_level,
        "analysis_version": _ANALYSIS_VERSION,
    }
    raw = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    return f'bazi:{hashlib.sha256(raw.encode()).hexdigest()[:32]}'
