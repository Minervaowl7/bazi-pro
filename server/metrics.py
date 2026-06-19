"""
bazi-pro 指标模块 — Prometheus 指标暴露

提供请求计数、延迟直方图、错误计数等指标，
通过 /metrics 端点暴露给 Prometheus 抓取。

指标列表：
  - bazi_requests_total: 请求总数（按 method/status/endpoint 分类）
  - bazi_request_duration_seconds: 请求延迟直方图
  - bazi_analysis_total: 分析请求总数（按 school/status 分类）
  - bazi_analysis_duration_seconds: 分析延迟直方图
  - bazi_cache_hits_total: 缓存命中总数
  - bazi_cache_misses_total: 缓存未命中总数
  - bazi_llm_calls_total: LLM 调用总数（按 status 分类）
  - bazi_llm_duration_seconds: LLM 调用延迟直方图
  - bazi_rate_limited_total: 被限流的请求总数

使用方式：
  from server.metrics import metrics_middleware, metrics_endpoint, ANALYSIS_DURATION
  # 在 app 中添加中间件和端点
"""

import logging
import time
from typing import Optional

logger = logging.getLogger("bazi-pro.metrics")

# Prometheus 指标存储（纯 Python 实现，无需 prometheus_client 依赖）
# 如果 prometheus_client 可用，使用它；否则使用内存计数器


class _MetricsStore:
    """轻量级指标存储（无外部依赖）"""

    def __init__(self):
        self._counters: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._lock = None  # 单线程访问，无需锁

    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[dict] = None):
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0.0) + value

    def observe_histogram(self, name: str, value: float, labels: Optional[dict] = None):
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def get_counter(self, name: str, labels: Optional[dict] = None) -> float:
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_histogram(self, name: str, labels: Optional[dict] = None) -> list[float]:
        key = self._make_key(name, labels)
        return self._histograms.get(key, [])

    def get_all_metrics(self) -> dict:
        return {
            'counters': dict(self._counters),
            'histograms': {
                k: {
                    'count': len(v),
                    'sum': sum(v),
                    'avg': sum(v) / len(v) if v else 0,
                    'min': min(v) if v else 0,
                    'max': max(v) if v else 0,
                }
                for k, v in self._histograms.items()
            },
        }

    def _make_key(self, name: str, labels: Optional[dict]) -> str:
        if not labels:
            return name
        label_str = ','.join(f'{k}={v}' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}}'


_store = _MetricsStore()

# ── 指标名称常量 ──

REQUESTS_TOTAL = 'bazi_requests_total'
REQUEST_DURATION = 'bazi_request_duration_seconds'
ANALYSIS_TOTAL = 'bazi_analysis_total'
ANALYSIS_DURATION = 'bazi_analysis_duration_seconds'
CACHE_HITS = 'bazi_cache_hits_total'
CACHE_MISSES = 'bazi_cache_misses_total'
LLM_CALLS = 'bazi_llm_calls_total'
LLM_DURATION = 'bazi_llm_duration_seconds'
RATE_LIMITED = 'bazi_rate_limited_total'


# ── 公开 API ──

def inc_counter(name: str, value: float = 1.0, labels: Optional[dict] = None):
    """递增计数器"""
    _store.inc_counter(name, value, labels)


def observe_histogram(name: str, value: float, labels: Optional[dict] = None):
    """记录直方图观测值"""
    _store.observe_histogram(name, value, labels)


def record_cache_hit():
    """记录缓存命中"""
    _store.inc_counter(CACHE_HITS)


def record_cache_miss():
    """记录缓存未命中"""
    _store.inc_counter(CACHE_MISSES)


def record_rate_limited():
    """记录限流事件"""
    _store.inc_counter(RATE_LIMITED)


def get_metrics_snapshot() -> dict:
    """获取当前指标快照"""
    return _store.get_all_metrics()


def format_prometheus_text() -> str:
    """格式化为 Prometheus text exposition 格式"""
    lines = []
    metrics = _store.get_all_metrics()

    for name, value in metrics['counters'].items():
        lines.append(f'# TYPE {name.split("{")[0]} counter')
        lines.append(f'{name} {value}')

    for name, stats in metrics['histograms'].items():
        base = name.split('{')[0]
        labels = name[len(base):]
        lines.append(f'# TYPE {base} histogram')
        lines.append(f'{base}_count{labels} {stats["count"]}')
        lines.append(f'{base}_sum{labels} {stats["sum"]}')

    return '\n'.join(lines) + '\n'


class _TimerContext:
    """计时器上下文管理器"""

    def __init__(self, metric_name: str, labels: Optional[dict] = None):
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.monotonic() - self.start_time
            _store.observe_histogram(self.metric_name, duration, self.labels)
        return False


def timer(metric_name: str, labels: Optional[dict] = None) -> _TimerContext:
    """创建计时器上下文管理器

    用法:
        with timer(ANALYSIS_DURATION, {'school': 'ziping'}):
            result = do_analysis()
    """
    return _TimerContext(metric_name, labels)


# ── FastAPI 中间件 ──

def create_metrics_middleware():
    """创建 FastAPI ASGI 中间件，自动记录请求指标"""

    class MetricsMiddleware:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http":
                await self.app(scope, receive, send)
                return

            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "/")

            # 跳过 /metrics 端点自身的指标
            if path == "/metrics":
                await self.app(scope, receive, send)
                return

            start_time = time.monotonic()
            status_code = [200]

            async def send_with_status(message):
                if message["type"] == "http.response.start":
                    status_code[0] = message.get("status", 200)
                await send(message)

            try:
                await self.app(scope, receive, send_with_status)
            finally:
                duration = time.monotonic() - start_time
                labels = {
                    'method': method,
                    'status': str(status_code[0]),
                    'endpoint': _normalize_path(path),
                }
                _store.inc_counter(REQUESTS_TOTAL, 1.0, labels)
                _store.observe_histogram(REQUEST_DURATION, duration, labels)

                if status_code[0] >= 500:
                    _store.inc_counter('bazi_errors_total', 1.0, {'status': str(status_code[0])})

    return MetricsMiddleware


def _normalize_path(path: str) -> str:
    """将路径中的 ID 参数归一化（如 /api/analysis/ana_abc123 → /api/analysis/{id}）"""
    import re
    # 归一化分析 ID
    path = re.sub(r'/ana_[0-9a-f]+', '/{id}', path)
    # 归一化数字 ID
    path = re.sub(r'/\d+', '/{id}', path)
    return path
