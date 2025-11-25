import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. 页面基础配置 (必须是第一个 st 命令)
# ==========================================
st.set_page_config(layout="wide", page_title="迪拜超充投资模型 V8.2 - 受保护", page_icon="🔒")

# ==========================================
# 2. 🔐 安全验证模块 (Gatekeeper)
# 这段代码会拦截未授权访问，只有密码正确才会继续向下执行
# ==========================================

# 设定访问密码
ADMIN_PASSWORD = "DbeVc"

# 初始化 session state 用于记录登录状态
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    """检查用户是否已登录，未登录则显示登录界面并停止执行后续代码"""
    # 如果用户已经通过验证，直接返回，允许执行后面的代码
    if st.session_state["authenticated"]:
        return

    # --- 尚未登录，显示登录界面 ---
    st.markdown("# 🔒 访问受限")
    st.markdown("该财务模型包含敏感商业数据，请输入授权密码以继续访问。")
    st.markdown("---")

    # 使用表单，支持回车键提交
    with st.form("login_form"):
        password_input = st.text_input("请输入访问密码", type="password", placeholder="在此输入密码...")
        submit_button = st.form_submit_button("验证登录", type="primary")

        if submit_button:
            if password_input == ADMIN_PASSWORD:
                # 密码正确
                st.session_state["authenticated"] = True
                st.toast("验证成功，正在加载数据...", icon="✅")
                # 重新运行脚本以立即进入主界面
                st.rerun()
            else:
                # 密码错误
                st.error("❌ 密码错误，请核对后重试。")

    # 【关键】如果未通过验证，在这里停止执行脚本
    # 后面的所有主界面代码都不会被渲染
    st.stop()

# 执行安全检查
check_password()

# ==========================================
# 3. 主应用程序界面 (只有通过验证才会执行到这里)
# ==========================================

st.title("🇦🇪 迪拜新能源超充站 · 投资回报测算模型 (V8.2)")
st.caption("Financial Model & ROI Analysis | 集成完整CAPEX及含租金OPEX结构 | 支持配置保存与导入")
st.markdown("---")

# ==========================================
# 配置导入区
# ==========================================
with st.expander("📂 导入历史配置 (Load Configuration)", expanded=False):
    uploaded_config = st.file_uploader(
        "上传之前的配置文件 (CSV)", 
        type=["csv"], 
        help="上传之前保存的 'operation_config.csv' 文件以恢复设置。"
    )
    if uploaded_config is not None:
        # 立即尝试读取并验证文件
        try:
            df_uploaded = pd.read_csv(uploaded_config)
            required_columns = ["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]
            # 简单的校验：确保包含必要的列
            if all(col in df_uploaded.columns for col in required_columns):
                st.session_state['df_config_cache'] = df_uploaded
                st.success("✅ 配置文件验证成功！将在下方表格中使用。")
            else:
                st.error(f"❌ 配置文件格式不正确。缺少必要的列: {set(required_columns) - set(df_uploaded.columns)}。将使用默认设置。")
                st.session_state.pop('df_config_cache', None) # 清除可能的无效缓存
        except Exception as e:
            st.error(f"❌ 文件读取失败：{e}。将使用默认设置。")
            st.session_state.pop('df_config_cache', None) # 清除可能的无效缓存


# ==========================================
# 第一部分：【赋值型】后台基准配置
# 用于设定市场通用的单价和费率标准
# ==========================================
with st.expander("⚙️ 【后台配置】 (基准单价与费率设定)", expanded=False):
    st.info("👇 以下数值基于最新讨论的 12 车位旗舰站配置设定作为测算基准。如有供应链变动可在此微调。")
    
    tab1, tab2, tab3 = st.tabs(["🏗️ CAPEX 明细", "🛠️ OPEX 基准", "📉 财务参数"])
    
    with tab1:
        st.markdown("##### 1. 核心设备与电力设施")
        c1, c2, c3 = st.columns(3)
        # 默认基准：480kW, 6枪, 20万AED
        pile_power_kw = c1.number_input("超充主机单台功率 (kW)", value=480, step=20, help="支持一拖六")
        guns_per_pile = c2.number_input("单台主机配备枪数 (把)", value=6, step=1)
        price_pile_unit = c3.number_input("超充主机单价 (AED/台)", value=200000, step=5000, help="一拖六 (含2液冷枪+4风冷枪)")

        st.markdown("##### 2. 变电站模型 (严格选型)")
        t1, t2 = st.columns(2)
        trans_type_str = t1.selectbox("专用箱式变电站规格", ["1000 kVA (含RMU)", "1500 kVA (含RMU)"])
        # 严格定价逻辑
        trans_val = 1000 if "1000" in trans_type_str else 1500
        locked_price = 200000 if trans_val == 1000 else 250000
        price_trans_unit = t2.number_input("变电站单价 (AED/台)", value=locked_price, help="含环网柜(RMU)与外壳，已更新为最新报价")

        st.markdown("##### 3. 电力接入与配套")
        e1, e2, e3 = st.columns(3)
        cost_dewa_conn = e1.number_input("DEWA 电力接入费 (AED/站)", value=200000, help="按约1000kW需量预估")
        cost_hv_cable = e2.number_input("高压电缆总成本 (AED)", value=20000)
        cost_lv_cable = e3.number_input("低压电缆总成本 (AED)", value=80000)

        st.markdown("##### 4. 土建与工程施工")
        c_e1, c_e2, c_e3 = st.columns(3)
        cost_civil_work = c_e1.number_input("场地土建施工费 (AED/站)", value=150000)
        cost_canopy = c_e2.number_input("高端遮阳棚与品牌 (AED/站)", value=80000, help="12车位标准")
        cost_design = c_e3.number_input("设计与顾问费 (AED/站)", value=40000, help="含审批咨询")

        st.markdown("##### 5. 弱电智能化系统")
        w1, w2, w3 = st.columns(3)
        cost_cctv = w1.number_input("视频监控系统 (CCTV) (AED)", value=25000)
        cost_locks = w2.number_input("智能地锁系统 (AED)", value=30000)
        cost_network = w3.number_input("站内网络与布线 (AED)", value=15000)
        cost_weak_current_total = cost_cctv + cost_locks + cost_network

        st.markdown("##### 6. 前期与杂项")
        o1, o2 = st.columns(2)
        other_name_1 = o1.text_input("项目 1 名称", value="前期开办费")
        other_cost_1 = o1.number_input("项目 1 预算 (AED)", value=30000)
        other_name_2 = o2.text_input("项目 2 名称", value="不可预见金")
        other_cost_2 = o2.number_input("项目 2 预算 (AED)", value=20000)

    with tab2:
        st.markdown("### 年度固定运营投入 (Fixed OPEX)")
        o_col1, o_col2 = st.columns(2)
        with o_col1:
            st.markdown("**固定开销**")
            base_rent = st.number_input("场地车位租金 (AED/年)", value=96000, help="12车位 x 8000 AED/年 预估，若为分成模式可设为0")
            base_it_saas = st.number_input("IT维护及SaaS开发 (AED/年)", value=50000, help="固定技术投入")
        with o_col2:
            st.markdown("**维保与营销**")
            base_marketing = st.number_input("广告及营销投入 (AED/年)", value=50000, help="固定市场投入")
            base_maintenance = st.number_input("基准维护外包 (AED/年)", value=30000)
            st.caption("注：人力成本已移至前台表格配置。")

    with tab3:
        st.markdown("**高阶财务参数**")
        f1, f2, f3 = st.columns(3)
        # 核心隐性成本参数
        power_efficiency = f1.number_input("⚡ 电能效率 (%)", value=95.0, step=0.5) / 100
        inflation_rate = f2.number_input("📈 OPEX 通胀率 (%)", value=3.0, step=0.5) / 100
        tax_rate = f3.number_input("🏛️ 企业所得税率 (%)", value=9.0, step=1.0) / 100
        tax_threshold = 375000 # UAE免税额度

# ==========================================
# 第二部分：【变量型】前台项目输入
# 用于针对具体项目的规模和周期进行设定
# ==========================================
st.subheader("1. 项目规模与资金设定 (Project Scale)")

col_in1, col_in2, col_in3 = st.columns(3)

with col_in1:
    st.markdown("#### A. 设备数量")
    qty_piles = st.number_input("拟投超充主机 (台)", value=2, step=1, help="默认2台以支持12枪")
    qty_trans = st.number_input("拟投变压器 (台)", value=1, step=1)
    
    total_guns = qty_piles * guns_per_pile
    total_pile_power = qty_piles * pile_power_kw
    total_trans_capacity = qty_trans * trans_val
    
    # 容量安全校验
    if total_pile_power > total_trans_capacity:
        st.error(f"⚠️ **容量警告**: 桩总功率 {total_pile_power}kW > 变压器 {total_trans_capacity}kVA")
    else:
        st.caption(f"✅ **配置安全**: 总枪数 {total_guns} | 总功率 {total_pile_power}kW | 变压器 {total_trans_capacity}kVA")

with col_in2:
    st.markdown("#### B. 资金与电价")
    interest_rate = st.number_input("资金成本费率 (%)", value=5.0, help="资金占用的年化利息") / 100
    price_sale = st.number_input("销售电价 (AED/kWh)", value=1.20)
    price_cost = st.number_input("进货电价 (AED/kWh)", value=0.44)

with col_in3:
    st.markdown("#### C. 周期设定")
    years_duration = st.number_input("运营测算年限 (年)", value=5, help="不含Year 0建设期")

# 自动计算 CAPEX 总额
capex_equip = (price_pile_unit * qty_piles) + (price_trans_unit * qty_trans)
capex_power_infra = cost_dewa_conn + cost_hv_cable + cost_lv_cable
capex_civil = cost_civil_work + cost_canopy + cost_design
capex_others = other_cost_1 + other_cost_2
total_capex = capex_equip + capex_power_infra + capex_civil + cost_weak_current_total + capex_others

st.info(f"💰 **Year 0 (建设期) 总投入：{total_capex:,.0f} AED** (含全套设备、基建、弱电及杂项)")

# ==========================================
# 第三部分：年度动态推演 (含导入逻辑)
# 支持上传之前的配置文件
# ==========================================
st.divider()
st.subheader("2. 年度运营推演 (核心变量表)")

st.caption("请在下方表格修改每一年的**单枪日充电量**和**人力配置**（可直接编辑，也可在上方导入之前的配置）。")

# --- 配置数据准备逻辑 ---
# 默认值 (爬坡模型)
default_daily_kwh = [50, 100, 150, 200, 250, 300, 300, 300, 300, 300]
default_staff = [2] * 10
default_salary = [75000] * 10

# 初始化 df_input
df_input = None

# 检查是否有缓存的有效配置
if st.session_state.get('df_config_cache') is not None:
    df_uploaded = st.session_state['df_config_cache']
    # 如果上传的数据行数少于当前设置的年数，用默认值填充
    if len(df_uploaded) < years_duration:
        extra_years = years_duration - len(df_uploaded)
        df_extra = pd.DataFrame({
            "单枪日均充电量 (kWh)": default_daily_kwh[len(df_uploaded):years_duration],
            "运营人数 (人)": default_staff[len(df_uploaded):years_duration],
            "人均年薪 (AED)": default_salary[len(df_uploaded):years_duration]
        })
        df_input = pd.concat([df_uploaded, df_extra], ignore_index=True)
    else:
        # 截取需要的年数
        df_input = df_uploaded.head(years_duration)
    
    st.toast("已应用导入的配置数据。", icon="✅")
    
else:
    # 使用默认值构建
    df_input = pd.DataFrame({
        "单枪日均充电量 (kWh)": default_daily_kwh[:years_duration],
        "运营人数 (人)": default_staff[:years_duration],
        "人均年薪 (AED)": default_salary[:years_duration]
    })

# 重新生成年份列，确保格式统一并放在第一列
df_input["年份"] = [f"Year {i+1}" for i in range(years_duration)]
df_input = df_input[["年份", "单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]]


# 可编辑表格
edited_df = st.data_editor(
    df_input,
    column_config={
        "年份": st.column_config.TextColumn(disabled=True), # 年份不可编辑
        "单枪日均充电量 (kWh)": st.column_config.NumberColumn(min_value=0, max_value=1000, step=10, required=True),
        "运营人数 (人)": st.column_config.NumberColumn(min_value=0, step=1, help="建议配置：1现场维护 + 1营销推广"),
        "人均年薪 (AED)": st.column_config.NumberColumn(format="%d", help="基准年薪：75,000 AED")
    },
    hide_index=True,
    use_container_width=True
)

# ==========================================
# 第四部分：核心计算引擎
# ==========================================
results = []

# 初始化 Year 0 (建设期)
results.append({
    "年份": "Year 0",
    "营收": 0, "成本": 0, "税前净利": 0, "税金": 0, "税后净利": 0,
    "自由现金流": -total_capex,
    "累计现金流": -total_capex
})

cumulative_cash = -total_capex
payback_year = None

# 年度迭代计算
for index, row in edited_df.iterrows():
    year_idx = index
    
    # 获取当前年度变量
    daily_kwh = row["单枪日均充电量 (kWh)"]
    staff_count = row["运营人数 (人)"]
    salary_avg = row["人均年薪 (AED)"]
    
    # 1. 收入计算
    annual_sales_kwh = daily_kwh * total_guns * 365
    revenue = annual_sales_kwh * price_sale
    
    # 2. 支出计算
    # A. 电费 (含效率损耗)
    annual_buy_kwh = annual_sales_kwh / power_efficiency
    cost_power = annual_buy_kwh * price_cost
    
    # B. 运营费 (含通胀)
    inflation_factor = (1 + inflation_rate) ** year_idx
    current_labor = (staff_count * salary_avg) * inflation_factor
    # 固定OPEX包含：租金 + IT/SaaS + 营销 + 维保
    current_fixed = (base_rent + base_it_saas + base_marketing + base_maintenance) * inflation_factor
    
    # C. 资金成本 (固定利息)
    cost_finance = total_capex * interest_rate
    
    total_opex = cost_power + current_labor + current_fixed + cost_finance
    
    # 3. 利润与税 (UAE 企业所得税逻辑)
    pre_tax_profit = revenue - total_opex
    
    tax_amount = 0
    if pre_tax_profit > tax_threshold:
        tax_amount = (pre_tax_profit - tax_threshold) * tax_rate
        
    net_profit = pre_tax_profit - tax_amount
    
    # 4. 现金流累积
    cumulative_cash += net_profit
    
    # 回本计算 (线性插值)
    if payback_year is None and cumulative_cash >= 0:
        prev_cash = results[-1]["累计现金流"]
        # 防止除以零的极端情况
        if net_profit > 0:
             payback_year = (year_idx) + (abs(prev_cash) / net_profit)
        else:
             payback_year = year_idx + 1 # 刚好回本或仍在微亏

    results.append({
        "年份": f"Year {year_idx + 1}",
        "营收": revenue,
        "成本": total_opex,
        "税前净利": pre_tax_profit,
        "税金": tax_amount,
        "税后净利": net_profit,
        "自由现金流": net_profit,
        "累计现金流": cumulative_cash,
        "资金成本": cost_finance
    })

df_res = pd.DataFrame(results)

# ==========================================
# 第五部分：报表输出与数据下载
# ==========================================
st.divider()
st.subheader("📊 财务评估报告 (Report)")

# 关键指标卡片
m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 初始总投资 (CAPEX)", f"{total_capex:,.0f}")
m2.metric("💸 运营期总净利 (税后)", f"{df_res['税后净利'].sum():,.0f}")
m3.metric("📉 总资金成本", f"{df_res['资金成本'].sum():,.0f}")

if payback_year and payback_year <= years_duration + 1:
    m4.metric("⏱️ 动态回本 (含Year 0)", f"{payback_year:.1f} 年", delta="盈利", delta_color="normal")
else:
    m4.metric("⏱️ 动态回本 (含Year 0)", "未回本或超出测算期", delta="风险", delta_color="inverse")

# 详细表格展示
st.markdown("#### 💰 现金流明细表 (AED)")
st.dataframe(
    df_res.style.format("{:,.0f}", subset=["营收", "成本", "税前净利", "税金", "税后净利", "自由现金流", "累计现金流", "资金成本"]),
    use_container_width=True
)

# J曲线图
st.markdown("#### 📈 累计现金流曲线 (J-Curve)")
st.line_chart(df_res.set_index("年份")["累计现金流"])

# ==========================================
# 下载区域
# ==========================================
st.markdown("---")
st.subheader("📥 数据存取中心")

col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    # 导出财务报表
    csv_report = df_res.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下载财务评估报告 (Result)",
        data=csv_report,
        file_name='dubai_financial_report.csv',
        mime='text/csv',
        help="下载详细的财务测算结果表格"
    )

with col_dl2:
    # 导出当前配置 (用于下次导入)
    # 只保存可编辑的列，不保存 "年份" 列，以便导入时灵活适应不同的年份设置
    csv_config = edited_df[["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]].to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="💾 保存当前运营配置 (Config)",
        data=csv_config,
        file_name='operation_config.csv',
        mime='text/csv',
        help="保存当前的年度流量和人力设置，下次可直接上传此文件恢复。"
    )