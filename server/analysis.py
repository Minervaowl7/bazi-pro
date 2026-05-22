#!/usr/bin/env python3
"""
bazi-pro 异步分析编排 v4.6
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
    """异步执行八字分析流程，通过 WebSocket 推送进度

    Args:
        mcp_json: Bazi MCP 返回的 JSON 数据
        run_id: 分析运行 ID
        detail_level: 'brief' | 'standard' | 'detailed'

    Returns:
        分析结果 dict
    """
    cache = get_cache()

    # 检查缓存
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
        # Step 0: 检索
        await manager.send_progress(run_id, '0', 'running', '古籍条文检索中...')
        retrieval = await _do_retrieve(mcp_json)
        await manager.send_progress(run_id, '0', 'done',
                                     f'检索完成，命中 {len(retrieval.get("results", []))} 条',
                                     retrieval)
        result['retrieval'] = retrieval

        # Step 1: 数据校验
        await manager.send_progress(run_id, '1', 'running', '数据校验中...')
        await asyncio.sleep(0.1)
        validation = _validate_input(mcp_json)
        await manager.send_progress(run_id, '1', 'done', '数据校验完成', validation)
        result['validation'] = validation

        # Step 2: 旺衰判断
        await manager.send_progress(run_id, '2', 'running', '日主旺衰判断中...')
        await asyncio.sleep(0.05)
        strength = _estimate_strength(mcp_json)
        await manager.send_progress(run_id, '2', 'done',
                                     f'旺衰: {strength.get("level", "未知")}',
                                     strength)
        result['strength'] = strength

        # Step 3-4: 格局+喜用
        await manager.send_progress(run_id, '3', 'running', '格局判定中...')
        await asyncio.sleep(0.05)
        pattern = _estimate_pattern(mcp_json, strength)
        await manager.send_progress(run_id, '3', 'done',
                                     f'格局: {pattern.get("name", "未知")}',
                                     pattern)
        result['pattern'] = pattern

        # Step 5-8: 简化的后续步骤
        await manager.send_progress(run_id, '5', 'running', '五行力量分析中...')
        elements = _estimate_elements(mcp_json)
        await manager.send_progress(run_id, '5', 'done', '五行力量分析完成', elements)
        result['elements'] = elements

        # Step 9: 完成
        await manager.send_progress(run_id, '9', 'done', '全部分析步骤完成')

        result['completed_at'] = datetime.now(timezone.utc).isoformat()
        cache.set(cache_key, result, ttl=3600)

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        await manager.send_progress(run_id, 'error', 'failed', str(e))

    return result


async def _do_retrieve(mcp_json: dict) -> dict:
    """异步执行古籍检索"""
    def _sync():
        try:
            from bazi_pro.retrieve_classical import retrieve
            # 构造查询词
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
    """校验输入数据"""
    required = ['八字', '日主', '性别']
    missing = [f for f in required if f not in mcp_json]
    return {
        'valid': len(missing) == 0,
        'missing_fields': missing,
        'bazi': mcp_json.get('八字', ''),
        'day_master': mcp_json.get('日主', ''),
        'gender': mcp_json.get('性别', ''),
    }


def _estimate_strength(mcp_json: dict) -> dict:
    """估计日主旺衰（简化版，详细分析由 LLM 完成）"""
    day_master = mcp_json.get('日主', '')
    # 简化：返回基本数据，让 LLM 做详细分析
    return {
        'day_master': day_master,
        'level': '待分析',
        'note': '旺衰分析需由 LLM 按照 SKILL.md 第二步量化三要素完成',
    }


def _estimate_pattern(mcp_json: dict, strength: dict) -> dict:
    """估计格局（简化版）"""
    return {
        'name': '待分析',
        'note': '格局判定需由 LLM 按照 SKILL.md 第三步六层筛查完成',
    }


def _estimate_elements(mcp_json: dict) -> dict:
    """五行力量分析（简化版）"""
    return {
        'wood': 0, 'fire': 0, 'earth': 0, 'metal': 0, 'water': 0,
        'note': '五行力量精确计算需由 MCP 或 LLM 完成',
    }


def _make_cache_key(mcp_json: dict, detail_level: str) -> str:
    """生成缓存键"""
    raw = f'{mcp_json.get("八字", "")}|{detail_level}'
    return f'bazi:{hashlib.md5(raw.encode()).hexdigest()[:12]}'
