from bazi_pro.core.branches import ZHI_CANGGAN


def get_canggan(zhi: str) -> list[tuple[str, str]]:
    return ZHI_CANGGAN.get(zhi, [])
