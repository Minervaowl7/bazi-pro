"""MCP 工具适配器 — 封装 MCP 命理工具为 Python 内部调用

单例模式，维护工具注册表，每个工具调用带超时控制和重试机制。
所有工具直接调用 Python 函数，不走 subprocess。
统一返回格式: {"success": bool, "data": dict, "error": str, "source": "internal"}
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger("bazi-pro.mcp")


@dataclass
class ToolMeta:
    """工具注册元数据"""
    name: str
    func: Callable[..., Any]
    timeout: float = 10.0
    max_retries: int = 1
    description: str = ""


@dataclass
class ToolResult:
    """统一工具返回格式"""
    success: bool = False
    data: dict = field(default_factory=dict)
    error: str = ""
    source: str = "internal"
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "success": self.success,
            "source": self.source,
        }
        if self.success:
            d["data"] = self.data
        else:
            d["data"] = {}
            d["error"] = self.error
        return d


def _run_with_timeout(func: Callable, kwargs: dict, timeout: float) -> Any:
    """同步函数带超时包装（在线程中执行）"""
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"工具调用超时 ({timeout}s)")


class MCPToolAdapter:
    """MCP 工具适配器（单例）

    维护工具注册表，提供同步/异步调用入口，支持超时与重试。
    """

    _instance: Optional["MCPToolAdapter"] = None

    def __new__(cls) -> "MCPToolAdapter":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry: dict[str, ToolMeta] = {}
            cls._instance._initialized = False
        return cls._instance

    def _ensure_init(self) -> None:
        if self._initialized:
            return
        self._register_builtin_tools()
        self._initialized = True

    def _register_builtin_tools(self) -> None:
        self.register(ToolMeta(
            name="get_bazi_details",
            func=self._get_bazi_details,
            timeout=10.0,
            max_retries=1,
            description="八字排盘 — 调用 paipan_from_datetime",
        ))
        self.register(ToolMeta(
            name="get_ziwei_chart",
            func=self._get_ziwei_chart,
            timeout=15.0,
            max_retries=1,
            description="紫微斗数排盘 — 调用 server.ziwei.get_ziwei_chart",
        ))
        self.register(ToolMeta(
            name="get_bazi_chart",
            func=self._get_bazi_chart,
            timeout=30.0,
            max_retries=1,
            description="八字完整分析 — 调用 bazi_pro.core.full_analysis",
        ))
        self.register(ToolMeta(
            name="get_bazi_fortune",
            func=self._get_bazi_fortune,
            timeout=15.0,
            max_retries=1,
            description="大运流年评分 — 调用 server.dayun_score",
        ))
        self.register( ToolMeta(
            name="analyze_bazi_element",
            func=self._analyze_bazi_element,
            timeout=10.0,
            max_retries=1,
            description="五行力量计算 — 调用 bazi_pro.core.calc_element_forces",
        ))

    def register(self, meta: ToolMeta) -> None:
        self._registry[meta.name] = meta

    def get_tool(self, name: str) -> Optional[ToolMeta]:
        self._ensure_init()
        return self._registry.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        self._ensure_init()
        return [
            {"name": m.name, "description": m.description}
            for m in self._registry.values()
        ]

    def call(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        """同步调用工具入口"""
        self._ensure_init()
        meta = self._registry.get(tool_name)
        if not meta:
            return ToolResult(
                success=False,
                error=f"未知工具: {tool_name}，可用工具: {', '.join(self._registry.keys())}",
            ).to_dict()

        last_error = ""
        for attempt in range(1, meta.max_retries + 1):
            t0 = time.monotonic()
            try:
                raw = _run_with_timeout(meta.func, kwargs, meta.timeout)
                elapsed = (time.monotonic() - t0) * 1000

                if isinstance(raw, dict) and raw.get("error"):
                    last_error = raw["error"]
                    if attempt < meta.max_retries:
                        logger.warning(
                            "MCP tool %s attempt %d/%d failed: %s",
                            tool_name, attempt, meta.max_retries, last_error,
                        )
                        continue
                    return ToolResult(
                        success=False,
                        error=last_error,
                        elapsed_ms=elapsed,
                    ).to_dict()

                return ToolResult(
                    success=True,
                    data=raw if isinstance(raw, dict) else {"raw": raw},
                    elapsed_ms=elapsed,
                ).to_dict()

            except TimeoutError:
                elapsed = (time.monotonic() - t0) * 1000
                last_error = f"工具调用超时 ({meta.timeout}s)"
                if attempt < meta.max_retries:
                    logger.warning(
                        "MCP tool %s timeout attempt %d/%d",
                        tool_name, attempt, meta.max_retries,
                    )
                    continue
                return ToolResult(
                    success=False,
                    error=last_error,
                    elapsed_ms=elapsed,
                ).to_dict()

            except Exception as e:
                elapsed = (time.monotonic() - t0) * 1000
                last_error = str(e)
                logger.error("MCP tool %s error: %s", tool_name, e)
                return ToolResult(
                    success=False,
                    error=last_error,
                    elapsed_ms=elapsed,
                ).to_dict()

        return ToolResult(success=False, error=last_error).to_dict()

    async def call_tool(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        """异步调用工具入口 — 在线程池中执行同步逻辑"""
        return await asyncio.to_thread(self.call, tool_name, **kwargs)

    # ── 内置工具实现 ────────────────────────────────────────────

    @staticmethod
    def _get_bazi_details(
        year: int = 2000,
        month: int = 1,
        day: int = 1,
        hour: int = 12,
        gender: str = "male",
    ) -> dict[str, Any]:
        from bazi_pro.paipan import paipan_from_datetime

        gender_cn = "男" if gender in ("male", "男", "M", "m", "1") else "女"
        solar = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:00"
        result = paipan_from_datetime(solar, gender_cn)
        if result.get("status") == "error":
            return {"error": result.get("message", "排盘失败")}
        return result

    @staticmethod
    def _get_ziwei_chart(
        date: str = "",
        time_index: int = 6,
        gender: str = "男",
    ) -> dict[str, Any]:
        from server.ziwei import get_ziwei_chart

        gender_num = 1 if gender in ("男", "male", "1", "M") else 0
        result = get_ziwei_chart(solar_date=date, hour=time_index, gender=gender_num)
        return result

    @staticmethod
    def _get_bazi_chart(
        bazi: str = "",
        day_master: str = "",
        gender: str = "男",
        dayun: list | None = None,
    ) -> dict[str, Any]:
        from bazi_pro.core import full_analysis

        mcp_json: dict[str, Any] = {
            "八字": bazi,
            "日主": day_master,
            "性别": gender,
        }
        if dayun:
            mcp_json["dayun"] = dayun
        result = full_analysis(mcp_json)
        return result

    @staticmethod
    def _get_bazi_fortune(
        bazi: str = "",
        day_master: str = "",
        gender: str = "男",
        dayun: list | None = None,
        qiyun_age: int = 5,
        birth_year: int = 0,
        yongshen: str = "",
        jishen: list | None = None,
        xishen: list | None = None,
    ) -> dict[str, Any]:
        from server.dayun_score import score_dayun, score_liunian

        if not dayun:
            from bazi_pro.core import full_analysis

            core = full_analysis({"八字": bazi, "日主": day_master, "性别": gender})
            if core.get("status") != "completed":
                return {"error": "核心分析失败，无法评分"}
            dayun = core.get("dayun", [])
            qiyun_age = core.get("qiyun_age", 5)

            yongshen_info = core.get("yongshen", {})
            if isinstance(yongshen_info, dict):
                yongshen = yongshen or yongshen_info.get("yongshen", "")
                jishen = jishen or yongshen_info.get("jishen", [])
                xishen = xishen or yongshen_info.get("xishen", [])

            if not birth_year:
                solar_str = core.get("阳历", "")
                if solar_str:
                    try:
                        birth_year = int(solar_str.split("-")[0])
                    except (ValueError, IndexError):
                        pass

        if not dayun:
            return {"error": "缺少大运数据"}
        if not yongshen:
            return {"error": "缺少用神数据，无法评分"}
        if not birth_year:
            return {"error": "缺少出生年份，无法计算流年"}

        jishen_list = jishen if isinstance(jishen, list) else ([jishen] if jishen else [])
        xishen_list = xishen if isinstance(xishen, list) else ([xishen] if xishen else [])

        dayun_scores = score_dayun(dayun, yongshen, jishen_list, day_master)
        liunian_scores = score_liunian(
            dayun, yongshen, jishen_list, xishen_list,
            day_master, birth_year, qiyun_age,
        )
        return {
            "dayun_scores": dayun_scores,
            "liunian_scores": liunian_scores,
            "yongshen": yongshen,
            "birth_year": birth_year,
            "qiyun_age": qiyun_age,
        }

    @staticmethod
    def _analyze_bazi_element(
        bazi: str = "",
        birth_date: str = "",
        time_index: int = 12,
        gender: str = "男",
    ) -> dict[str, Any]:
        from bazi_pro.core.elements import calc_element_forces

        if not bazi:
            from bazi_pro.paipan import paipan_from_datetime

            gender_cn = "男" if gender in ("男", "male", "1", "M") else "女"
            paipan_result = paipan_from_datetime(birth_date, gender_cn)
            if paipan_result.get("status") != "completed":
                return {"error": "排盘失败，无法计算五行力量"}
            bazi = paipan_result.get("八字", "")
            if not bazi:
                return {"error": "八字为空"}

        bazi_parts = bazi.split()
        if len(bazi_parts) < 2 or len(bazi_parts[1]) < 2:
            return {"error": f"八字格式错误: {bazi}"}
        month_zhi = bazi_parts[1][1]
        result = calc_element_forces(bazi_parts, month_zhi)
        return result


_adapter_instance: Optional[MCPToolAdapter] = None


def get_adapter() -> MCPToolAdapter:
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = MCPToolAdapter()
    return _adapter_instance


async def call_tool(tool_name: str, **kwargs: Any) -> dict[str, Any]:
    return await get_adapter().call_tool(tool_name, **kwargs)


def call_tool_sync(tool_name: str, **kwargs: Any) -> dict[str, Any]:
    return get_adapter().call(tool_name, **kwargs)
