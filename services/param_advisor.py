"""参数推荐服务 — 根据场景推荐MMC/柔直系统参数。"""

SCENARIOS = {
    "low_voltage": {
        "name": "低压配电研究场景",
        "description": "适合初学入门、快速仿真验证控制策略",
        "params": {
            "直流电压": "±10kV（极间20kV）",
            "交流电压": "110kV / 10.5kV（变压器变比）",
            "额定容量": "5-10 MW",
            "子模块数N": "10-20级/桥臂",
            "子模块电容Csm": "3-5 mF",
            "桥臂电感Larm": "5-10 mH",
            "A站控制": "定Udc=20kV + 定Q=0",
            "B站控制": "定P=5MW + 定Q=0",
            "直流线路电阻": "0.003 Ω",
            "直流线路电感": "0.02 mH",
            "母线电容": "5 mF",
            "仿真步长": "100 μs",
            "建议仿真时间": "5-10 s",
            "预计仿真耗时": "1-5 分钟",
        },
    },
    "medium_voltage": {
        "name": "中压园区配电场景",
        "description": "对标成都天府国际生物城±10kV直流配电园区",
        "params": {
            "直流电压": "±10kV（极间20kV）",
            "交流电压": "110kV / 10kV",
            "额定容量": "10-50 MW",
            "子模块数N": "20-40级/桥臂",
            "子模块电容Csm": "2-4 mF",
            "桥臂电感Larm": "3-8 mH",
            "A站控制": "定Udc + 定Q",
            "B站控制": "定P + 定Q",
            "电缆型号": "2×400mm² 铜芯XLPE",
            "最大输送电流": "2.2 kA",
            "储能配置": "1.5-2.0h，磷酸铁锂",
            "仿真步长": "50-100 μs",
            "建议仿真时间": "10-20 s",
        },
    },
    "high_voltage": {
        "name": "高压输电场景（甘孜光伏基地）",
        "description": "对标甘孜±150kV/850MW全光伏基地直流送出工程",
        "params": {
            "直流电压": "±150kV（极间300kV）",
            "交流电压": "500kV / 150kV",
            "额定容量": "850 MW",
            "子模块数N": "72级/桥臂（36全桥+36半桥）",
            "子模块电容Csm": "1260 μF",
            "桥臂电感Larm": "0.156 H (156 mH)",
            "额定电流": "2.83 kA",
            "A站控制": "定Udc=300kV + 定Q",
            "B站控制": "定P=850MW + 定Q",
            "输出THD": "<0.21%",
            "一级升压DC/DC": "2MW, 1500V/±20kV, IPOS",
            "二级升压": "250MW, ±20kV/±150kV",
            "储能配置": "20-30%装机，4h容量型",
            "仿真步长": "50-100 μs",
            "建议仿真时间": "20 s",
            "预计仿真耗时": "30-120 分钟",
        },
    },
    "custom": {
        "name": "自定义场景",
        "description": "根据用户输入的电压等级和容量自动计算推荐参数",
        "params": {},
    },
}


def get_scenarios() -> list[dict]:
    """获取所有预设场景列表。"""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in SCENARIOS.items()
        if k != "custom"
    ]


def get_params(scenario_id: str) -> dict | None:
    """获取指定场景的推荐参数。"""
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return None
    return {"name": scenario["name"], "description": scenario["description"], "params": scenario["params"]}


def calculate_custom_params(udc_kv: float, capacity_mw: float) -> dict:
    """根据直流电压和容量计算推荐参数。"""
    # 额定电流
    i_rated = capacity_mw * 1e3 / (2 * udc_kv)  # kA

    # 子模块数（每个子模块约4-5kV耐压）
    n_sm = max(10, int(udc_kv / 4))

    # 子模块电容电压
    uc0 = 2 * udc_kv / n_sm  # kV

    # 子模块电容（按5%纹波率计算）
    # Csm = 2*S / (N * omega * Uc0^2 * epsilon)
    omega = 2 * 3.14159 * 50
    epsilon = 0.05
    csm_f = 2 * capacity_mw * 1e6 / (n_sm * omega * (uc0 * 1e3) ** 2 * epsilon)
    csm_mf = csm_f * 1e3  # mF

    # 桥臂电感（取0.1 p.u.）
    z_base = (udc_kv * 1e3) ** 2 / (capacity_mw * 1e6)
    larm = 0.1 * z_base / omega
    larm_mh = larm * 1e3

    return {
        "name": f"自定义场景（±{udc_kv}kV / {capacity_mw}MW）",
        "description": "根据输入参数自动计算",
        "params": {
            "直流电压": f"±{udc_kv}kV（极间{2*udc_kv}kV）",
            "额定容量": f"{capacity_mw} MW",
            "额定电流": f"{i_rated:.2f} kA",
            "子模块数N": f"{n_sm}级/桥臂",
            "子模块电容电压Uc0": f"{uc0:.1f} kV",
            "子模块电容Csm": f"{csm_mf:.2f} mF",
            "桥臂电感Larm": f"{larm_mh:.1f} mH",
            "A站控制": f"定Udc={2*udc_kv}kV + 定Q=0",
            "B站控制": f"定P={capacity_mw}MW + 定Q=0",
            "仿真步长": "100 μs" if n_sm <= 20 else "50 μs",
        },
    }
