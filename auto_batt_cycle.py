import subprocess
import re
import time
import sys

# --- 配置参数 ---
CHARGE_UPPER_LIMIT = 80  # 当电量达到或超过此值时，停止充电并开始放电
DISCHARGE_LOWER_LIMIT = 20 # 当电量低于或等于此值时，开始充电

CHECK_INTERVAL_SECONDS = 60  # 每隔多久检查一次电量 (建议 1 分钟左右)
BATT_COMMAND = "batt"      # batt 命令的路径，如果 batt 不在你的 PATH 中，请修改为完整路径

# 正则表达式用于匹配 "Current charge: XX%" 并提取百分比
CHARGE_PERCENTAGE_PATTERN = re.compile(r"Current charge:\s*(\d+)%")
# 正则表达式用于匹配 "State: XXX" 并提取电池状态 (charging, discharging, not charging)
BATTERY_STATE_PATTERN = re.compile(r"State:\s*(charging|discharging|not charging)")

# 脚本内部状态管理：'charging' 或 'discharging' 或 'initial' （初始化状态）
# 这表示脚本当前希望电池处于什么状态
current_script_policy = "initial" 

def run_batt_command(args):
    """通用函数，用于执行 batt 命令。"""
    try:
        cmd = [BATT_COMMAND] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # 不自动抛出异常，以便我们自己处理错误输出
        )
        if result.returncode != 0:
            print(f"[{time.ctime()}] ❌ 命令 '{' '.join(cmd)}' 失败。")
            print(f"Stderr: {result.stderr.strip()}")
            return None, False
        
        # batt 的状态输出通常在 stderr，其他命令成功输出在 stdout
        output = result.stderr if 'status' in args else result.stdout 
        return output, True
    except FileNotFoundError:
        print(f"[{time.ctime()}] ❌ 错误：命令 '{BATT_COMMAND}' 未找到。请检查 batt 是否已安装且在 PATH 中。")
        return None, False
    except Exception as e:
        print(f"[{time.ctime()}] ❌ 发生未知错误执行 '{' '.join(cmd)}'：{e}")
        return None, False

def get_current_batt_info():
    """
    获取当前电池电量和电池的实际充电/放电/不充电状态。
    返回 (current_percentage, battery_state)
    battery_state 会是 "charging", "discharging", "not charging" 之一。
    如果获取失败，返回 (None, None)
    """
    output, success = run_batt_command(["status"])
    if not success or not output:
        return None, None

    current_percentage = None
    battery_state = None

    charge_match = CHARGE_PERCENTAGE_PATTERN.search(output)
    if charge_match:
        current_percentage = int(charge_match.group(1))

    state_match = BATTERY_STATE_PATTERN.search(output)
    if state_match:
        battery_state = state_match.group(1).lower()

    return current_percentage, battery_state

def set_batt_charging_mode(enable_charging: bool, limit_percentage: int):
    """
    根据目标设置 batt 的充电模式。
    enable_charging: True 为开启充电，False 为关闭。
    limit_percentage: 充电上限，0-100。
    """
    success_limit = True
    success_adapter = True

    # 1. 设置充电上限
    if limit_percentage == 100:
        print(f"[{time.ctime()}] ➡️ 设置 batt 限制为 100% (禁用内部限制)。")
        _, success_limit = run_batt_command(["limit", "100"])
    elif limit_percentage > 0 and limit_percentage < 100:
        print(f"[{time.ctime()}] ➡️ 设置 batt 限制为 {limit_percentage}%。")
        _, success_limit = run_batt_command(["limit", str(limit_percentage)])
    else:
        print(f"[{time.ctime()}] ⚠️ 无效的限制百分比: {limit_percentage}")
        success_limit = False

    # 2. 控制电源适配器
    if enable_charging:
        print(f"[{time.ctime()}] 🔌 开启电源适配器。")
        _, success_adapter = run_batt_command(["adapter", "enable"])
    else:
        print(f"[{time.ctime()}] ⚡ 切断电源适配器（强制放电）。")
        _, success_adapter = run_batt_command(["adapter", "disable"])
    
    return success_limit and success_adapter

def main():
    global current_script_policy # 声明要修改全局变量

    print("--- batt 自动充放电循环管理脚本启动 ---")
    print(f"充电上限 (停止充电并开始放电): {CHARGE_UPPER_LIMIT}%")
    print(f"放电下限 (开始充电): {DISCHARGE_LOWER_LIMIT}%")
    print(f"检查间隔: {CHECK_INTERVAL_SECONDS} 秒")
    print("---------------------------------------")

    if CHARGE_UPPER_LIMIT <= DISCHARGE_LOWER_LIMIT:
        print(f"[{time.ctime()}] ❌ 配置错误: 充电上限 ({CHARGE_UPPER_LIMIT}%) 必须高于放电下限 ({DISCHARGE_LOWER_LIMIT}%)。请检查配置！")
        sys.exit(1)

    while True:
        current_charge, battery_state = get_current_batt_info()

        if current_charge is None or battery_state is None:
            print(f"[{time.ctime()}] 无法获取电池信息，等待下次检查...")
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        print(f"[{time.ctime()}] 电量: {current_charge}%, 实际状态: {battery_state}, 脚本策略: {current_script_policy}")

        # --- 决策逻辑 ---

        # 1. 初始化脚本策略
        if current_script_policy == "initial":
            if current_charge <= DISCHARGE_LOWER_LIMIT:
                print(f"[{time.ctime()}] 💡 初始状态，电量 {current_charge}% 低于放电下限 {DISCHARGE_LOWER_LIMIT}%。")
                set_batt_charging_mode(True, CHARGE_UPPER_LIMIT)
                current_script_policy = "charging"
            elif current_charge >= CHARGE_UPPER_LIMIT:
                print(f"[{time.ctime()}] 💡 初始状态，电量 {current_charge}% 高于充电上限 {CHARGE_UPPER_LIMIT}%。")
                set_batt_charging_mode(False, 100) # 强制放电，极限设为100以免batt内部干预
                current_script_policy = "discharging"
            else: # 在上下限之间，根据当前实际状态决定
                if battery_state == "charging":
                    print(f"[{time.ctime()}] 💡 初始状态，电量 {current_charge}% 在范围内，且正在充电。策略设为充电。")
                    set_batt_charging_mode(True, CHARGE_UPPER_LIMIT)
                    current_script_policy = "charging"
                else: # discharging 或 not charging
                    print(f"[{time.ctime()}] 💡 初始状态，电量 {current_charge}% 在范围内，且未在充电。策略设为放电。")
                    set_batt_charging_mode(False, 100)
                    current_script_policy = "discharging"
            # 无论如何，首次决策后跳过本次循环的后续检查，等待下次循环
            time.sleep(CHECK_INTERVAL_SECONDS) 
            continue

        # 2. 策略为“充电”时
        if current_script_policy == "charging":
            if current_charge >= CHARGE_UPPER_LIMIT:
                print(f"[{time.ctime()}] 🎯 达到充电上限 {CHARGE_UPPER_LIMIT}%。切换到放电策略。")
                set_batt_charging_mode(False, 100) # 强制放电，极限设为100以免batt内部干预
                current_script_policy = "discharging"
            elif battery_state != "charging": # 确保仍然在充电
                 # 如果我们想充电，但实际没有在充，说明 batt limit 可能生效了(在上限附近)
                 # 或者适配器被断开了 (虽然脚本期望连接)，再次确认指令
                print(f"[{time.ctime()}] 🔄 策略为充电，但实际未充电。再次确认指令。")
                set_batt_charging_mode(True, CHARGE_UPPER_LIMIT)
            else:
                print(f"[{time.ctime()}] 👍 策略为充电，正在按计划充电中。")

        # 3. 策略为“放电”时
        elif current_script_policy == "discharging":
            if current_charge <= DISCHARGE_LOWER_LIMIT:
                print(f"[{time.ctime()}] 🔋 达到放电下限 {DISCHARGE_LOWER_LIMIT}%。切换到充电策略。")
                set_batt_charging_mode(True, CHARGE_UPPER_LIMIT)
                current_script_policy = "charging"
            elif battery_state == "charging": # 如果我们想放电，但实际在充电，说明适配器被启用了，再次确认指令
                print(f"[{time.ctime()}] 🔄 策略为放电，但实际在充电。再次确认指令。")
                set_batt_charging_mode(False, 100)
            else:
                print(f"[{time.ctime()}] 👍 策略为放电，正在按计划放电中。")

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n[{time.ctime()}] 脚本已接收到中断信号，正在退出。")
        sys.exit(0)
    except Exception as e:
        print(f"[{time.ctime()}] 脚本异常退出: {e}")
        sys.exit(1)
