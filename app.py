import streamlit as st
import pandas as pd

# ==========================================
# 页面基础配置
# ==========================================
# 1. 浏览器标签页标题 (英文通用)
st.set_page_config(
    layout="wide",
    page_title="Dubai EV Charging Investment Model",
    page_icon="🇦🇪"
)

# 2. 页面内部主标题 (中文)
st.title("🇦🇪 迪拜超充站 · 投资财务评估模型")
st.caption("Financial Model & ROI Analysis | 支持配置文件的保存与读取")
st.markdown("---")

# ==========================================
# 第一部分：【赋值型】后台基准配置
# 用于设定市场通用的单价和费率标准
# ==========================================
with st.expander("⚙️ 【后台配置】 (基准单价与费率设定)", expanded=False):
    st.info("👇 数值基于当前市场行情设定作为测算基准。如有供应链变动可在此微调。")
    
    tab1, tab2, tab3 = st.tabs(["🏗️ CAPEX 单价", "🛠️ OPEX 基准", "📉 财务参数"])
    
    with tab1:
        st.markdown("##### 1. 充电设备模型 (源头供应链)")
        c1, c2, c3 = st.columns(3)
        # 默认基准：400kW, 6枪, 16万AED
        pile_power_kw = c1.number_input("设备单台功率 (kW)", value=400, step=20)
        guns_per_pile = c2.number_input("单台配备枪数 (把)", value=6, step=1)
        price_pile_unit = c3.number_input("设备单台价格 (AED/台)", value=160000, step=5000, help="含海运与清关")

        st.markdown("##### 2. 变压器模型 (严格选型)")
        t1, t2 = st.columns(2)
        trans_type_str = t1.selectbox("变电站规格 (kVA)", ["1000 kVA", "1500 kVA"])
        # 严格定价逻辑
        trans_val = 1000 if "1000" in trans_type_str else 1500
        locked_price = 200000 if trans_val == 1000 else 250000
        price_trans_unit = t2.number_input("变电站单价 (AED/台)", value=locked_price, help="含环网柜(RMU)与外壳")

        st.markdown("##### 3. 工程基建 (本地施工)")
        e1, e2, e3 = st.columns(3)
        cost_hv_cable = e1.number_input("高压电缆总成本 (AED)", value=20000)
        cost_lv_cable = e2.number_input("低压电缆总成本 (AED)", value=80000)
        cost_civil_work = e3.number_input("土建施工基础费 (AED/站)", value=150000)
        
        e4, e5, e6 = st.columns(3)
        cost_dewa_conn = e4.number_input("DEWA 接入费 (AED/站)", value=200000)
        cost_canopy = e5.number_input("遮阳棚与品牌 (AED/站)", value=80000)
        cost_design = e6.number_input("顾问与审批费 (AED/站)", value=40000)

        st.markdown("##### 4. 其他投入 (杂项与备用)")
        o1, o2 = st.columns(2)
        other_name_1 = o1.text_input("项目 1 名称", value="前期开办费")
        other_cost_1 = o1.number_input("项目 1 预算 (AED)", value=30000)
        other_name_2 = o2.text_input("项目 2 名称", value="不可预见金")
        other_cost_2 = o2.number_input("项目 2 预算 (AED)", value=20000)

    with tab2:
        o_col1, o_col2 = st.columns(2)
        with o_col1:
            st.markdown("**固定开销**")
            base_rent = st.number_input("基准场地租金 (AED/年)", value=120000, help="若为分成模式可设为0")
            base_admin = st.number_input("基准办公行政 (AED/年)", value=50000)
        with o_col2:
            st.markdown("**维保开销**")
            base_maintenance = st.number_input("基准维护外包 (AED/年)", value=30000)

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
    qty_piles = st.number_input("拟投充电设备 (台)", value=2, step=1)
    qty_trans = st.number_input("拟投变压器 (台)", value=1, step=1)
    
    total_guns = qty_piles * guns_per_pile
    total_pile_power = qty_piles * pile_power_kw
    total_trans_capacity = qty_trans * trans_val
    
    # 容量安全校验
    if total_pile_power > total_trans_capacity:
        st.error(f"⚠️ **容量警告**: 桩总功率 {total_pile_power}kW > 变压器 {total_trans_capacity}kVA")
    else:
        st.caption(f"✅ **配置安全**: 总枪数 {total_guns} | 总功率 {total_pile_power}kW")

with col_in2:
    st.markdown("#### B. 资金与电价")
    interest_rate = st.number_input("资金成本费率 (%)", value=5.0, help="资金占用的年化利息") / 100
    price_sale = st.number_input("销售电价 (AED/kWh)", value=1.20)
    price_cost = st.number_input("进货电价 (AED/kWh)", value=0.44)

with col_in3:
    st.markdown("#### C. 周期设定")
    years_duration = st.number_input("运营测算年限 (年)", value=8, help="不含Year 0建设期")

# 自动计算 CAPEX 总额
capex_equip = (price_pile_unit * qty_piles) + (price_trans_unit * qty_trans)
capex_infra = cost_hv_cable + cost_lv_cable + cost_civil_work + cost_dewa_conn + cost_canopy + cost_design
capex_others = other_cost_1 + other_cost_2
total_capex = capex_equip + capex_infra + capex_others

st.info(f"💰 **Year 0 (建设期) 总投入：{total_capex:,.0f} AED**")

# ==========================================
# 第三部分：年度动态推演 (核心交互区)
# 支持上传之前的配置文件
# ==========================================
st.divider()
st.subheader("2. 年度运营推演 (核心变量表)")

# --- 文件上传区 (用于导入配置) ---
uploaded_file = st.file_uploader("📂 上传之前的配置文件 (CSV)", type=["csv"], help="上传 operation_config.csv 以恢复之前的设置")

# 默认科学评估数据 (爬坡模型)
default_daily_kwh = [80, 200, 300, 350, 400, 400, 400, 400, 400, 400]
default_staff = [2] * 10
default_salary = [150000] * 10

# 数据加载逻辑：优先读取上传文件，否则使用默认值
if uploaded_file is not None:
    try:
        df_input = pd.read_csv(uploaded_file)
        st.success("✅ 配置文件加载成功！")
    except Exception as e:
        st.error(f"❌ 文件读取失败，已回退至默认设置: {e}")
        df_input = pd.DataFrame({
            "年份": [f"Year {i+1}" for i in range(years_duration)],
            "单枪日均充电量 (kWh)": default_daily_kwh[:years_duration],
            "运营人数 (人)": default_staff[:years_duration],
            "人均年薪 (AED)": default_salary[:years_duration]
        })
else:
    # 使用默认数据
    df_input = pd.DataFrame({
        "年份": [f"Year {i+1}" for i in range(years_duration)],
        "单枪日均充电量 (kWh)": default_daily_kwh[:years_duration],
        "运营人数 (人)": default_staff[:years_duration],
        "人均年薪 (AED)": default_salary[:years_duration]
    })

st.caption("请在下方表格直接修改每一年的数据（可直接编辑，也可上传之前的配置）。")
# 可编辑表格
edited_df = st.data_editor(
    df_input,
    column_config={
        "单枪日均充电量 (kWh)": st.column_config.NumberColumn(min_value=0, max_value=1000, step=10, required=True),
        "运营人数 (人)": st.column_config.NumberColumn(min_value=0, step=1),
        "人均年薪 (AED)": st.column_config.NumberColumn(format="%d")
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
    current_fixed = (base_rent + base_admin + base_maintenance) * inflation_factor
    
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

if payback_year:
    m4.metric("⏱️ 动态回本 (含Year 0)", f"{payback_year:.1f} 年", delta="盈利", delta_color="normal")
else:
    m4.metric("⏱️ 动态回本 (含Year 0)", "未回本", delta="风险", delta_color="inverse")

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
    csv_config = edited_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="💾 保存当前运营配置 (Config)",
        data=csv_config,
        file_name='operation_config.csv',
        mime='text/csv',
        help="保存当前的年度流量和人力设置，下次可直接上传此文件恢复。"
    )