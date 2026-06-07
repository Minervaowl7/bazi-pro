"""十神工具函数 — 四维度分析模块共享的十神查找和透干检测"""
from __future__ import annotations
from bazi_pro.core.constants import GAN_SHISHEN_MAP, derive_shishen
from bazi_pro.core.hidden_stems import get_canggan
from bazi_pro.core.branches import CANGGAN_WEIGHT

def get_transparent_gans(bazi_parts: list[str]) -> set[str]:
    """返回所有透干（天干）的干集合"""
    return {p[0] for p in bazi_parts if len(p) >= 1}

def find_shishen_instances(
    day_master: str,
    target_shishen: str,
    bazi_parts: list[str],
) -> list[dict]:
    """找出命盘中所有属于 target_shishen 的干（天干+藏干）
    Returns list of dicts with keys: gan, position, is_transparent, qi_level, root_weight, pillar_idx
    """
    instances = []
    positions = ['年柱', '月柱', '日柱', '时柱']
    
    for i, part in enumerate(bazi_parts):
        if len(part) < 2:
            continue
        gan, zhi = part[0], part[1]
        pos = positions[i] if i < len(positions) else f'第{i}柱'
        
        # Check transparent gan
        ss = derive_shishen(day_master, gan)
        if ss == target_shishen:
            instances.append({
                'gan': gan,
                'position': f'{pos}{gan}',
                'is_transparent': True,
                'qi_level': '透干',
                'root_weight': 1.0,
                'pillar_idx': i,
            })
        
        # Check hidden stems
        canggan = get_canggan(zhi)
        for cg_gan, qi_level in canggan:
            cg_ss = derive_shishen(day_master, cg_gan)
            if cg_ss == target_shishen:
                weight = CANGGAN_WEIGHT.get(qi_level, 0.3)
                instances.append({
                    'gan': cg_gan,
                    'position': f'{pos}{zhi}({qi_level})',
                    'is_transparent': False,
                    'qi_level': qi_level,
                    'root_weight': weight,
                    'pillar_idx': i,
                })
    
    # Dedup by gan + position
    seen = {}
    for inst in instances:
        key = f"{inst['gan']}_{inst['position']}"
        if key not in seen:
            seen[key] = inst
    return list(seen.values())
