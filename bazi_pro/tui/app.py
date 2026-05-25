#!/usr/bin/env python3
"""
bazi-pro 交互式 TUI v5.0
基于 rich 库的终端界面：彩色表格、进度条、面板、Tab 补全
"""

import os

try:
    from rich import box
    from rich.console import Console
    from rich.layout import Layout  # noqa: F401
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax  # noqa: F401
    from rich.table import Table
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False


# 常用查询词（Tab 补全候选）
COMMON_QUERIES = [
    "伤官见官 财星通关", "杀印相生 七杀 印绶", "食神制杀 身弱",
    "从格 假从 从象", "从强 假从 顺势 印比成势", "枭神夺食 食神 偏印",
    "寒木向阳 调候 丙火", "火炎土燥 调候 壬癸", "金寒水冷 无火不发",
    "官杀混杂 去留", "建禄格 透官", "月劫格 透官", "羊刃 官杀制刃",
    "财格 食伤生财", "印格 官生印", "伤官配印",
    "比劫争财 破财", "魁罡 庚戌 戊戌", "阴差阳错 丙子",
    "三合局 申子辰", "天乙贵人 文昌",
]


class BaziTUI:
    """八字命理交互式终端界面"""

    def __init__(self):
        self.console = Console()
        self._corpus_path = ''

    def run(self) -> None:
        """主入口：显示欢迎界面和检索 REPL"""
        if not _RICH_AVAILABLE:
            print("rich 库未安装。请运行: pip install rich")
            print("降级为纯文本模式...")
            self._run_simple()
            return

        self._render_welcome()
        self._repl()

    def _run_simple(self) -> None:
        """纯文本降级模式"""
        print("\nbazi-pro TUI v5.0（纯文本模式）")
        print("输入查询词进行古籍检索，输入 :q 退出\n")
        while True:
            try:
                query = input("检索> ").strip()
                if query in (':q', ':quit', 'exit'):
                    break
                if query:
                    self._do_retrieve(query)
            except (KeyboardInterrupt, EOFError):
                break
        print("再见。")

    def _render_welcome(self) -> None:
        """渲染欢迎界面"""
        self.console.clear()
        title = Panel.fit(
            "[bold gold1]bazi-pro v5.0[/bold gold1]\n"
            "[dim]专业八字命理解读引擎 · 交互式终端界面[/dim]\n"
            "[dim]语料库: 2964 条古籍原文 | 6 部经典 | BM25 + Hybrid Search[/dim]",
            border_style="gold1",
            padding=(1, 3),
        )
        self.console.print(title)

        # 显示常用命令
        cmd_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        cmd_table.add_column("命令", style="cyan")
        cmd_table.add_column("说明", style="dim")
        cmd_table.add_row(":h, :help", "显示帮助信息")
        cmd_table.add_row(":q, :quit", "退出程序")
        cmd_table.add_row(":s, :stats", "显示语料库统计")
        cmd_table.add_row(":d, :doctor", "运行环境诊断")
        cmd_table.add_row(":t, :tab", "显示常用查询词")
        cmd_table.add_row("<查询词>", "执行古籍检索（BM25）")
        self.console.print(Panel(cmd_table, title="命令列表", border_style="blue"))
        self.console.print()

    def _repl(self) -> None:
        """交互式检索 REPL"""
        import readline

        # 注册 Tab 补全
        def completer(text, state):
            matches = [q for q in COMMON_QUERIES if q.startswith(text)]
            if state < len(matches):
                return matches[state]
            return None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

        while True:
            try:
                query = self.console.input("[bold cyan]检索>[/bold cyan] ").strip()
                if not query:
                    continue
                if query in (':q', ':quit', 'exit'):
                    break
                if query in (':h', ':help'):
                    self._render_welcome()
                elif query in (':s', ':stats'):
                    self._show_stats()
                elif query in (':d', ':doctor'):
                    self._run_doctor()
                elif query in (':t', ':tab'):
                    self._show_queries()
                else:
                    self._do_retrieve(query)
            except (KeyboardInterrupt, EOFError):
                break

        self.console.print("\n[dim]再见。[/dim]")

    def _show_stats(self) -> None:
        """显示语料库统计"""
        try:
            corpus = self._resolve_corpus()
            from bazi_pro.retrieve_classical import load_corpus
            entries = load_corpus(corpus)

            table = Table(title="语料库统计", box=box.ROUNDED)
            table.add_column("指标", style="cyan")
            table.add_column("数值", style="green")
            table.add_row("总条数", str(len(entries)))

            # 按出处统计
            sources = {}
            for e in entries:
                src = e.get('source', '未知')
                sources[src] = sources.get(src, 0) + 1
            for src, count in sorted(sources.items(), key=lambda x: -x[1]):
                table.add_row(f"  {src}", str(count))

            self.console.print(table)
        except Exception as e:
            self.console.print(f"[red]统计失败: {e}[/red]")

    def _run_doctor(self) -> None:
        """运行环境诊断"""
        self.console.print("[dim]运行环境诊断...[/dim]")
        try:
            from bazi_pro.doctor import main
            main()
        except Exception as e:
            self.console.print(f"[red]诊断失败: {e}[/red]")

    def _show_queries(self) -> None:
        """显示常用查询词"""
        table = Table(title="常用查询词", box=box.SIMPLE)
        table.add_column("#", style="dim")
        table.add_column("查询词", style="green")
        for i, q in enumerate(COMMON_QUERIES, 1):
            table.add_row(str(i), q)
        self.console.print(table)

    def _do_retrieve(self, query: str) -> None:
        """执行古籍检索并美化输出"""
        corpus = self._resolve_corpus()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(f"[cyan]检索中: {query[:30]}...", total=None)

            try:
                from bazi_pro.retrieve_classical import retrieve
                result = retrieve(corpus, query, k=5)
            except Exception as e:
                progress.stop()
                self.console.print(f"[red]检索失败: {e}[/red]")
                return

            progress.update(task, completed=True)

        mode = result.get('mode', 'unknown')
        latency = result.get('latency_ms', 0)
        results = result.get('results', [])

        if not results:
            self.console.print("[yellow]未找到匹配的古籍条文[/yellow]")
            return

        # 结果表格
        table = Table(
            title=f"检索结果 — {mode} ({latency}ms)",
            box=box.ROUNDED,
            show_lines=True,
        )
        table.add_column("得分", style="green", width=8)
        table.add_column("ID", style="dim", width=14)
        table.add_column("出处", style="gold1", width=12)
        table.add_column("主题", style="cyan", width=8)
        table.add_column("内容", style="white", max_width=60)

        for r in results:
            table.add_row(
                f"{r['score']:.1f}",
                r['id'],
                r.get('source', ''),
                r.get('topic', ''),
                r['content'][:80] + ('...' if len(r.get('content', '')) > 80 else ''),
            )

        self.console.print(table)

    def _resolve_corpus(self) -> str:
        """解析语料库路径"""
        if self._corpus_path:
            return self._corpus_path

        candidates = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'references', 'classical_corpus.md'),
            os.path.join(os.path.expanduser('~'), '.hermes', 'skills', 'bazi-pro', 'references', 'classical_corpus.md'),
        ]
        for p in candidates:
            if os.path.exists(p):
                self._corpus_path = os.path.abspath(p)
                return self._corpus_path

        return ''


def main():
    app = BaziTUI()
    app.run()


if __name__ == '__main__':
    main()
