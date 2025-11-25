import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

# ==========================================
# 1. 配置与常量层 (Configuration & Constants)
# ==========================================
PAGE_CONFIG = {
    "layout": "wide",
    "page_title": "迪拜新能源超充投资模型 V9.5 Pro",
    "page_icon": "🇦🇪",
    "initial_sidebar_state": "collapsed"
}

ADMIN_PASSWORD = "DbeVc"

# 默认年度推演参数
DEFAULT_PARAMS = {
    "daily_kwh": [50, 100, 150, 200, 250, 300, 300, 300, 300, 300],
    "staff": [2] * 10,
    "salary": [75000] * 10
}

# 自定义 CSS 样式
CSS_STYLES = """
    <style>
    /* 头部横幅样式 */
    .main-header-container {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem 1rem;
        border-radius: 0 0 15px 15px;
        color: white;
        text-align: center;
        margin-top: -4rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title { font-size: 2.2rem; font-weight: 800; margin: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }
    .sub-title { font-size: 1rem; opacity: 0.9; margin-top: 0.5rem; font-weight: 300; }

    /* 指标卡片优化 */
    [data-testid="stMetric"] {
        background-color: #f8f9fa; border-radius: 10px; padding: 15px;
        border: 1px solid #e9ecef; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #0056b3 !important; font-weight: 700 !important; }

    /* 移动端适配 */
    @media (max-width: 640px) {
        .main-title { font-size: 1.6rem; }
        [data-testid="stNumberInput"] input { width: 100%; }
    }
    </style>
"""

# ==========================================
# 2. 工具函数层 (Utility Functions)
# ==========================================
def dataframe_to_png(df):
    """将 DataFrame 渲染为 PNG 图像的 BytesIO 对象"""
    df_display = df.copy()
    # 千分位格式化
    for col in df_display.columns:
        if pd.api.types.is_numeric_dtype(df_display[col]) and col != "年份":
             df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f}")

    fig, ax = plt.subplots(figsize=(12, len(df)*0.6 + 1))
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df_display.values, colLabels=df_display.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)

    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#2a5298')
            cell.set_edgecolor('white')
        else:
            cell.set_edgecolor('#e9ecef')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf

def check_password():
    """安全验证门禁"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
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

# ==========================================
# 3. 核心逻辑层 (Core Logic) - 纯计算
# ==========================================
def calculate_capex(inputs):
    """计算各项 CAPEX 及总额"""
    capex_equip = (inputs['price_pile_unit'] * inputs['qty_piles']) + (inputs['price_trans_unit'] * inputs['qty_trans'])
    capex_power_infra = inputs['cost_dewa_conn'] + inputs['cost_hv_cable'] + inputs['cost_lv_cable']
    capex_civil = inputs['cost_civil_work'] + inputs['cost_canopy'] + inputs['cost_design']
    capex_others = inputs['other_cost_1'] + inputs['other_cost_2']
    total_capex = capex_equip + capex_power_infra + capex_civil + inputs['cost_weak_current_total'] + capex_others
    return total_capex

def calculate_financial_model(edited_df, total_capex, inputs):
    """执行年度财务推演计算"""
    results = []
    # Year 0
    results.append({
        "年份": "Y0", "营收": 0, "成本": 0, "税前净利": 0, "税金": 0, "税后净利": 0,
        "自由现金流": -total_capex, "累计现金流": -total_capex
    })
    cumulative_cash = -total_capex
    payback_year = None
    total_guns = inputs['qty_piles'] * inputs['guns_per_pile']

    # 年度迭代
    for index, row in edited_df.iterrows():
        year_idx = index
        daily_kwh = row["单枪日均充电量 (kWh)"]
        staff_count = row["运营人数 (人)"]
        salary_avg = row["人均年薪 (AED)"]
        
        annual_sales_kwh = daily_kwh * total_guns * 365
        revenue = annual_sales_kwh * inputs['price_sale']
        annual_buy_kwh = annual_sales_kwh / inputs['power_efficiency']
        cost_power = annual_buy_kwh * inputs['price_cost']
        
        inflation_factor = (1 + inputs['inflation_rate']) ** year_idx
        current_labor = (staff_count * salary_avg) * inflation_factor
        fixed_opex_base = inputs['base_rent'] + inputs['base_it_saas'] + inputs['base_marketing'] + inputs['base_maintenance']
        current_fixed = fixed_opex_base * inflation_factor
        cost_finance = total_capex * inputs['interest_rate']
        
        total_opex = cost_power + current_labor + current_fixed + cost_finance
        pre_tax_profit = revenue - total_opex
        
        tax_amount = 0
        if pre_tax_profit > inputs['tax_threshold']:
            tax_amount = (pre_tax_profit - inputs['tax_threshold']) * inputs['tax_rate']
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
            "营收": revenue, "成本": total_opex, "税前净利": pre_tax_profit,
            "税金": tax_amount, "税后净利": net_profit,
            "自由现金流": net_profit, "累计现金流": cumulative_cash, "资金成本": cost_finance
        })
    
    return pd.DataFrame(results), payback_year

# ==========================================
# 4. 界面渲染层 (UI Rendering) - 纯展示
# ==========================================
def render_header():
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    st.markdown("""
        <div class="main-header-container">
            <div class="main-title">🇦🇪 迪拜新能源超充站 · 投资测算模型 (V9.5 Pro)</div>
            <div class="sub-title">Financial Model & ROI Analysis | 专业版 UI | 模块化重构</div>
        </div>
    """, unsafe_allow_html=True)

def render_config_loader(years_duration):
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
            except Exception as e:
                st.error(f"❌ 文件读取失败：{e}")

def render_backend_config():
    inputs = {}
    st.write("")
    with st.expander("⚙️ **后台基准配置** (点击展开/收起)", expanded=False):
        st.caption("👇 以下数值基于 12 车位旗舰站基准设定。供应链变动可在此微调。")
        tab1, tab2, tab3 = st.tabs(["🏗️ CAPEX 明细", "🛠️ OPEX 基准", "📉 财务参数"])
        
        with tab1:
            with st.container(border=True):
                st.markdown("**1. 核心设备与电力设施**")
                c1, c2 = st.columns(2)
                inputs['pile_power_kw'] = c1.number_input("超充主机单台功率 (kW)", value=480, step=20)
                inputs['guns_per_pile'] = c1.number_input("单台主机配备枪数 (把)", value=6, step=1)
                inputs['price_pile_unit'] = c1.number_input("超充主机单价 (AED/台)", value=200000, step=5000)
                trans_type = c2.selectbox("专用箱式变电站规格", ["1000 kVA", "1500 kVA"])
                inputs['trans_val'] = 1000 if "1000" in trans_type else 1500
                inputs['price_trans_unit'] = c2.number_input("变电站单价 (AED/台)", value=(200000 if inputs['trans_val'] == 1000 else 250000))

            with st.container(border=True):
                 st.markdown("**2. 电力接入与土建工程**")
                 ce1, ce2 = st.columns(2)
                 inputs['cost_dewa_conn'] = ce1.number_input("DEWA 电力接入费", value=200000)
                 inputs['cost_hv_cable'] = ce1.number_input("高压电缆总成本", value=20000)
                 inputs['cost_lv_cable'] = ce1.number_input("低压电缆总成本", value=80000)
                 inputs['cost_civil_work'] = ce2.number_input("场地土建施工费", value=150000)
                 inputs['cost_canopy'] = ce2.number_input("高端遮阳棚与品牌", value=80000)
                 inputs['cost_design'] = ce2.number_input("设计与顾问费", value=40000)

            with st.container(border=True):
                st.markdown("**3. 弱电系统与杂项**")
                w1, w2, w3 = st.columns(3)
                cost_cctv = w1.number_input("视频监控 (CCTV)", value=25000)
                cost_locks = w2.number_input("智能地锁系统", value=30000)
                cost_network = w3.number_input("站内网络与布线", value=15000)
                inputs['cost_weak_current_total'] = cost_cctv + cost_locks + cost_network
                st.divider()
                o1, o2 = st.columns(2)
                inputs['other_cost_1'] = o1.number_input("前期开办费", value=30000)
                inputs['other_cost_2'] = o2.number_input("不可预见金", value=20000)

        with tab2:
            with st.container(border=True):
                st.markdown("### 年度固定运营投入 (Fixed OPEX)")
                o1, o2 = st.columns(2)
                inputs['base_rent'] = o1.number_input("场地车位租金 (AED/年)", value=96000)
                inputs['base_it_saas'] = o1.number_input("IT维护及SaaS开发 (AED/年)", value=50000)
                inputs['base_marketing'] = o2.number_input("广告及营销投入 (AED/年)", value=50000)
                inputs['base_maintenance'] = o2.number_input("基准维护外包 (AED/年)", value=30000)

        with tab3:
            with st.container(border=True):
                st.markdown("### 高阶财务参数")
                f1, f2, f3 = st.columns(3)
                inputs['power_efficiency'] = f1.number_input("⚡ 电能效率 (%)", value=95.0, step=0.5) / 100
                inputs['inflation_rate'] = f2.number_input("📈 OPEX 通胀率 (%)", value=3.0, step=0.5) / 100
                inputs['tax_rate'] = f3.number_input("🏛️ 企业所得税率 (%)", value=9.0, step=1.0) / 100
                inputs['tax_threshold'] = 375000
    return inputs

def render_project_inputs(backend_inputs):
    st.header("1. 项目规模与周期设定 (Project Scale)")
    inputs = backend_inputs.copy()
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### A. 设备数量")
            inputs['qty_piles'] = st.number_input("拟投超充主机 (台)", value=2, step=1)
            inputs['qty_trans'] = st.number_input("拟投变压器 (台)", value=1, step=1)
            total_power = inputs['qty_piles'] * inputs['pile_power_kw']
            total_trans = inputs['qty_trans'] * inputs['trans_val']
            if total_power > total_trans:
                st.error(f"⚠️ 容量不足: {total_power}kW > {total_trans}kVA")
            else:
                st.success(f"✅ 配置确认: {inputs['qty_piles']*inputs['guns_per_pile']}枪 | 总功率 {total_power}kW")
        with c2:
            st.markdown("##### B. 资金与电价")
            inputs['interest_rate'] = st.number_input("资金成本费率 (%)", value=5.0) / 100
            inputs['price_sale'] = st.number_input("销售电价 (AED/kWh)", value=1.20)
            inputs['price_cost'] = st.number_input("进货电价 (AED/kWh)", value=0.44)
        with c3:
            st.markdown("##### C. 周期设定")
            inputs['years_duration'] = st.number_input("运营测算年限 (年)", value=5)
    return inputs

def render_dynamic_table(years_duration):
    st.header("2. 年度运营推演核心表 (Dynamic Table)")
    st.markdown("✍️ **请直接编辑下表**修改每年的“单枪日充电量”和“人力配置”。")
    
    # 数据准备逻辑
    df_input = None
    if st.session_state.get('df_config_cache') is not None:
        df_uploaded = st.session_state['df_config_cache']
        if len(df_uploaded) < years_duration:
            extra_years = years_duration - len(df_uploaded)
            df_extra = pd.DataFrame({
                "单枪日均充电量 (kWh)": DEFAULT_PARAMS['daily_kwh'][len(df_uploaded):years_duration],
                "运营人数 (人)": DEFAULT_PARAMS['staff'][len(df_uploaded):years_duration],
                "人均年薪 (AED)": DEFAULT_PARAMS['salary'][len(df_uploaded):years_duration]
            })
            df_input = pd.concat([df_uploaded, df_extra], ignore_index=True)
        else:
            df_input = df_uploaded.head(years_duration)
    else:
        df_input = pd.DataFrame({
            "单枪日均充电量 (kWh)": DEFAULT_PARAMS['daily_kwh'][:years_duration],
            "运营人数 (人)": DEFAULT_PARAMS['staff'][:years_duration],
            "人均年薪 (AED)": DEFAULT_PARAMS['salary'][:years_duration]
        })
    
    df_input["年份"] = [f"Y{i+1}" for i in range(years_duration)]
    df_input = df_input[["年份", "单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]]

    # 渲染可编辑表格
    edited_df = st.data_editor(
        df_input,
        column_config={
            "年份": st.column_config.TextColumn(disabled=True, width="small"),
            "单枪日均充电量 (kWh)": st.column_config.NumberColumn(min_value=0, max_value=1000, step=10, required=True, format="%d kWh"),
            "运营人数 (人)": st.column_config.NumberColumn(min_value=0, step=1, format="%d 人"),
            "人均年薪 (AED)": st.column_config.NumberColumn(format="%d AED")
        },
        hide_index=True, use_container_width=True,
        height=int(35 * (years_duration + 2) if years_duration < 10 else 400)
    )
    return edited_df

def render_financial_report(df_res, total_capex, payback_year, years_duration):
    st.header("📊 财务评估结果 (Financial Report)")
    
    # 核心指标卡片
    m1, m2 = st.columns(2)
    m1.metric("💰 初始总投资 (CAPEX)", f"{total_capex:,.0f} AED", help="建设期总投入")
    m2.metric("💸 运营期总净利 (税后)", f"{df_res['税后净利'].sum():,.0f} AED", help="测算期内累计净利润")
    m3, m4 = st.columns(2)
    m3.metric("📉 总资金成本 (利息)", f"{df_res['资金成本'].sum():,.0f} AED")
    if payback_year and payback_year <= years_duration + 1:
        m4.metric("⏱️ 动态回本期 (Payback)", f"{payback_year:.1f} 年", delta="已回本", delta_color="normal")
    else:
        m4.metric("⏱️ 动态回本期 (Payback)", "未回本", delta="周期外", delta_color="inverse")
    st.write("")

    # 图表与表格 Tab
    tab_chart, tab_table = st.tabs(["📈 累计现金流曲线 (J-Curve)", "📄 详细现金流表 (Cash Flow)"])
    with tab_chart:
        st.area_chart(df_res.set_index("年份")["累计现金流"], color="#2a5298", use_container_width=True)
    with tab_table:
        st.dataframe(df_res.style.format("{:,.0f}", subset=["营收", "成本", "税前净利", "税金", "税后净利", "自由现金流", "累计现金流", "资金成本"]), use_container_width=True)

def render_download_section(df_res, edited_df):
    st.divider()
    with st.container(border=True):
        st.write("📥 **数据存取中心 (Data Center)**")
        c1, c2 = st.columns(2)
        with c1:
            csv_report = df_res.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📄 下载财务评估报告 (.csv)", csv_report, 'dubai_financial_report_v9.csv', 'text/csv', use_container_width=True)
            png_buffer = dataframe_to_png(df_res)
            st.download_button("🖼️ 下载表格图片 (.png)", png_buffer, 'dubai_financial_report_v9.png', 'image/png', use_container_width=True)
        with c2:
            csv_config = edited_df[["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]].to_csv(index=False).encode('utf-8-sig')
            st.download_button("💾 保存当前运营配置 (.csv)", csv_config, 'operation_config_v9.csv', 'text/csv', use_container_width=True)

# ==========================================
# 5. 主控制流 (Main Execution)
# ==========================================
def main():
    st.set_page_config(**PAGE_CONFIG)
    check_password() # 安全门禁

    render_header() # 渲染头部

    # 1. 获取所有输入参数
    backend_inputs = render_backend_config()
    all_inputs = render_project_inputs(backend_inputs)
    
    render_config_loader(all_inputs['years_duration']) # 渲染配置加载器

    # 2. 执行计算
    total_capex = calculate_capex(all_inputs)
    st.info(f"💰 **Year 0 (建设期) 总投入预估：{total_capex:,.0f} AED** (含全套设备、基建、弱电及杂项)")
    
    # 3. 获取动态输入并执行核心模型计算
    edited_df = render_dynamic_table(all_inputs['years_duration'])
    df_res, payback_year = calculate_financial_model(edited_df, total_capex, all_inputs)

    # 4. 渲染结果与下载区
    render_financial_report(df_res, total_capex, payback_year, all_inputs['years_duration'])
    render_download_section(df_res, edited_df)

if __name__ == "__main__":
    main()