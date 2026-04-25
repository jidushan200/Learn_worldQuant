import json
import os
import time
import threading
from prompt_builder import grade_ge
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from auth_client import create_authenticated_session
from simulate import submit_and_wait
from evaluate import get_alpha_result
from logger import log_start, log_result, log_end
from generate_web import generate_web
from setting import (
    ALPHAS_FILE, SIMULATION_SETTINGS,
    MAX_WAIT_SEC, SESSION_REFRESH_INTERVAL, MAX_CONCURRENT,
    MAX_ITERATIONS, TARGET_SHARPE, TARGET_FITNESS, TARGET_GRADE,
    JUDGE_ENABLED,
)

_thread_local = threading.local()


# ═══════════════════════════════════════════════════════════
#  Alpha 列表构建
# ═══════════════════════════════════════════════════════════

def _build_alpha_list(alphas: list[dict]) -> list[dict]:
    alpha_list = []
    for item in alphas:
        name     = item["name"]
        expr     = item["expr"]
        custom   = item.get("setting", {})
        settings = {**SIMULATION_SETTINGS, **custom}
        payload  = {
            "type":     "REGULAR",
            "settings": settings,
            "regular":  expr,
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
                _thread_local.sess          = sess
                _thread_local.session_start = time.time()
                print(f"  🔑 [线程 {threading.current_thread().name}] 认证成功: {status}")
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(f"  ⚠️  [线程 {threading.current_thread().name}] "
                      f"认证失败 (第 {attempt}/{max_retries} 次): {e}")
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
    payload  = item["payload"]
    expr     = payload["regular"]
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
    result["field_id"]      = field_id
    result["expr"]          = expr
    result["settings_used"] = settings
    return result


# ═══════════════════════════════════════════════════════════
#  批量回测
# ═══════════════════════════════════════════════════════════

def run_simulation(alpha_list: list[dict]) -> list[dict]:
    total = len(alpha_list)
    log_start(total)

    all_results  = []
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
#  达标判断
# ═══════════════════════════════════════════════════════════

def _target_reached(results: list[dict]) -> bool:
    for r in results:
        gr = r.get("grade", "")
        if grade_ge(gr, TARGET_GRADE):
            return True
    return False

# ═══════════════════════════════════════════════════════════
#  AI 研判
# ═══════════════════════════════════════════════════════════

def _run_judge(results: list[dict]) -> list[dict]:
    if not JUDGE_ENABLED:
        return results

    from ai_client import judge

    for r in results:
        if r.get("error") or r.get("alpha_id") is None:
            r["judge"] = {"verdict": "SKIP", "comment": "回测失败，跳过研判"}
            continue

        try:
            metrics = {
                "name":        r.get("field_id"),
                "expr":        r.get("expr"),
                "sharpe":      r.get("sharpe"),
                "fitness":     r.get("fitness"),
                "turnover":    r.get("turnover"),
                "returns":     r.get("returns"),
                "drawdown":    r.get("drawdown"),
                "grade":       r.get("grade"),
                "checks_pass": r.get("checks_pass"),
            }
            j = judge(json.dumps(metrics, ensure_ascii=False, indent=2))
            r["judge"] = j
            tag = "✅" if j["verdict"] == "PASS" else "❌"
            print(f"  {tag} 研判 {r.get('field_id', '?')}: {j['verdict']}")
        except Exception as e:
            r["judge"] = {"verdict": "ERROR", "comment": str(e)}
            print(f"  ⚠️  研判异常 {r.get('field_id', '?')}: {e}")

    return results


# ═══════════════════════════════════════════════════════════
#  AI 递归优化
# ═══════════════════════════════════════════════════════════

def _run_auto():
    from ai_client import chat
    from prompt_builder import load_initial_idea, build_initial_prompt, build_iteration_prompt
    from alpha_parser import parse_alphas_from_response

    idea = load_initial_idea()
    if not idea:
        print("❌ 请在 strategy_prompt.txt 中写入你的策略思路后再运行")
        return

    print(f"  📝 策略思路已加载 ({len(idea)} 字符)")
    print(f"  🎯 目标: Sharpe >= {TARGET_SHARPE}, Fitness >= {TARGET_FITNESS}")
    print(f"  🔁 最多 {MAX_ITERATIONS} 轮")
    print(f"  🧠 AI 研判: {'开启' if JUDGE_ENABLED else '关闭'}\n")

    iter_dir = os.path.join("iterations", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(iter_dir, exist_ok=True)

    history: list[dict] = []

    for iteration in range(1, MAX_ITERATIONS + 1):

        print(f"\n{'=' * 60}")
        print(f"  🔄  第 {iteration} / {MAX_ITERATIONS} 轮迭代")
        print(f"{'=' * 60}\n")

        # ── 1. 构建 prompt ───────────────────────────────
        if iteration == 1:
            sys_p, user_p = build_initial_prompt(idea)
        else:
            sys_p, user_p = build_iteration_prompt(idea, iteration, history)

        prompt_path = os.path.join(iter_dir, f"iter{iteration}_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(f"=== SYSTEM ===\n{sys_p}\n\n=== USER ===\n{user_p}")

        # ── 2. 调用 AI ──────────────────────────────────
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

        # ── 3. 解析 alpha ────────────────────────────────
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
                with open(os.path.join(iter_dir, f"iter{iteration}_response_retry.txt"),
                          "w", encoding="utf-8") as f:
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

        # ── 4. 回测 ─────────────────────────────────────
        alpha_list = _build_alpha_list(alphas)
        print(f"\n  ▶ 开始回测 {len(alpha_list)} 个 alpha ...\n")
        results = run_simulation(alpha_list)

        # ── 5. AI 研判 ──────────────────────────────────
        if JUDGE_ENABLED:
            print(f"\n  🧠 AI 研判中 ...")
            results = _run_judge(results)

        with open(os.path.join(iter_dir, f"iter{iteration}_results.json"),
                  "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        # ── 6. 更新历史 ─────────────────────────────────
        history.append({"iteration": iteration, "results": results})

        # ── 7. 是否达标 ─────────────────────────────────
        if _target_reached(results):
            hit = [
                r for r in results
                if grade_ge(r.get("grade", ""), TARGET_GRADE)
            ]
            for h in hit:
                print(
                    f"\n  🎉 第 {iteration} 轮 [{h.get('field_id')}] "
                    f"Grade={h.get('grade')} 达标！"
                    f"（Sharpe={h.get('sharpe')}, Fitness={h.get('fitness')}）"
                )
            break

        ok = [
            r for r in results
            if isinstance(r.get("sharpe"), (int, float)) and not r.get("error")
        ]
        if ok:
            best = max(ok, key=lambda x: x["sharpe"])
            print(
                f"\n  📊 本轮最佳: Sharpe={best['sharpe']:.4f}  "
                f"Fitness={best.get('fitness', 'N/A')}  —— 未达标，继续 ..."
            )
        else:
            print("\n  📊 本轮无成功 alpha，继续 ...")

    # ── 最终汇总 ─────────────────────────────────────────
    generate_web()

    all_ok = [
        r for h in history for r in h["results"]
        if isinstance(r.get("sharpe"), (int, float)) and not r.get("error")
    ]
    print(f"\n{'=' * 60}")
    print(f"  📋 递归优化完成 — 共 {len(history)} 轮")
    if all_ok:
        best = max(all_ok, key=lambda x: x["sharpe"])
        print(
            f"  🏆 全局最佳: Sharpe={best['sharpe']:.4f}  "
            f"Fitness={best.get('fitness', 'N/A')}  "
            f"({best.get('field_id', '?')})"
        )
    print(f"  📂 中间产物: {iter_dir}")
    print(f"{'=' * 60}\n")


# ═══════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════

def main():
    _run_auto()


if __name__ == "__main__":
    main()