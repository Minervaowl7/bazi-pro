from bazi_pro.core.schools.base import SchoolAnalyzer

SCHOOL_REGISTRY = {}

_LOADED = False


def _ensure_schools_loaded():
    global _LOADED
    if not _LOADED:
        import bazi_pro.core.schools.mangpai  # noqa: F401
        import bazi_pro.core.schools.xinpai  # noqa: F401
        import bazi_pro.core.schools.ziping  # noqa: F401
        _LOADED = True


def school_analyze(mcp_json: dict, school: str = 'ziping') -> dict:
    _ensure_schools_loaded()
    if school == 'all':
        results = {}
        for name, analyzer_cls in SCHOOL_REGISTRY.items():
            results[name] = analyzer_cls().analyze(mcp_json)
        return results
    analyzer_cls = SCHOOL_REGISTRY.get(school)
    if not analyzer_cls:
        return {'status': 'error', 'message': f'未知流派: {school}'}
    return analyzer_cls().analyze(mcp_json)


def register_school(name: str, analyzer_cls):
    SCHOOL_REGISTRY[name] = analyzer_cls


__all__ = ['SchoolAnalyzer', 'SCHOOL_REGISTRY', 'school_analyze', 'register_school']
