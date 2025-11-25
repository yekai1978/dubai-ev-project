import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ==========================================
# 1. 配置与常量层
# ==========================================
PAGE_CONFIG = {
    "layout": "wide",
    "page_title": "迪拜新能源超充投资模型 V10.7 Ultimate",
    "page_icon": "🇦🇪",
}

ADMIN_PASSWORD = "DbeVc"
FONT_FILENAME = 'NotoSansSC-Regular.ttf'

# 默认年度推演参数
DEFAULT_PARAMS = {
    "daily_kwh": [50, 100, 150, 200, 250, 300, 350, 400, 450, 500],
    "staff": [2] * 10,
    "salary": [75000] * 10
}

# 自定义 CSS
CSS_STYLES = """
    <style>
    .main-header-container {
        background: linear-gradient(90deg, #1a2a6c, #b21f1f, #fdbb2d);
        padding: 2rem;
        border-radius: 15px;
        color: white; text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .main-title { font-size: 2.2rem; font-weight: 800; margin: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.3); }
    .sub-title { font-size: 1rem; opacity: 0.95; margin-top: 0.5rem; font-weight: 400; }
    [data-testid="stMetric"] {
        background-color: #fff; border-radius: 10px; padding: 15px;
        border: 1px solid #eee; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #1a2a6c !important; font-weight: 700 !important; }
    .stButton > button[type="primary"] {
        width: 100%; height: 3.5rem; font-size: 1.2rem; font-weight: bold;
        background: linear-gradient(90deg, #1a2a6c, #b21f1f); border: none;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); transition: all 0.3s ease;
    }
    .stButton > button[type="primary"]:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.3); }
    
    /* 优化 Checkbox 样式 */
    [data-testid="stCheckbox"] label { font-weight: 600; color: #1a2a6c; }
    
    @media (max-width: 640px) {
        .main-title { font-size: 1.6rem; }
        [data-testid="stNumberInput"] input { width: 100%; }
    }
    </style>
"""

# ==========================================
# 2. 资源加载与安全层
# ==========================================
@st.cache_resource
def load_custom_font():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, FONT_FILENAME)
    if os.path.exists(font_path): return fm.FontProperties(fname=font_path)
    else: return fm.FontProperties(family='sans-serif')

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return
    st.markdown("# 🔒 访问受限")
    with st.form("login_form"):
        password_input = st.text_input("请输入授权密码", type="password", label_visibility="collapsed")
        submit_button = st.form_submit_button("验证登录", type="primary", use_container_width=True)
        if submit_button:
            if password_input == ADMIN_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("密码错误")
    st.stop()

# ==========================================
# 3. 工具函数层
# ==========================================
def dataframe_to_png(df, font_prop):
    df_display = df.copy()
    for col in df_display.columns:
        if pd.api.types.is_numeric_dtype(df_display[col]) and col != "年份":
             df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f}" if abs(x) > 100 else (f"{x:.1f}" if abs(x) > 1 else f"{x:.2f}"))
    fig, ax = plt.subplots(figsize=(14, len(df)*0.7 + 2))
    ax.axis('tight'); ax.axis('off')
    table = ax.table(cellText=df_display.values, colLabels=df_display.columns, loc='center', cellLoc='center')
    for key, cell in table.get_celld().items():
        cell.set_text_props(fontproperties=font_prop); cell.set_edgecolor('#e0e0e0')
        if key[0] == 0:
            cell.set_facecolor('#1a2a6c'); cell.get_text().set_color('white'); cell.get_text().set_weight('bold'); cell.set_height(0.08)
        else:
            cell.set_height(0.06)
            if key[0] % 2 == 0: cell.set_facecolor('#f8f9fa')
    table.auto_set_font_size(False); table.set_fontsize(11); table.scale(1.1, 1.1)
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, transparent=True); buf.seek(0); plt.close(fig)
    return buf

# ==========================================
# 4. 核心逻辑层 (计算)
# ==========================================
def calculate_capex_details(inputs):
    """将 CAPEX 按照折旧类别进行分组计算"""
    # 1. 充电设备类
    capex_charger = (inputs['price_pile_unit'] * inputs['qty_piles'])
    # 2. 变压器及接入类
    capex_trans_group = (inputs['price_trans_unit'] * inputs['qty_trans']) + inputs['cost_dewa_conn']
    # 3. 线缆类
    capex_cable_group = inputs['cost_hv_cable'] + inputs['cost_lv_cable']
    # 4. 土建及其他类
    capex_civil_other = inputs['cost_civil_work'] + inputs['cost_canopy'] + inputs['cost_design'] + \
                        inputs['cost_weak_current_total'] + inputs['other_cost_1'] + inputs['other_cost_2']
    
    total_capex = capex_charger + capex_trans_group + capex_cable_group + capex_civil_other
    
    return {
        "total_capex": total_capex,
        "capex_charger": capex_charger,
        "capex_trans_group": capex_trans_group,
        "capex_cable_group": capex_cable_group,
        "capex_civil_other": capex_civil_other
    }

def calculate_financial_model(edited_df, capex_data, inputs):
    results = []
    total_capex = capex_data["total_capex"]
    results.append({"年份": "Y0", "营收": 0, "成本(OPEX)": 0, "折旧(抵税)": 0, "息税前利(EBIT)": 0, "税金": 0, "净利润": 0, "自由现金流(FCF)": -total_capex, "累计现金流": -total_capex})
    cumulative_cash = -total_capex
    payback_year = None
    total_guns = inputs['qty_piles'] * inputs['guns_per_pile']

    # --- V10.7 核心升级：计算分类年折旧额 (加入是否启用判断) ---
    # 如果未启用折旧，或年限设置不合理，则该项年折旧额为 0
    dep_charger_annual = 0
    if inputs.get('enable_dep_charger', True) and inputs['dep_years_charger'] > 0:
        dep_charger_annual = capex_data["capex_charger"] / inputs['dep_years_charger']

    dep_trans_annual = 0
    if inputs.get('enable_dep_trans', True) and inputs['dep_years_trans'] > 0:
        dep_trans_annual = capex_data["capex_trans_group"] / inputs['dep_years_trans']

    dep_cable_annual = 0
    if inputs.get('enable_dep_cable', True) and inputs['dep_years_cable'] > 0:
        dep_cable_annual = capex_data["capex_cable_group"] / inputs['dep_years_cable']

    dep_civil_annual = 0
    if inputs.get('enable_dep_civil', True) and inputs['dep_years_civil'] > 0:
        dep_civil_annual = capex_data["capex_civil_other"] / inputs['dep_years_civil']
    # ------------------------------------------------------

    for index, row in edited_df.iterrows():
        year_idx = index; year_num = year_idx + 1
        daily_kwh = row["单枪日均充电量 (kWh)"]; staff_count = row["运营人数 (人)"]; salary_avg = row["人均年薪 (AED)"]
        
        current_price_sale = inputs['price_sale'] * ((1 + inputs['price_sale_growth']) ** year_idx)
        current_price_cost = inputs['price_cost'] * ((1 + inputs['price_cost_growth']) ** year_idx)
        annual_sales_kwh = daily_kwh * total_guns * 365
        revenue = annual_sales_kwh * current_price_sale
        
        annual_buy_kwh = annual_sales_kwh / inputs['power_efficiency']
        cost_power = annual_buy_kwh * current_price_cost
        inflation_factor = (1 + inputs['inflation_rate']) ** year_idx
        current_labor = (staff_count * salary_avg) * inflation_factor
        fixed_opex_base = inputs['base_rent'] + inputs['base_it_saas'] + inputs['base_marketing'] + inputs['base_maintenance']
        current_fixed = fixed_opex_base * inflation_factor
        total_opex = cost_power + current_labor + current_fixed
        
        ebitda = revenue - total_opex
        
        # 计算当年总折旧额（判断各项是否在折旧期内，且已启用）
        current_dep_charger = dep_charger_annual if (inputs.get('enable_dep_charger', True) and year_num <= inputs['dep_years_charger']) else 0
        current_dep_trans = dep_trans_annual if (inputs.get('enable_dep_trans', True) and year_num <= inputs['dep_years_trans']) else 0
        current_dep_cable = dep_cable_annual if (inputs.get('enable_dep_cable', True) and year_num <= inputs['dep_years_cable']) else 0
        current_dep_civil = dep_civil_annual if (inputs.get('enable_dep_civil', True) and year_num <= inputs['dep_years_civil']) else 0
        current_total_depreciation = current_dep_charger + current_dep_trans + current_dep_cable + current_dep_civil

        ebit = ebitda - current_total_depreciation
        cost_finance = total_capex * inputs['interest_rate']
        ebt = ebit - cost_finance
        tax_amount = (ebt - inputs['tax_threshold']) * inputs['tax_rate'] if ebt > inputs['tax_threshold'] else 0
        net_profit = ebt - tax_amount
        free_cash_flow = net_profit + current_total_depreciation
        cumulative_cash += free_cash_flow
        
        if payback_year is None and cumulative_cash >= 0:
            prev_cash = results[-1]["累计现金流"]
            payback_year = (year_idx) + (abs(prev_cash) / free_cash_flow) if free_cash_flow > 0 else year_idx + 1

        results.append({"年份": f"Y{year_num}", "营收": revenue, "成本(OPEX)": total_opex, "折旧(抵税)": current_total_depreciation, "息税前利(EBIT)": ebit, "税金": tax_amount, "净利润": net_profit, "自由现金流(FCF)": free_cash_flow, "累计现金流": cumulative_cash})
    
    return pd.DataFrame(results), payback_year

# ==========================================
# 5. 界面渲染层 (UI Rendering)
# ==========================================
def render_header():
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    st.markdown("""
        <div class="main-header-container">
            <div class="main-title">🇦🇪 迪拜新能源超充站 · 投资测算模型</div>
            <div class="sub-title">V10.7 Ultimate | 极简流线版 | 灵活折旧策略</div>
        </div>
    """, unsafe_allow_html=True)

def render_config_import():
    with st.expander("📂 **导入历史配置 (Optional)**", expanded=False):
        uploaded_config = st.file_uploader("上传CSV文件恢复表格设置", type=["csv"])
        if uploaded_config is not None:
            try:
                df_uploaded = pd.read_csv(uploaded_config)
                required_columns = ["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]
                if all(col in df_uploaded.columns for col in required_columns):
                    st.session_state['df_config_cache'] = df_uploaded
                    st.toast("配置已加载，将在下方表格中生效。", icon="✅")
                else: st.error("CSV格式错误，缺少必要列。")
            except Exception as e: st.error(f"读取失败：{e}")

def render_base_params_section():
    st.header("1. 基础参数设置 (Base Parameters)")
    with st.expander("⚙️ **点击展开/收起基准配置 (Advanced Config)**", expanded=False):
        st.caption("包含供应链单价、运营基准费用及核心财务假设。")
        inputs = {}
        t1, t2, t3 = st.tabs(["🏗️ CAPEX基建", "🛠️ OPEX运营", "📉 财务假设"])
        with t1:
            c1, c2 = st.columns(2)
            inputs['pile_power_kw'] = c1.number_input("主机功率(kW)", value=480, step=20)
            inputs['guns_per_pile'] = c2.number_input("单机枪数(把)", value=6, step=1)
            inputs['price_pile_unit'] = st.number_input("主机单价(AED)", value=200000, step=5000)
            tt1, tt2 = st.columns(2)
            trans_type = tt1.selectbox("变电站规格", ["1000 kVA", "1500 kVA"])
            inputs['trans_val'] = 1000 if "1000" in trans_type else 1500
            inputs['price_trans_unit'] = tt2.number_input("变电站单价", value=(200000 if inputs['trans_val']==1000 else 250000), step=5000)
            st.markdown("---")
            inputs['cost_dewa_conn'] = st.number_input("DEWA接入费", value=200000, step=10000)
            inputs['cost_civil_work'] = st.number_input("土建施工费", value=150000, step=10000)
            inputs['cost_weak_current_total'] = st.number_input("弱电/杂项/开办费总计", value=120000, step=10000)
            inputs['cost_hv_cable'] = 20000; inputs['cost_lv_cable'] = 80000; inputs['cost_canopy'] = 80000; inputs['cost_design'] = 40000; inputs['other_cost_1'] = 0; inputs['other_cost_2'] = 0

        with t2:
            inputs['base_rent'] = st.number_input("车位租金(AED/年)", value=96000, step=5000)
            inputs['base_it_saas'] = st.number_input("IT/SaaS/营销/维保总计(AED/年)", value=130000, step=5000)
            inputs['base_marketing'] = 0; inputs['base_maintenance'] = 0

        with t3:
            f1, f2 = st.columns(2)
            inputs['power_efficiency'] = f1.number_input("⚡ 电能效率(%)", value=95.0, step=0.5) / 100
            inputs['inflation_rate'] = f2.number_input("📈 通胀率(%)", value=3.0, step=0.5) / 100
            p1, p2 = st.columns(2)
            inputs['price_sale_growth'] = p1.number_input("💹 销售涨幅(%)", value=0.0, step=0.5) / 100
            inputs['price_cost_growth'] = p2.number_input("💹 成本涨幅(%)", value=0.0, step=0.5) / 100
            tx1, tx2 = st.columns(2)
            inputs['tax_rate'] = tx1.number_input("🏛️ 税率(%)", value=9.0, step=1.0) / 100
            inputs['tax_threshold'] = tx2.number_input("免税额度", value=375000, step=10000)
            
            st.markdown("---")
            st.markdown("##### 折旧策略设定 (Depreciation Strategy)")
            st.caption("勾选“启用”后，对应的资产将按设定年限计提折旧以抵扣税基；否则不计折旧。")
            
            # --- V10.7 核心升级：可选可填的折旧设置 ---
            dp1, dp2, dp3, dp4 = st.columns(4)
            with dp1:
                st.markdown("**🔋 充电设备**")
                inputs['enable_dep_charger'] = st.checkbox("启用折旧", value=True, key="cb_c")
                if inputs['enable_dep_charger']:
                     inputs['dep_years_charger'] = st.number_input("年限(年)", value=5, min_value=1, step=1, key="ni_c")
                else: inputs['dep_years_charger'] = 1 # Dummy value
            
            with dp2:
                st.markdown("**🏗️ 变压器及接入**")
                inputs['enable_dep_trans'] = st.checkbox("启用折旧", value=True, key="cb_t")
                if inputs['enable_dep_trans']:
                    inputs['dep_years_trans'] = st.number_input("年限(年)", value=15, min_value=1, step=1, key="ni_t")
                else: inputs['dep_years_trans'] = 1

            with dp3:
                st.markdown("**➰ 线缆工程**")
                inputs['enable_dep_cable'] = st.checkbox("启用折旧", value=True, key="cb_ca")
                if inputs['enable_dep_cable']:
                    inputs['dep_years_cable'] = st.number_input("年限(年)", value=20, min_value=1, step=1, key="ni_ca")
                else: inputs['dep_years_cable'] = 1
            
            with dp4:
                st.markdown("**🧱 土建及其他**")
                inputs['enable_dep_civil'] = st.checkbox("启用折旧", value=True, key="cb_ci")
                if inputs['enable_dep_civil']:
                    inputs['dep_years_civil'] = st.number_input("年限(年)", value=20, min_value=1, step=1, key="ni_ci")
                else: inputs['dep_years_civil'] = 1
            # ---------------------------------------

    return inputs

def render_project_scale_section(inputs):
    st.header("2. 项目规模与周期 (Project Scale)")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### A. 设备数量")
            inputs['qty_piles'] = st.number_input("拟投超充主机 (台)", value=2, min_value=1, step=1)
            inputs['qty_trans'] = st.number_input("拟投变压器 (台)", value=1, min_value=1, step=1)
        with c2:
            st.markdown("##### B. 资金与电价 (Y1基准)")
            inputs['interest_rate'] = st.number_input("资金成本费率 (%)", value=5.0, step=0.5) / 100
            inputs['price_sale'] = st.number_input("销售电价 (AED/kWh)", value=1.20, step=0.05)
            inputs['price_cost'] = st.number_input("进货电价 (AED/kWh)", value=0.44, step=0.05)
        with c3:
            st.markdown("##### C. 周期设定")
            inputs['years_duration'] = st.number_input("运营测算年限 (年)", value=10, min_value=3, max_value=20, step=1)

    total_power = inputs['qty_piles'] * inputs['pile_power_kw']
    total_trans = inputs['qty_trans'] * inputs['trans_val']
    if total_power > total_trans: st.warning(f"⚠️ 容量提示: 总功率 {total_power}kW > 变压器 {total_trans}kVA")
    else: st.success(f"✅ 配置确认: {inputs['qty_piles']*inputs['guns_per_pile']}枪 | 总功率 {total_power}kW | 变压器 {total_trans}kVA")
    return inputs

def render_capex_preview(inputs):
    capex_data = calculate_capex_details(inputs)
    with st.container(border=True):
        st.markdown(f"**💰 Year 0 初始投资预览：{capex_data['total_capex']:,.0f} AED**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔋 充电设备", f"{capex_data['capex_charger']:,.0f}")
        c2.metric("🏗️ 变压器及接入", f"{capex_data['capex_trans_group']:,.0f}")
        c3.metric("➰ 线缆工程", f"{capex_data['capex_cable_group']:,.0f}")
        c4.metric("🧱 土建及其他", f"{capex_data['capex_civil_other']:,.0f}")
    return capex_data

def render_dynamic_table_section(years_duration):
    st.header("3. 年度运营推演 (Annual Operations)")
    st.caption("请在下方表格中直接修改每年的关键运营假设。")
    df_input = None
    if st.session_state.get('df_config_cache') is not None:
        df_uploaded = st.session_state['df_config_cache']
        if len(df_uploaded) < years_duration:
            last_row = df_uploaded.iloc[-1]
            df_extra = pd.DataFrame([last_row] * (years_duration - len(df_uploaded)))
            df_input = pd.concat([df_uploaded, df_extra], ignore_index=True)
        else: df_input = df_uploaded.head(years_duration)
    else:
        long_daily_kwh = DEFAULT_PARAMS['daily_kwh'] + [DEFAULT_PARAMS['daily_kwh'][-1]] * years_duration
        long_staff = DEFAULT_PARAMS['staff'] + [DEFAULT_PARAMS['staff'][-1]] * years_duration
        long_salary = DEFAULT_PARAMS['salary'] + [DEFAULT_PARAMS['salary'][-1]] * years_duration
        df_input = pd.DataFrame({"单枪日均充电量 (kWh)": long_daily_kwh[:years_duration],"运营人数 (人)": long_staff[:years_duration],"人均年薪 (AED)": long_salary[:years_duration]})
    
    df_input["年份"] = [f"Y{i+1}" for i in range(years_duration)]
    df_input = df_input[["年份", "单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]]

    edited_df = st.data_editor(
        df_input,
        column_config={
            "年份": st.column_config.TextColumn(disabled=True, width="small"),
            "单枪日均充电量 (kWh)": st.column_config.NumberColumn(label="✏️ 日均充电量 (kWh)", min_value=0, max_value=2500, step=10, required=True, format="%d"),
            "运营人数 (人)": st.column_config.NumberColumn(label="✏️ 运营人数 (人)", min_value=0, step=1, format="%d"),
            "人均年薪 (AED)": st.column_config.NumberColumn(label="✏️ 人均年薪 (AED)", format="%d")
        },
        hide_index=True, use_container_width=True, height=int(38 * (min(years_duration, 12) + 2))
    )
    return edited_df

def render_run_button():
    st.divider()
    run_pressed = st.button("🚀 开始测算 (Run Analysis)", type="primary", use_container_width=True)
    return run_pressed

def render_results_section(df_res, total_capex, payback_year, edited_df, font_prop):
    st.divider()
    st.header("📊 测算结果报告 (Results Report)")
    total_net_profit = df_res["净利润"].sum()
    total_fcf_ops = df_res["净利润"].sum() + df_res["折旧(抵税)"].sum() 
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 初始总投资 (CAPEX)", f"{total_capex:,.0f}")
    c2.metric("💸 运营期总净利", f"{total_net_profit:,.0f}")
    c3.metric("🌊 运营期自由现金流", f"{total_fcf_ops:,.0f}")
    if payback_year and payback_year <= len(df_res) + 1: c4.metric("⏱️ 动态回本期", f"{payback_year:.1f} 年", delta="已回本", delta_color="normal")
    else: c4.metric("⏱️ 动态回本期", "未回本", delta="周期外", delta_color="inverse")

    tab_chart, tab_table = st.tabs(["📈 现金流曲线", "📄 详细报表"])
    with tab_chart: st.area_chart(df_res.set_index("年份")["累计现金流"], color="#1a2a6c", use_container_width=True)
    with tab_table:
        cols_to_show = ["营收", "成本(OPEX)", "折旧(抵税)", "息税前利(EBIT)", "税金", "净利润", "自由现金流(FCF)", "累计现金流"]
        st.dataframe(df_res.style.format("{:,.0f}", subset=cols_to_show), use_container_width=True)

    st.divider()
    with st.expander("📥 **下载数据与报告 (Download)**", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            csv_report = df_res.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📄 下载财务报告 (.csv)", csv_report, 'financial_report_v10.7.csv', 'text/csv', use_container_width=True)
            png_buffer = dataframe_to_png(df_res, font_prop)
            st.download_button("🖼️ 下载表格图片 (.png)", png_buffer, 'financial_report_v10.7.png', 'image/png', use_container_width=True)
        with c2:
            csv_config = edited_df[["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]].to_csv(index=False).encode('utf-8-sig')
            st.download_button("💾 保存当前配置 (.csv)", csv_config, 'operation_config_v10.7.csv', 'text/csv', use_container_width=True)

# ==========================================
# 6. 主控制流
# ==========================================
def main():
    st.set_page_config(**PAGE_CONFIG)
    zh_font = load_custom_font()
    check_password()
    render_header()
    render_config_import()
    inputs = render_base_params_section()
    inputs = render_project_scale_section(inputs)
    capex_data = render_capex_preview(inputs)
    edited_df = render_dynamic_table_section(inputs['years_duration'])
    
    if 'run_analysis' not in st.session_state: st.session_state['run_analysis'] = False
    if render_run_button(): st.session_state['run_analysis'] = True

    if st.session_state['run_analysis']:
        with st.spinner("正在进行复杂财务测算..."):
            df_res, payback_year = calculate_financial_model(edited_df, capex_data, inputs)
        render_results_section(df_res, capex_data['total_capex'], payback_year, edited_df, zh_font)
    else:
        st.info("👉 请按照顺序设置参数，最后点击上方按钮开始测算。")

if __name__ == "__main__":
    main()