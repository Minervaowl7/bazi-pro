#!/usr/bin/env python3
"""
bazi-pro 异步分析编排 v5.0
统一调用 bazi_pro.core_rules.full_analysis() 完成确定性计算
"""

import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from bazi_pro.core_rules import full_analysis
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

        await manager.send_progress(run_id, '2', 'running', '确定性核心计算中（旺衰/格局/用神/五行/刑冲合害）...')
        await asyncio.sleep(0.05)
        core = await asyncio.to_thread(full_analysis, mcp_json)
        await manager.send_progress(run_id, '2', 'done',
                                     f'核心计算完成：旺衰={core.get("wangshuai", {}).get("verdict", "未知")} 格局={core.get("pattern", {}).get("pattern", "未知")}',
                                     core)

        result['core'] = core
        result['deling'] = core.get('deling', {})
        result['dedi'] = core.get('dedi', {})
        result['deshi'] = core.get('deshi', {})
        result['strength'] = {
            'day_master': mcp_json.get('日主', ''),
            'wangshuai': core.get('wangshuai', {}),
        }
        result['element_forces'] = core.get('element_forces', {})
        result['pattern'] = core.get('pattern', {})
        result['yongshen'] = core.get('yongshen', {})
        result['relations'] = core.get('relations', {})
        result['pillars'] = core.get('pillars', [])
        result['shishen'] = {f"{p['position']}干": p.get('shishen', '')
                             for p in core.get('pillars', []) if p.get('gan')}

        await manager.send_progress(run_id, '9', 'done', '全部分析步骤完成')

        result['completed_at'] = datetime.now(timezone.utc).isoformat()
        cache.set(cache_key, result, ttl=3600)

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = 'Internal server error'
        await manager.send_progress(run_id, 'error', 'failed', 'Internal server error')

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


def _make_cache_key(mcp_json: dict, detail_level: str) -> str:
    raw = f'{mcp_json.get("八字", "")}|{detail_level}'
    return f'bazi:{hashlib.md5(raw.encode()).hexdigest()[:12]}'
