import streamlit as st
import pandas as pd
import io

# ==========================================
# 0. 全局样式注入与页面配置 (UI核心优化)
# ==========================================
st.set_page_config(
    layout="wide",
    page_title="迪拜新能源超充投资模型 V9.0 Pro",
    page_icon="🇦🇪",
    initial_sidebar_state="collapsed"
)

# --- 自定义 CSS 注入 ---
# 目的：打造专业头部、优化指标卡片显示、适配移动端字体
st.markdown("""
    <style>
    /* 1. 头部横幅样式 */
    .main-header-container {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem 1rem;
        border-radius: 0 0 15px 15px;
        color: white;
        text-align: center;
        margin-top: -4rem; /* 抵消 Streamlit 默认顶部留白 */
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title {
        font-size: 2.2rem; font-weight: 800; margin: 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .sub-title {
        font-size: 1rem; opacity: 0.9; margin-top: 0.5rem; font-weight: 300;
    }

    /* 2. 指标卡片优化 (让 Metric 看起来更酷) */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #0056b3 !important; /* 使用深蓝色强调数字 */
        font-weight: 700 !important;
    }

    /* 3. 移动端适配微调 */
    @media (max-width: 640px) {
        .main-title { font-size: 1.6rem; }
        /* 在手机上强制输入框占满宽度，避免挤压 */
        [data-testid="stNumberInput"] input { width: 100%; }
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 安全验证模块 (Gatekeeper) - 保持不变
# ==========================================
ADMIN_PASSWORD = "DbeVc"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]:
        return
    st.markdown("# 🔒 访问受限")
    st.markdown("该财务模型包含敏感商业数据，请输入授权密码以继续访问。")
    st.markdown("---")
    with st.form("login_form"):
        password_input = st.text_input("请输入访问密码", type="password", placeholder="在此输入密码...")
        submit_button = st.form_submit_button("验证登录", type="primary", use_container_width=True)
        if submit_button:
            if password_input == ADMIN_PASSWORD:
                st.session_state["authenticated"] = True
                st.toast("验证成功，正在加载数据...", icon="✅")
                st.rerun()
            else:
                st.error("❌ 密码错误，请核对后重试。")
    st.stop()
check_password()

# ==========================================
# 主界面开始
# ==========================================

# --- 使用自定义 HTML 头部替代原有 st.title ---
st.markdown("""
    <div class="main-header-container">
        <div class="main-title">🇦🇪 迪拜新能源超充站 · 投资测算模型 (V9.0 Pro)</div>
        <div class="sub-title">Financial Model & ROI Analysis | 专业版 UI | 移动端适配优化</div>
    </div>
""", unsafe_allow_html=True)


# ==========================================
# 配置导入区 (使用卡片式容器包裹，视觉更整洁)
# ==========================================
with st.container(border=True):
    col_load1, col_load2 = st.columns([3, 1])
    with col_load1:
        st.write("📂 **导入历史配置** (Load Configuration)")
        st.caption("上传之前的 'operation_config.csv' 文件以快速恢复表格设置。")
    with col_load2:
        uploaded_config = st.file_uploader("上传之前的配置文件 (CSV)", type=["csv"], label_visibility="collapsed")
    
    if uploaded_config is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_config)
            required_columns = ["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]
            if all(col in df_uploaded.columns for col in required_columns):
                st.session_state['df_config_cache'] = df_uploaded
                st.toast("✅ 配置文件已加载，将在表格中生效。", icon="📂")
            else:
                st.error(f"❌ 格式错误，缺少必要列。")
                st.session_state.pop('df_config_cache', None)
        except Exception as e:
            st.error(f"❌ 文件读取失败：{e}")
            st.session_state.pop('df_config_cache', None)

# ==========================================
# 第一部分：后台基准配置 (重构布局以适应移动端)
# ==========================================
st.write("") # 添加一点间距
with st.expander("⚙️ **后台基准配置** (点击展开/收起)", expanded=False):
    st.caption("👇 以下数值基于 12 车位旗舰站基准设定。供应链变动可在此微调。")
    
    # 使用更专业的图标
    tab1, tab2, tab3 = st.tabs(["🏗️ CAPEX 明细 (基建)", "🛠️ OPEX 基准 (运营)", "📉 财务参数 (税务/通胀)"])
    
    # --- CAPEX Tab 重构：使用 Container 分组，减少手机端的列挤压 ---
    with tab1:
        # Group 1: 核心设备
        with st.container(border=True):
            st.markdown("**1. 核心设备与电力设施 (Equipment & Power)**")
            # 手机上会自动堆叠，电脑上显示2列
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                pile_power_kw = st.number_input("超充主机单台功率 (kW)", value=480, step=20)
                guns_per_pile = st.number_input("单台主机配备枪数 (把)", value=6, step=1)
                price_pile_unit = st.number_input("超充主机单价 (AED/台)", value=200000, step=5000, help="含2液冷+4风冷")
            with c_col2:
                trans_type_str = st.selectbox("专用箱式变电站规格", ["1000 kVA (含RMU)", "1500 kVA (含RMU)"])
                trans_val = 1000 if "1000" in trans_type_str else 1500
                locked_price = 200000 if trans_val == 1000 else 250000
                price_trans_unit = st.number_input("变电站单价 (AED/台)", value=locked_price, help="含环网柜(RMU)")

        # Group 2: 电力接入与基建 (合并为一组，移动端体验更好)
        with st.container(border=True):
             st.markdown("**2. 电力接入与土建工程 (Connection & Civil Work)**")
             ce_col1, ce_col2 = st.columns(2)
             with ce_col1:
                 cost_dewa_conn = st.number_input("DEWA 电力接入费 (AED/站)", value=200000)
                 cost_hv_cable = st.number_input("高压电缆总成本 (AED)", value=20000)
                 cost_lv_cable = st.number_input("低压电缆总成本 (AED)", value=80000)
             with ce_col2:
                 cost_civil_work = st.number_input("场地土建施工费 (AED/站)", value=150000)
                 cost_canopy = st.number_input("高端遮阳棚与品牌 (AED/站)", value=80000)
                 cost_design = st.number_input("设计与顾问费 (AED/站)", value=40000)

        # Group 3: 弱电与杂项
        with st.container(border=True):
            st.markdown("**3. 弱电系统与杂项 (Weak Current & Others)**")
            w_col1, w_col2, w_col3 = st.columns(3)
            cost_cctv = w_col1.number_input("视频监控 (CCTV)", value=25000)
            cost_locks = w_col2.number_input("智能地锁系统", value=30000)
            cost_network = w_col3.number_input("站内网络与布线", value=15000)
            cost_weak_current_total = cost_cctv + cost_locks + cost_network
            
            st.divider()
            o_col1, o_col2 = st.columns(2)
            other_cost_1 = o_col1.number_input("前期开办费 (AED)", value=30000)
            other_cost_2 = o_col2.number_input("不可预见金 (AED)", value=20000)

    with tab2:
        with st.container(border=True):
            st.markdown("### 年度固定运营投入 (Fixed OPEX)")
            st.caption("注：人力成本已移至前台表格动态配置。")
            o_col1, o_col2 = st.columns(2)
            with o_col1:
                st.markdown("🏣 **固定开销**")
                base_rent = st.number_input("场地车位租金 (AED/年)", value=96000, help="若为分成模式可设为0")
                base_it_saas = st.number_input("IT维护及SaaS开发 (AED/年)", value=50000)
            with o_col2:
                st.markdown("🛠️ **维保与营销**")
                base_marketing = st.number_input("广告及营销投入 (AED/年)", value=50000)
                base_maintenance = st.number_input("基准维护外包 (AED/年)", value=30000)

    with tab3:
        with st.container(border=True):
            st.markdown("### 高阶财务参数 (Parameters)")
            f1, f2, f3 = st.columns(3)
            power_efficiency = f1.number_input("⚡ 电能效率 (%)", value=95.0, step=0.5) / 100
            inflation_rate = f2.number_input("📈 OPEX 通胀率 (%)", value=3.0, step=0.5) / 100
            tax_rate = f3.number_input("🏛️ 企业所得税率 (%)", value=9.0, step=1.0) / 100
            tax_threshold = 375000 # UAE免税额度

# ==========================================
# 第二部分：前台项目输入 (使用带标题的容器强调)
# ==========================================
st.header("1. 项目规模与周期设定 (Project Scale)")

# 使用容器包裹，增加视觉整体感
with st.container(border=True):
    col_in1, col_in2, col_in3 = st.columns(3)

    with col_in1:
        st.markdown("##### A. 设备数量")
        qty_piles = st.number_input("拟投超充主机 (台)", value=2, step=1)
        qty_trans = st.number_input("拟投变压器 (台)", value=1, step=1)
        
        total_guns = qty_piles * guns_per_pile
        total_pile_power = qty_piles * pile_power_kw
        total_trans_capacity = qty_trans * trans_val
        
        if total_pile_power > total_trans_capacity:
            st.error(f"⚠️ 容量不足: {total_pile_power}kW > {total_trans_capacity}kVA")
        else:
            st.success(f"✅ 配置确认: {total_guns}枪 | 总功率 {total_pile_power}kW")

    with col_in2:
        st.markdown("##### B. 资金与电价")
        interest_rate = st.number_input("资金成本费率 (%)", value=5.0) / 100
        price_sale = st.number_input("销售电价 (AED/kWh)", value=1.20)
        price_cost = st.number_input("进货电价 (AED/kWh)", value=0.44)

    with col_in3:
        st.markdown("##### C. 周期设定")
        years_duration = st.number_input("运营测算年限 (年)", value=5)

# CAPEX 计算与展示
capex_equip = (price_pile_unit * qty_piles) + (price_trans_unit * qty_trans)
capex_power_infra = cost_dewa_conn + cost_hv_cable + cost_lv_cable
capex_civil = cost_civil_work + cost_canopy + cost_design
capex_others = other_cost_1 + other_cost_2
total_capex = capex_equip + capex_power_infra + capex_civil + cost_weak_current_total + capex_others

# 使用 Info 样式展示关键数据
st.info(f"💰 **Year 0 (建设期) 总投入预估：{total_capex:,.0f} AED** (含全套设备、基建、弱电及杂项)")

# ==========================================
# 第三部分：年度动态推演 (核心变量表)
# ==========================================
st.header("2. 年度运营推演核心表 (Dynamic Table)")
st.markdown("✍️ **请直接编辑下表**修改每年的“单枪日充电量”和“人力配置”。")

# --- 配置数据准备 ---
default_daily_kwh = [50, 100, 150, 200, 250, 300, 300, 300, 300, 300]
default_staff = [2] * 10
default_salary = [75000] * 10
df_input = None

if st.session_state.get('df_config_cache') is not None:
    df_uploaded = st.session_state['df_config_cache']
    if len(df_uploaded) < years_duration:
        extra_years = years_duration - len(df_uploaded)
        df_extra = pd.DataFrame({
            "单枪日均充电量 (kWh)": default_daily_kwh[len(df_uploaded):years_duration],
            "运营人数 (人)": default_staff[len(df_uploaded):years_duration],
            "人均年薪 (AED)": default_salary[len(df_uploaded):years_duration]
        })
        df_input = pd.concat([df_uploaded, df_extra], ignore_index=True)
    else:
        df_input = df_uploaded.head(years_duration)
else:
    df_input = pd.DataFrame({
        "单枪日均充电量 (kWh)": default_daily_kwh[:years_duration],
        "运营人数 (人)": default_staff[:years_duration],
        "人均年薪 (AED)": default_salary[:years_duration]
    })

df_input["年份"] = [f"Y{i+1}" for i in range(years_duration)] # 简化年份显示，适合手机
df_input = df_input[["年份", "单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]]

# 可编辑表格 (保持宽度拉伸)
edited_df = st.data_editor(
    df_input,
    column_config={
        "年份": st.column_config.TextColumn(disabled=True, width="small"),
        "单枪日均充电量 (kWh)": st.column_config.NumberColumn(min_value=0, max_value=1000, step=10, required=True, format="%d kWh"),
        "运营人数 (人)": st.column_config.NumberColumn(min_value=0, step=1, help="建议：1维护+1营销", format="%d 人"),
        "人均年薪 (AED)": st.column_config.NumberColumn(format="%d AED")
    },
    hide_index=True,
    use_container_width=True, # 关键：确保手机上表格撑满容器
    height=int(35 * (years_duration + 1) if years_duration < 10 else 400) # 动态高度优化
)

# ==========================================
# 第四部分：核心计算引擎 (保持不变，逻辑无需修改)
# ==========================================
results = []
results.append({
    "年份": "Y0", "营收": 0, "成本": 0, "税前净利": 0, "税金": 0, "税后净利": 0,
    "自由现金流": -total_capex, "累计现金流": -total_capex
})
cumulative_cash = -total_capex
payback_year = None

for index, row in edited_df.iterrows():
    year_idx = index
    daily_kwh = row["单枪日均充电量 (kWh)"]
    staff_count = row["运营人数 (人)"]
    salary_avg = row["人均年薪 (AED)"]
    
    annual_sales_kwh = daily_kwh * total_guns * 365
    revenue = annual_sales_kwh * price_sale
    annual_buy_kwh = annual_sales_kwh / power_efficiency
    cost_power = annual_buy_kwh * price_cost
    inflation_factor = (1 + inflation_rate) ** year_idx
    current_labor = (staff_count * salary_avg) * inflation_factor
    current_fixed = (base_rent + base_it_saas + base_marketing + base_maintenance) * inflation_factor
    cost_finance = total_capex * interest_rate
    total_opex = cost_power + current_labor + current_fixed + cost_finance
    pre_tax_profit = revenue - total_opex
    tax_amount = 0
    if pre_tax_profit > tax_threshold:
        tax_amount = (pre_tax_profit - tax_threshold) * tax_rate
    net_profit = pre_tax_profit - tax_amount
    cumulative_cash += net_profit
    if payback_year is None and cumulative_cash >= 0:
        prev_cash = results[-1]["累计现金流"]
        if net_profit > 0:
             payback_year = (year_idx) + (abs(prev_cash) / net_profit)
        else:
             payback_year = year_idx + 1

    results.append({
        "年份": f"Y{year_idx + 1}",
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
# 第五部分：报表输出 (UI 重点优化)
# ==========================================
st.header("📊 财务评估结果 (Financial Report)")

# --- 核心指标卡片 (使用 CSS 增强后的效果) ---
# 布局优化：在手机上自动折行显示为 2x2
m1, m2 = st.columns(2)
with m1:
    st.metric("💰 初始总投资 (CAPEX)", f"{total_capex:,.0f} AED", help="建设期总投入")
with m2:
    st.metric("💸 运营期总净利 (税后)", f"{df_res['税后净利'].sum():,.0f} AED", help="测算期内累计净利润")

m3, m4 = st.columns(2)
with m3:
    st.metric("📉 总资金成本 (利息)", f"{df_res['资金成本'].sum():,.0f} AED", help="测算期内财务费用总计")
with m4:
    if payback_year and payback_year <= years_duration + 1:
        st.metric("⏱️ 动态回本期 (Payback)", f"{payback_year:.1f} 年", delta="已回本", delta_color="normal")
    else:
        st.metric("⏱️ 动态回本期 (Payback)", "未回本", delta="周期外", delta_color="inverse", help="超出测算年限")

st.write("") # 留白

# J曲线图与表格 Tab化，手机上浏览更方便
tab_chart, tab_table = st.tabs(["📈 累计现金流曲线 (J-Curve)", "📄 详细现金流表 (Cash Flow)"])

with tab_chart:
    st.area_chart(df_res.set_index("年份")["累计现金流"], color="#2a5298", use_container_width=True)

with tab_table:
    st.dataframe(
        df_res.style.format("{:,.0f}", subset=["营收", "成本", "税前净利", "税金", "税后净利", "自由现金流", "累计现金流", "资金成本"]),
        use_container_width=True,
        height=400
    )

# ==========================================
# 下载区域 (使用容器包裹，底部统一)
# ==========================================
st.divider()
with st.container(border=True):
    st.write("📥 **数据存取中心 (Data Center)**")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        csv_report = df_res.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📄 下载财务评估报告 (.csv)",
            data=csv_report,
            file_name='dubai_financial_report_v9.csv',
            mime='text/csv',
            use_container_width=True # 按钮撑满宽度，手机更好点
        )

    with col_dl2:
        csv_config = edited_df[["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]].to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="💾 保存当前运营配置 (.csv)",
            data=csv_config,
            file_name='operation_config_v9.csv',
            mime='text/csv',
            use_container_width=True # 按钮撑满宽度
        )