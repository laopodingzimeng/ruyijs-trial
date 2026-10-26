"""ruyiJS 冒烟测试：只验证运行时本身可用，不访问任何风控目标站点。"""
import sys
import traceback

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import ruyijs
from ruyijs import Context, JSError

results = []


def check(name, fn):
    try:
        detail = fn()
        results.append((name, True, detail))
        print(f"[PASS] {name} :: {detail}")
    except Exception as error:  # noqa: BLE001
        results.append((name, False, repr(error)))
        print(f"[FAIL] {name} :: {error!r}")
        traceback.print_exc()


def basics():
    with Context(timeout=30) as context:
        context.eval("let count = 40")
        value = context.eval("count += 2")
        assert value == 42, value
        agent = context.eval("navigator.userAgent")
        return f"eval 持久化=42, UA={agent[:60]}..."


def bridge():
    with Context(timeout=30) as context:
        context.set("config", {"offset": 2})
        add = context.eval("(value) => value + config.offset", to_py=False)
        assert add(40) == 42
        context.expose(lambda a, b: a + b, "add")
        assert context.eval("add(20, 22)") == 42
        return "set / eval(to_py=False) / expose 全通"


def fingerprint():
    with Context(timeout=30) as context:
        context.configure_fingerprint({
            "navigator": {"language": "zh-CN", "hardwareConcurrency": 8},
            "screen": {"width": 1920, "height": 1080},
            "viewport": {"width": 1280, "height": 720},
            "locale": {"timezone": "Asia/Shanghai"},
        })
        language, width = context.eval("[navigator.language, screen.width]")
        assert language == "zh-CN" and width == 1920
        return f"language={language}, screen={width}"


def clock():
    with Context(timeout=30) as context:
        context.configure_clock("logical", epoch_ms=1700000000000)
        context.eval("globalThis.result = 0; setTimeout(() => { result = 42 }, 10)")
        context.advance(10)
        value = context.eval("result")
        assert value == 42, value
        return "逻辑时钟驱动 setTimeout OK"


def js_error():
    with Context(timeout=30) as context:
        try:
            context.eval("throw new TypeError('bad input')", filename="demo.js")
        except JSError as error:
            assert error.name == "TypeError"
            return f"JSError({error.name}: {error.message}) 带堆栈 OK"
        raise AssertionError("expected JSError")


def _net_log_tail(context):
    try:
        return str(context.net_log())[:600]
    except Exception as error:  # noqa: BLE001
        return f"<net_log 不可用: {error!r}>"


def network():
    # 真实 Necko 网络栈验证：导航到中性站点 example.com
    with Context(timeout=120) as context:
        context.navigate("https://example.com/")
        text = ""
        for _ in range(8):
            context.advance(2000)
            text = str(context.eval(
                "document.title + '|' + (document.body ? document.body.textContent.slice(0, 100) : '')"
            ))
            if "Example" in text:
                return f"navigate + DOM 解析 OK :: {text[:80]!r}"

        # 回退路径：页面内 fetch
        context.load_page("https://example.com/", "")
        context.eval("globalThis.r = null; fetch('/').then(x => x.text()).then(v => { r = v })")
        context.advance(10000)
        page = str(context.eval("r") or "")
        if "Example" in page:
            return f"页内 fetch OK（navigate 未提交） :: {page[:80]!r}"

        raise AssertionError(
            f"navigate={text!r}, fetch={page[:60]!r}, net_log={_net_log_tail(context)}"
        )


print(f"python: {sys.version.split()[0]}, ruyijs: {getattr(ruyijs, '__version__', 'unknown')}")
check("01 引擎基础 (eval/持久化/navigator)", basics)
check("02 Python<->JS 桥", bridge)
check("03 指纹配置", fingerprint)
check("04 确定性时钟", clock)
check("05 JSError 异常处理", js_error)
check("06 真实网络 (Necko -> example.com)", network)

failed = [name for name, ok, _ in results if not ok]
print()
print(f"total: {len(results)}, passed: {len(results) - len(failed)}, failed: {len(failed)}")
if failed:
    print("failed:", ", ".join(failed))
    sys.exit(1)
print("ALL GREEN")
