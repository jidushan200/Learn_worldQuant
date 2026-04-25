import json
import os
import sys
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from auth_client import create_authenticated_session
from simulate import submit_and_wait
from evaluate import get_alpha_result
from logger import log_start, log_result, log_end
from generate_web import generate_web
from prompt_utils import grade_ge
from setting import (
    ALPHAS_FILE, SIMULATION_SETTINGS,
    MAX_WAIT_SEC, SESSION_REFRESH_INTERVAL, MAX_CONCURRENT,
    MAX_ITERATIONS, TARGET_SHARPE, TARGET_FITNESS, TARGET_GRADE,
)

_thread_local = threading.local()


# ═══════════════════════════════════════════════════════════
#  Alpha 比较（基于回测返回的 grade / sharpe / fitness）
# ═══════════════════════════════════════════════════════════

def _is_better(a: dict, b: dict) -> bool:
    """a 是否严格优于 b，比较顺序: grade > sharpe > fitness"""
    gr_a = a.get("grade", "")
    gr_b = b.get("grade", "")
    a_ge_b = grade_ge(gr_a, gr_b)
    b_ge_a = grade_ge(gr_b, gr_a)
    if a_ge_b and not b_ge_a:
        return True
    if b_ge_a and not a_ge_b:
        return False
    sh_a = a.get("sharpe", 0) or 0
    sh_b = b.get("sharpe", 0) or 0
    if sh_a != sh_b:
        return sh_a > sh_b
    fi_a = a.get("fitness", 0) or 0
    fi_b = b.get("fitness", 0) or 0
    return fi_a > fi_b


def _find_best(results: list[dict]) -> dict | None:
    valid = [r for r in results if r.get("alpha_id")]
    if not valid:
        return None
    best = valid[0]
    for r in valid[1:]:
        if _is_better(r, best):
            best = r
    return best


# ═══════════════════════════════════════════════════════════
#  Alpha 列表构建
# ═══════════════════════════════════════════════════════════

def _build_alpha_list(alphas: list[dict]) -> list[dict]:
    alpha_list = []
    for item in alphas:
        name = item["name"]
        expr = item["expr"]
        custom = item.get("setting", {})
        settings = {**SIMULATION_SETTINGS, **custom}
        payload = {
            "type": "REGULAR",
            "settings": settings,
            "regular": expr,
        }
        alpha_list.append({"field_id": name, "payload": payload})
    return alpha_list


# ═══════════════════════════════════════════════════════════
#  Session 管理（线程级）
# ═══════════════════════════════════════════════════════════

def _get_session(max_retries: int = 3, retry_delay: float = 5.0):
    need_new = (
        not hasattr(_thread_local, "sess")
        or _thread_local.sess is None
        or time.time() - _thread_local.session_start > SESSION_REFRESH_INTERVAL
    )
    if need_new:
        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                sess, status = create_authenticated_session()
                _thread_local.sess = sess
                _thread_local.session_start = time.time()
                print(f"  🔑 [线程 {threading.current_thread().name}] 认证成功: {status}")
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(
                    f"  ⚠️  [线程 {threading.current_thread().name}] "
                    f"认证失败 (第 {attempt}/{max_retries} 次): {e}"
                )
                if attempt < max_retries:
                    time.sleep(retry_delay)
        if last_err:
            raise last_err
    return _thread_local.sess


# ═══════════════════════════════════════════════════════════
#  单个 Alpha 处理
# ═══════════════════════════════════════════════════════════

def _process_one(item: dict, index: int, total: int) -> dict:
    field_id = item["field_id"]
    payload = item["payload"]
    expr = payload["regular"]
    settings = payload["settings"]

    try:
        sess = _get_session()
    except Exception as e:
        err = f"认证失败: {e}"
        log_result(index, total, None, field_id, expr, settings, None, err)
        return {"alpha_id": None, "field_id": field_id, "expr": expr, "error": err}

    alpha_id, err, _ = submit_and_wait(
        sess=sess, alpha_payload=payload, max_wait_sec=MAX_WAIT_SEC
    )
    if err:
        log_result(index, total, None, field_id, expr, settings, None, err)
        return {"alpha_id": None, "field_id": field_id, "expr": expr, "error": err}

    result, err = get_alpha_result(sess=sess, alpha_id=alpha_id)
    if err:
        log_result(index, total, alpha_id, field_id, expr, settings, None, err)
        return {"alpha_id": alpha_id, "field_id": field_id, "expr": expr, "error": err}

    log_result(index, total, alpha_id, field_id, expr, settings, result, None)
    result["field_id"] = field_id
    result["expr"] = expr
    result["settings_used"] = settings
    return result


# ═══════════════════════════════════════════════════════════
#  批量回测
# ═══════════════════════════════════════════════════════════

def run_simulation(alpha_list: list[dict]) -> list[dict]:
    total = len(alpha_list)
    log_start(total)

    all_results = []
    results_lock = threading.Lock()

    with ThreadPoolExecutor(
        max_workers=MAX_CONCURRENT,
        thread_name_prefix="sim",
    ) as executor:
        futures = {
            executor.submit(_process_one, item, i, total): i
            for i, item in enumerate(alpha_list, 1)
        }
        for future in as_completed(futures):
            result = future.result()
            with results_lock:
                all_results.append(result)

    succeeded = sum(1 for r in all_results if r.get("alpha_id"))
    log_end(total, succeeded)
    return all_results


# ═══════════════════════════════════════════════════════════
#  打印全局最佳 Alpha 详情（数据全部来自回测 response）
# ═══════════════════════════════════════════════════════════

def _print_best_alpha(best: dict, improved: bool):
    sh = best.get("sharpe", 0) or 0
    fi = best.get("fitness", 0) or 0
    to = best.get("turnover", 0) or 0
    rt = best.get("returns", 0) or 0
    dd = best.get("drawdown", 0) or 0
    gr = best.get("grade", "N/A")
    chk = best.get("checks_pass", "N/A")
    name = best.get("field_id", "?")
    expr = best.get("expr", "?")
    stg = best.get("settings_used", {})

    gap_sh = TARGET_SHARPE - sh
    gap_fi = TARGET_FITNESS - fi

    tag = "🆕 本轮刷新!" if improved else "📌 沿用上轮最优"

    print(f"\n  {'─' * 56}")
    print(f"  📊 全局最佳 Alpha — {tag}")
    print(f"  {'─' * 56}")
    print(f"  名称      : {name}")
    print(f"  表达式    : {expr}")
    print(f"  Grade     : {gr}  (目标 >= {TARGET_GRADE})"
          f"{'  ✅ 达标' if grade_ge(gr, TARGET_GRADE) else '  ❌ 未达标'}")
    print(f"  Sharpe    : {sh:.4f}  (目标 >= {TARGET_SHARPE})"
          f"{'  ✅' if sh >= TARGET_SHARPE else f'  ❌ 差 {gap_sh:.4f}'}")
    print(f"  Fitness   : {fi:.4f}  (目标 >= {TARGET_FITNESS})"
          f"{'  ✅' if fi >= TARGET_FITNESS else f'  ❌ 差 {gap_fi:.4f}'}")
    print(f"  Turnover  : {to:.4f}"
          f"{'  ⚠️ 偏高' if to > 0.7 else ''}"
          f"{'  ⚠️ 偏低' if 0 < to < 0.01 else ''}")
    print(f"  Returns   : {rt * 100:.2f}%")
    print(f"  Drawdown  : {dd * 100:.2f}%")
    print(f"  Checks    : {'✅ 全部通过' if chk is True else f'❌ {chk}'}")
    print(f"  Setting   : decay={stg.get('decay', '?')}, "
          f"neut={stg.get('neutralization', '?')}, "
          f"univ={stg.get('universe', '?')}")

    yearly = best.get("yearly_stats")
    if yearly:
        neg = [y for y in yearly if (y.get("sharpe", 0) or 0) < 0]
        weak = [y for y in yearly if 0 <= (y.get("sharpe", 0) or 0) < 0.5]
        if neg:
            print(f"  年度风险  : 🔴 {len(neg)} 年负Sharpe "
                  f"({', '.join(str(y.get('year', '?')) for y in neg)})")
        if weak:
            print(f"              🟡 {len(weak)} 年弱Sharpe(0~0.5) "
                  f"({', '.join(str(y.get('year', '?')) for y in weak)})")
        if not neg and not weak:
            print(f"  年度稳定性: ✅ 所有年份 Sharpe >= 0.5")
    else:
        print(f"  年度数据  : ⚠️ 未获取到")

    print(f"  {'─' * 56}")
    print(f"  —— 未达标，继续下一轮 ...\n")


# ═══════════════════════════════════════════════════════════
#  AI 链式递归优化
# ═══════════════════════════════════════════════════════════

def _run_auto():
    from ai_client import chat
    from prompt_utils import load_initial_idea
    from prompt_builder import build_initial_prompt, build_iteration_prompt
    from alpha_parser import parse_alphas_from_response

    idea = load_initial_idea()
    if not idea:
        print("❌ 请在 strategy_prompt.txt 中写入你的策略思路后再运行")
        return

    print(f"  📝 策略思路已加载 ({len(idea)} 字符)")
    print(f"  🎯 目标: Grade >= {TARGET_GRADE}, "
          f"Sharpe >= {TARGET_SHARPE}, Fitness >= {TARGET_FITNESS}")
    print(f"  🔁 最多 {MAX_ITERATIONS} 轮\n")

    iter_dir = os.path.join("iterations", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(iter_dir, exist_ok=True)

    best_alpha: dict | None = None
    last_results: list[dict] | None = None
    no_improve_count = 0

    for iteration in range(1, MAX_ITERATIONS + 1):

        print(f"\n{'=' * 60}")
        print(f"  🔄  第 {iteration} / {MAX_ITERATIONS} 轮迭代")
        print(f"{'=' * 60}\n")

        # ── 1. 构建 prompt ──
        if iteration == 1:
            sys_p, user_p = build_initial_prompt(idea)
        else:
            sys_p, user_p = build_iteration_prompt(
                idea, iteration, best_alpha, last_results,
                no_improve_count=no_improve_count,
            )

        prompt_path = os.path.join(iter_dir, f"iter{iteration}_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(f"=== SYSTEM ===\n{sys_p}\n\n=== USER ===\n{user_p}")

        # ── 2. 调用 AI ──
        print("  🤖 正在调用 AI 生成 alpha ...")
        try:
            response = chat(sys_p, user_p)
        except Exception as e:
            print(f"  ❌ AI 调用彻底失败: {e}")
            break

        resp_path = os.path.join(iter_dir, f"iter{iteration}_response.txt")
        with open(resp_path, "w", encoding="utf-8") as f:
            f.write(response)
        print(f"  ✅ AI 响应: {len(response)} 字符")

        # ── 3. 解析 alpha ──
        alphas = None
        try:
            alphas = parse_alphas_from_response(response)
        except ValueError:
            print("  ⚠️  首次解析失败，要求 AI 重新输出 JSON ...")
            retry_msg = (
                "你上次的输出无法被解析为有效 JSON 数组。\n"
                "请 **只** 输出一个 JSON 数组，格式如下，不要包含任何其他文字：\n"
                '```json\n[{"name": "...", "expr": "...", "setting": {...}}]\n```'
            )
            try:
                response2 = chat("", retry_msg)
                retry_path = os.path.join(
                    iter_dir, f"iter{iteration}_response_retry.txt"
                )
                with open(retry_path, "w", encoding="utf-8") as f:
                    f.write(response2)
                alphas = parse_alphas_from_response(response2)
            except Exception as e2:
                print(f"  ❌ 重试后仍失败: {e2}")
                break

        if not alphas:
            print("  ❌ 未能获取到任何 alpha，终止")
            break

        print(f"  ✅ 解析得到 {len(alphas)} 个 alpha")

        alphas_path = os.path.join(iter_dir, f"iter{iteration}_alphas.json")
        with open(alphas_path, "w", encoding="utf-8") as f:
            json.dump(alphas, f, ensure_ascii=False, indent=2)

        with open(ALPHAS_FILE, "w", encoding="utf-8") as f:
            json.dump(alphas, f, ensure_ascii=False, indent=2)

        # ── 4. 回测 ──
        alpha_list = _build_alpha_list(alphas)
        print(f"\n  ▶ 开始回测 {len(alpha_list)} 个 alpha ...\n")
        results = run_simulation(alpha_list)

        # ── 5. 保存结果 ──
        results_path = os.path.join(iter_dir, f"iter{iteration}_results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        # ── 6. 更新链式状态 ──
        last_results = results

        round_best = _find_best(results)
        improved = False
        if round_best and (best_alpha is None or _is_better(round_best, best_alpha)):
            best_alpha = round_best
            improved = True
            no_improve_count = 0
            print("  🏆 发现新的全局最优 alpha!")

            best_path = os.path.join(iter_dir, "best_alpha.json")
            with open(best_path, "w", encoding="utf-8") as f:
                json.dump(best_alpha, f, ensure_ascii=False, indent=2, default=str)
        else:
            no_improve_count += 1

        # ── 7. 是否达标 ──
        if best_alpha and grade_ge(best_alpha.get("grade", ""), TARGET_GRADE):
            print(f"\n  🎉🎉🎉 达标！Grade = {best_alpha['grade']}")
            print(f"  最终表达式: {best_alpha.get('expr')}")
            print(f"  Sharpe={best_alpha.get('sharpe')}, "
                  f"Fitness={best_alpha.get('fitness')}")
            generate_web(best_alpha)
            break
        else:
            if best_alpha:
                _print_best_alpha(best_alpha, improved)
            else:
                print("  ⚠️ 本轮无有效结果，继续下一轮 ...")

    else:
        print(f"\n  ⏹ 已达最大轮次 {MAX_ITERATIONS}，未能达标")
        if best_alpha:
            print(f"  最终最优: Grade={best_alpha.get('grade')}, "
                  f"Sharpe={best_alpha.get('sharpe'):.4f}, "
                  f"Expr={best_alpha.get('expr')}")


# ═══════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"

    if mode == "auto":
        _run_auto()
    elif mode == "manual":
        with open(ALPHAS_FILE, "r", encoding="utf-8") as f:
            alphas = json.load(f)
        alpha_list = _build_alpha_list(alphas)
        results = run_simulation(alpha_list)
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    else:
        print(f"未知模式: {mode}，可用: auto / manual")


if __name__ == "__main__":
    main()