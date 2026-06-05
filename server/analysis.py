#!/usr/bin/env python3
"""
bazi-pro 异步分析编排 v5.0
包装现有的同步 bazi_pro 模块，通过 asyncio.to_thread() 执行
"""

import asyncio
import hashlib
import json
import logging
import re
import traceback
from datetime import datetime, timezone

from bazi_pro import GAN_WUXING, ZHI_WUXING, derive_shishen
from bazi_pro.core import (
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
from bazi_pro.core.branches import SHIER_CHANGSHENG
from bazi_pro.paipan import paipan_from_datetime
from server.cache import get_cache
from server.gongwei import calc_gongwei
from server.nayin import lookup_nayin
from server.shensha import calc_shensha_enhanced
from server.ws import manager

logger = logging.getLogger(__name__)

try:
    from bazi_pro.core.schools import school_analyze
except ImportError:
    school_analyze = None


async def run_analysis(mcp_json: dict, run_id: str,
                       detail_level: str = 'standard',
                       school: str = 'ziping') -> dict:
    for key in list(mcp_json.keys()):
        if mcp_json[key] is None:
            mcp_json[key] = ''

    cache = get_cache()

    cache_key = _make_cache_key(mcp_json, detail_level, school)
    cached = cache.get(cache_key)
    if cached:
        await manager.send_progress(run_id, 'cache', 'done',
                                     '命中缓存，直接返回结果')
        return cached

    result = {
        'run_id': run_id,
        'status': 'completed',
        'detail_level': detail_level,
        'school': school,
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
        await asyncio.sleep(0)
        validation = _validate_input(mcp_json)
        await manager.send_progress(run_id, '1', 'done', '数据校验完成', validation)
        result['validation'] = validation

        if not validation['valid']:
            result['status'] = 'invalid_input'
            result['errors'] = validation.get('errors', [])
            await manager.send_progress(run_id, 'error', 'failed',
                                         f'输入数据校验失败: {validation.get("errors", [])}')
            return result

        bazi = mcp_json.get('八字') or ''
        day_master = mcp_json.get('日主') or ''
        bazi_parts = bazi.split()
        month_zhi = bazi_parts[1][1] if len(bazi_parts) >= 2 and len(bazi_parts[1]) >= 2 else ''

        paipan_result = None
        solar = mcp_json.get('阳历') or ''
        gender = mcp_json.get('性别') or ''
        if solar and gender:
            try:
                paipan_result = paipan_from_datetime(solar, gender)
            except Exception:
                paipan_result = None

        await manager.send_progress(run_id, '0', 'running', '古籍条文检索中...')
        retrieval = await _do_retrieve(mcp_json)
        await manager.send_progress(run_id, '0', 'done',
                                     f'检索完成，命中 {len(retrieval.get("results", []))} 条',
                                     retrieval)
        # 预留 analysis_context，后续在 pattern/yongshen/strength 计算完成后回填
        retrieval.setdefault('analysis_context', {})
        result['retrieval'] = retrieval

        element_forces = _estimate_elements(mcp_json, bazi_parts, month_zhi)

        await manager.send_progress(run_id, '2', 'running', '日主旺衰判断中...')
        await asyncio.sleep(0)
        strength = _estimate_strength(mcp_json, bazi_parts, month_zhi,
                                      element_forces=element_forces)
        await manager.send_progress(run_id, '2', 'done',
                                     f'旺衰: {strength.get("wangshuai", {}).get("verdict", "未知")}',
                                     strength)
        result['strength'] = strength

        await manager.send_progress(run_id, '3', 'running', '格局判定中...')
        await asyncio.sleep(0)
        pattern = _estimate_pattern(mcp_json, bazi_parts,
                                     strength.get('wangshuai', {}),
                                     element_forces)
        await manager.send_progress(run_id, '3', 'done',
                                     f'格局: {pattern.get("pattern", "未知")}',
                                     pattern)
        result['pattern'] = pattern

        await manager.send_progress(run_id, '4', 'running', '十神推导中...')
        await asyncio.sleep(0)
        shishen = _derive_shishen(mcp_json, bazi_parts)
        await manager.send_progress(run_id, '4', 'done', '十神推导完成', shishen)
        result['shishen'] = shishen

        gongwei = calc_gongwei(bazi_parts)
        if gongwei:
            result['gongwei'] = gongwei

        shensha = await calc_shensha_enhanced(bazi_parts, solar, 1 if gender == "男" else 0)
        if shensha:
            result['shensha'] = shensha

        await manager.send_progress(run_id, '4b', 'running', '喜用神候选推导中...')
        await asyncio.sleep(0)
        yongshen = _derive_yongshen(day_master, bazi_parts,
                                     pattern, strength.get('wangshuai', {}),
                                     element_forces)
        await manager.send_progress(run_id, '4b', 'done',
                                     f'用神: {yongshen.get("yongshen", "待定")}',
                                     yongshen)
        result['yongshen'] = yongshen

        await manager.send_progress(run_id, '5', 'running', '五行力量分析中...')
        await asyncio.sleep(0)
        await manager.send_progress(run_id, '5', 'done', '五行力量分析完成', element_forces)
        result['elements'] = element_forces

        await manager.send_progress(run_id, '5b', 'running', '调候查表中...')
        await asyncio.sleep(0)
        try:
            from bazi_pro.core.tiaohou import lookup_tiaohou
            tiaohou = lookup_tiaohou(day_master, month_zhi)
        except Exception:
            tiaohou = {'has_tiaohou': False, 'tiaohou_gan': [], 'tiaohou_wx': []}
        await manager.send_progress(run_id, '5b', 'done', '调候查表完成', tiaohou)
        result['tiaohou'] = tiaohou

        await manager.send_progress(run_id, '7', 'running', '刑冲合害检测中...')
        await asyncio.sleep(0)
        relations = _detect_relations(bazi_parts)
        await manager.send_progress(run_id, '7', 'done',
                                     f'检测到 {len(relations)} 条刑冲合害关系',
                                     relations)
        result['relations'] = relations

        # 将分析上下文回填到 retrieval，供下游 RAG/LLM 使用
        if 'retrieval' in result:
            result['retrieval']['analysis_context'] = {
                'day_master': day_master,
                'bazi': bazi,
                'gender': gender,
                'wangshuai': strength.get('wangshuai', {}),
                'pattern': pattern,
                'yongshen': yongshen,
                'elements': element_forces,
                'tiaohou': tiaohou,
                'relations': relations,
                'shishen': shishen,
                'school': school,
            }

        await manager.send_progress(run_id, '9', 'done', '全部分析步骤完成')

        if solar:
            try:
                m = re.match(r'(\d{4})', solar)
                if m:
                    result['birth_year'] = int(m.group(1))
            except (ValueError, TypeError):
                pass

        if paipan_result and 'dayun' in paipan_result:
            dayun_list = [
                {**step,
                 'gan_wuxing': GAN_WUXING.get(step.get('gan', ''), ''),
                 'zhi_wuxing': ZHI_WUXING.get(step.get('zhi', ''), '')}
                for step in paipan_result['dayun']
            ]
            result['dayun'] = dayun_list
            result['qiyun_age'] = paipan_result.get('qiyun_age', 5)
            mcp_json['dayun'] = dayun_list

        if school_analyze:
            await manager.send_progress(run_id, 'school', 'running', '流派分析中...')
            try:
                if school == 'all':
                    school_results = school_analyze(mcp_json, 'all')
                    result['school_analyses'] = school_results
                else:
                    school_result = school_analyze(mcp_json, school)
                    result['school_analysis'] = school_result
                await manager.send_progress(run_id, 'school', 'done', '流派分析完成')
            except Exception as e:
                result['school_warning'] = f'流派分析失败: {str(e)}'
                await manager.send_progress(run_id, 'school', 'done', '流派分析跳过')

        # 紫微斗数排盘（可选，依赖 iztro-py）

        # ── 命局层次评分（确定性，无 LLM） ──
        try:
            from server.chart_quality import calculate_chart_quality
            chart_quality = calculate_chart_quality(result, result.get('dayun', []))
            result['chart_quality'] = chart_quality
            await manager.send_progress(run_id, 'quality', 'done',
                                        f'命局评分: {chart_quality["total"]}/{chart_quality["total_max"]}',
                                        chart_quality)
        except Exception as e:
            logger.warning("chart_quality failed (non-fatal): %s", e)

        # ── LLM 命盘总览（自动触发，可选） ──
        try:
            from server.llm import chat_completion, is_llm_configured
            if is_llm_configured():
                await manager.send_progress(run_id, 'llm', 'running', 'AI 命盘总览生成中...')
                overview_prompt = _build_overview_prompt(result, mcp_json, result.get('dayun', []))
                overview_messages = [
                    {"role": "system", "content": OVERVIEW_SYSTEM_PROMPT},
                    {"role": "user", "content": overview_prompt},
                ]
                overview_text = await chat_completion(overview_messages, temperature=0.6, max_tokens=4096)
                if overview_text:
                    result['llm_overview'] = overview_text
                    await manager.send_progress(run_id, 'llm', 'done', 'AI 命盘总览完成')
                else:
                    await manager.send_progress(run_id, 'llm', 'done', 'AI 命盘总览（无输出）')
        except Exception as e:
            logger.debug("LLM overview generation failed (non-fatal): %s", e)
            await manager.send_progress(run_id, 'llm', 'done', 'AI 命盘总览跳过')

        if solar and gender:
            try:
                from server.ziwei import get_ziwei_chart
                # 从阳历字段提取出生小时（格式 "2002-05-19 06:14"）
                # mcp_json 无"时辰"字段，需从阳历时间部分解析
                _hour = 12  # 默认午时
                if solar and ' ' in solar:
                    try:
                        _time_part = solar.split()[1]
                        _hour = int(_time_part.split(':')[0])
                    except (ValueError, IndexError):
                        pass
                _gender_num = 1 if gender == "男" else 0
                ziwei = await asyncio.to_thread(
                    get_ziwei_chart,
                    solar_date=solar.split()[0] if ' ' in solar else solar,
                    hour=_hour,
                    gender=_gender_num,
                )
                if "error" not in ziwei:
                    result['ziwei'] = ziwei
            except Exception:
                pass  # 紫微斗数为可选功能，失败不影响主流程

        # ── 多智能体协作分析（可选） ──
        try:
            from server.agents import AgentOrchestrator
            orchestrator = AgentOrchestrator()
            await manager.send_progress(run_id, 'agents', 'running', '多智能体协作分析中...')
            agent_result = await orchestrator.analyze(mcp_json)
            if agent_result and agent_result.get('status') != 'failed':
                result['agent_analysis'] = agent_result
                await manager.send_progress(run_id, 'agents', 'done',
                                            f'多智能体分析完成: {agent_result.get("status", "")}',
                                            agent_result)
            else:
                await manager.send_progress(run_id, 'agents', 'done', '多智能体分析跳过')
        except Exception as e:
            logger.warning("Agent orchestration failed (non-fatal): %s", e)
            await manager.send_progress(run_id, 'agents', 'done', '多智能体分析跳过')

        result['completed_at'] = datetime.now(timezone.utc).isoformat()
        cache.set(cache_key, result, ttl=3600)

    except Exception as e:
        logger.error("run_analysis failed: %s\n%s", e, traceback.format_exc())
        result['status'] = 'failed'
        err_msg = str(e) or type(e).__name__
        result['error'] = err_msg
        result['error_type'] = type(e).__name__
        await manager.send_progress(run_id, 'error', 'failed', err_msg)

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
                       month_zhi: str,
                       element_forces: dict | None = None) -> dict:
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
    wangshuai = judge_wangshuai(deling_score, dedi['score'], deshi['score'],
                                 day_master=day_master,
                                 element_forces=element_forces)

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
    changsheng_table = SHIER_CHANGSHENG.get(day_master, {})
    pillars = []
    for i, token in enumerate(bazi_parts):
        if len(token) < 2:
            continue
        gan, zhi = token[0], token[1]
        shishen_gan = derive_shishen(day_master, gan)
        canggan_list = get_canggan(zhi)
        main_cg_gan = canggan_list[0][0] if canggan_list else ''
        shishen_zhi = derive_shishen(day_master, main_cg_gan) if main_cg_gan else ''
        pillars.append({
            'position': positions[i] if i < 4 else '',
            'gan': gan,
            'zhi': zhi,
            'wuxing_gan': GAN_WUXING.get(gan, ''),
            'wuxing_zhi': ZHI_WUXING.get(zhi, ''),
            'shishen': shishen_gan,
            'shishen_gan': shishen_gan,
            'shishen_zhi': shishen_zhi,
            'nayin': lookup_nayin(token),
            'changsheng': changsheng_table.get(zhi, ''),
            'canggan': [{'gan': cg, 'qi': ql,
                          'wuxing': GAN_WUXING.get(cg, ''),
                          'shishen': derive_shishen(day_master, cg)}
                         for cg, ql in canggan_list],
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


_ANALYSIS_VERSION = "v5"


def _make_cache_key(mcp_json: dict, detail_level: str, school: str = 'ziping') -> str:
    key_data = {
        "八字": mcp_json.get("八字", ""),
        "日主": mcp_json.get("日主", ""),
        "性别": mcp_json.get("性别", ""),
        "阳历": mcp_json.get("阳历", ""),
        "农历": mcp_json.get("农历", ""),
        "大运": mcp_json.get("大运", []),
        "detail_level": detail_level,
        "school": school,
        "analysis_version": _ANALYSIS_VERSION,
    }
    raw = json.dumps(key_data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "bazi:v5:%s" % hashlib.sha256(raw.encode()).hexdigest()[:24]


OVERVIEW_SYSTEM_PROMPT = """你是一位精通中国传统命理学的资深命理师，从业四十余年，精通子平法、盲派、新派。
现在命主已经完成了八字排盘和确定性计算，你需要基于这些确定性数据，为命主生成一份专业、深入、有温度的命盘总览报告。

要求：
1. 严格基于提供的确定性数据（四柱、旺衰、格局、用神、五行力量、大运等）进行解读，不要编造数据
2. 用古典命理术语行文，但要让普通人能读懂
3. 分析要有深度，不能泛泛而谈，要结合具体干支、十神、五行力量数据
4. 大运分析要结合命局喜忌，判断每步大运的吉凶趋势
5. 语气沉稳、有分寸，不夸大吉凶
6. 如果格局有破，要如实指出，并说明大运如何补救
7. 输出使用 Markdown 格式"""


def _build_overview_prompt(result: dict, mcp_json: dict, dayun_list: list | None) -> str:
    """构建命盘总览的 LLM prompt"""
    bazi = mcp_json.get('八字', '')
    gender = mcp_json.get('性别', '男')
    day_master = mcp_json.get('日主', '')

    ws = result.get('strength', {}).get('wangshuai', {})
    pat = result.get('pattern', {})
    ys = result.get('yongshen', {})
    ef = result.get('elements', {})
    pct = ef.get('percent', {})
    th = result.get('tiaohou', {})
    rels = result.get('relations', [])

    dayun_str = ""
    if dayun_list:
        for dy in dayun_list:
            if isinstance(dy, dict):
                dayun_str += f"  {dy.get('age_range', '')}: {dy.get('gan', '')}{dy.get('zhi', '')}（{dy.get('wuxing_gan', '')}{dy.get('wuxing_zhi', '')}）\n"

    rels_str = ""
    if rels:
        for r in rels[:10]:
            if isinstance(r, dict):
                rels_str += f"  {r.get('description', r.get('type', ''))}\n"

    prompt = f"""请为以下命主生成命盘总览报告：

【基本信息】
八字：{bazi}
性别：{gender}
日主：{day_master}

【旺衰判定】
得令：{ws.get('deling_score', 0)}分
得地：{ws.get('dedi_score', 0):.1f}分
得势：{ws.get('deshi_score', 0):.1f}分
综合判定：{ws.get('verdict', '未知')}

【格局判定】
格局：{pat.get('pattern', '未知')}
置信度：{pat.get('confidence', 0):.0%}
格局说明：{pat.get('reason', '')}

【用神推导】
用神五行：{ys.get('yongshen', '待定')}
喜神：{', '.join(ys.get('xishen', []))}
忌神：{', '.join(ys.get('jishen', []))}

【五行力量分布】
木：{pct.get('木', 0):.1f}%  火：{pct.get('火', 0):.1f}%  土：{pct.get('土', 0):.1f}%  金：{pct.get('金', 0):.1f}%  水：{pct.get('水', 0):.1f}%

【调候用神】
调候：{th.get('description', '无特殊调候需求')}

【刑冲合害】
{rels_str if rels_str else '  无特殊刑冲合害关系'}

【大运】
{dayun_str if dayun_str else '  大运数据不可用'}

请按以下结构生成报告（使用 Markdown 格式）：

## 命盘总览
（综合八字格局、旺衰、用神的整体定位，2-3段）

## 性格特征
（基于日主五行、十神配置、格局特征分析性格，3-4个要点）

## 事业方向
（基于用神和格局分析适合的事业方向和发展模式）

## 财运分析
（基于财星状态和格局分析财运特征）

## 感情婚姻
（基于日支、妻星/夫星、刑冲合害分析感情特征）

## 大运走势
（结合大运和命局喜忌，分析每步大运的吉凶趋势和注意事项）

## 健康提示
（基于五行偏枯分析健康隐患和养生建议）
"""
    return prompt
