import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ==========================================
# 1. 配置与常量层 (Configuration & Constants)
# ==========================================
PAGE_CONFIG = {
    "layout": "wide",
    "page_title": "迪拜新能源超充投资模型 V10.0 Ultimate",
    "page_icon": "🇦🇪",
    "initial_sidebar_state": "expanded" # 默认展开侧边栏以提示用户
}

ADMIN_PASSWORD = "DbeVc"
FONT_FILENAME = 'NotoSansSC-Regular.ttf'

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
        color: white; text-align: center;
        margin-top: -4rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title { font-size: 2.2rem; font-weight: 800; margin: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }
    .sub-title { font-size: 1rem; opacity: 0.9; margin-top: 0.5rem; font-weight: 300; }

    /* 指标卡片优化 */
    [data-testid="stMetric"] {
        background-color: #f8f9fa; border-radius: 10px; padding: 15px;
        border: 1px solid #e9ecef; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: transform 0.2s;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #0056b3 !important; font-weight: 700 !important; }

    /* 侧边栏样式微调 */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    /* 表单提交按钮样式 */
    [data-testid="stFormSubmitButton"] button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
    }

    /* 移动端适配 */
    @media (max-width: 640px) {
        .main-title { font-size: 1.6rem; }
        [data-testid="stNumberInput"] input { width: 100%; }
    }
    </style>
"""

# ==========================================
# 2. 资源加载与安全层 (Resources & Security)
# ==========================================
@st.cache_resource
def load_custom_font():
    """加载自定义中文字体，使用缓存避免重复加载"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, FONT_FILENAME)
    
    if os.path.exists(font_path):
        return fm.FontProperties(fname=font_path)
    else:
        print(f"Warning: Font file '{FONT_FILENAME}' not found. Chinese characters may not render correctly in images.")
        return fm.FontProperties(family='sans-serif')

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
# 3. 工具函数层 (Utility Functions)
# ==========================================
def dataframe_to_png(df, font_prop):
    """将 DataFrame 渲染为 PNG 图像的 BytesIO 对象，应用自定义字体"""
    df_display = df.copy()
    for col in df_display.columns:
        if pd.api.types.is_numeric_dtype(df_display[col]) and col != "年份":
             df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f}")

    fig, ax = plt.subplots(figsize=(12, len(df)*0.6 + 1))
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(cellText=df_display.values, colLabels=df_display.columns, loc='center', cellLoc='center')
    
    for key, cell in table.get_celld().items():
        cell.set_text_props(fontproperties=font_prop)

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)

    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_facecolor('#2a5298')
            cell.set_edgecolor('white')
            cell.get_text().set_color('white') 
        else:
            cell.set_edgecolor('#e9ecef')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf

# ==========================================
# 4. 核心逻辑层 (Core Logic) - 纯计算
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
    """执行年度财务推演计算（含动态电价与折旧抵税）"""
    results = []
    # Year 0
    results.append({
        "年份": "Y0", "营收": 0, "成本(OPEX)": 0, "折旧": 0, "息税前利(EBIT)": 0,
        "税金": 0, "净利润": 0, "自由现金流(FCF)": -total_capex, "累计现金流": -total_capex
    })
    cumulative_cash = -total_capex
    payback_year = None
    total_guns = inputs['qty_piles'] * inputs['guns_per_pile']
    
    # 计算年折旧额 (直线法)
    annual_depreciation = total_capex / inputs['depreciation_years'] if inputs['depreciation_years'] > 0 else 0

    # 年度迭代
    for index, row in edited_df.iterrows():
        year_idx = index # 0-indexed, 对应 Y1, Y2...
        
        # 1. 获取年度输入变量
        daily_kwh = row["单枪日均充电量 (kWh)"]
        staff_count = row["运营人数 (人)"]
        salary_avg = row["人均年薪 (AED)"]
        
        # 2. 计算动态电价 (考虑年增长率)
        current_price_sale = inputs['price_sale'] * ((1 + inputs['price_sale_growth']) ** year_idx)
        current_price_cost = inputs['price_cost'] * ((1 + inputs['price_cost_growth']) ** year_idx)

        # 3. 收入计算
        annual_sales_kwh = daily_kwh * total_guns * 365
        revenue = annual_sales_kwh * current_price_sale
        
        # 4. 支出计算 (OPEX)
        annual_buy_kwh = annual_sales_kwh / inputs['power_efficiency']
        cost_power = annual_buy_kwh * current_price_cost
        
        inflation_factor = (1 + inputs['inflation_rate']) ** year_idx
        current_labor = (staff_count * salary_avg) * inflation_factor
        fixed_opex_base = inputs['base_rent'] + inputs['base_it_saas'] + inputs['base_marketing'] + inputs['base_maintenance']
        current_fixed = fixed_opex_base * inflation_factor
        
        total_opex = cost_power + current_labor + current_fixed
        
        # 5. 利润计算 (EBITDA -> EBIT -> EBT -> Net Profit)
        ebitda = revenue - total_opex # 息税折旧摊销前利润
        
        # 处理折旧年限结束的情况
        current_depreciation = annual_depreciation if (year_idx + 1) <= inputs['depreciation_years'] else 0
        
        ebit = ebitda - current_depreciation # 息税前利润
        
        cost_finance = total_capex * inputs['interest_rate'] # 资金成本(利息)
        ebt = ebit - cost_finance # 税前利润
        
        # 税务计算
        tax_amount = 0
        if ebt > inputs['tax_threshold']:
            tax_amount = (ebt - inputs['tax_threshold']) * inputs['tax_rate']
        
        net_profit = ebt - tax_amount # 净利润
        
        # 6. 现金流计算 (自由现金流 FCF = 净利润 + 折旧)
        # *重要*: 资金成本(利息)已经在EBT中扣除，属于融资活动，标准FCF定义通常不加回利息，
        # 但对于项目投资回报测算，我们关注的是项目产生的用于偿还债务和回报股东的现金流。
        # 这里采用 FCFE (股权自由现金流) 的简化近似：净利润 + 折旧
        free_cash_flow = net_profit + current_depreciation
        
        cumulative_cash += free_cash_flow
        
        # 7. 回本期计算
        if payback_year is None and cumulative_cash >= 0:
            prev_cash = results[-1]["累计现金流"]
            if free_cash_flow > 0:
                 payback_year = (year_idx) + (abs(prev_cash) / free_cash_flow)
            else:
                 payback_year = year_idx + 1

        results.append({
            "年份": f"Y{year_idx + 1}",
            "营收": revenue, "成本(OPEX)": total_opex, "折旧": current_depreciation,
            "息税前利(EBIT)": ebit, "税金": tax_amount, "净利润": net_profit,
            "自由现金流(FCF)": free_cash_flow, "累计现金流": cumulative_cash,
            "资金成本(利息)": cost_finance # 仅做记录展示
        })
    
    return pd.DataFrame(results), payback_year

# ==========================================
# 5. 界面渲染层 (UI Rendering) - 纯展示
# ==========================================
def render_header():
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    st.markdown("""
        <div class="main-header-container">
            <div class="main-title">🇦🇪 迪拜新能源超充站 · 投资测算模型 (V10.0 Ultimate)</div>
            <div class="sub-title">Financial Model & ROI Analysis | 动态电价模型 | 折旧抵税 | 交互体验升级</div>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar_content(years_duration):
    """渲染侧边栏内容：配置导入和后台基准配置"""
    with st.sidebar:
        st.header("🎛️ 控制面板 (Control Panel)")
        
        # --- 配置导入区 ---
        with st.expander("📂 **导入历史配置**", expanded=False):
            st.caption("上传 csv 文件恢复表格设置。")
            uploaded_config = st.file_uploader("上传配置", type=["csv"], label_visibility="collapsed")
            if uploaded_config is not None:
                try:
                    df_uploaded = pd.read_csv(uploaded_config)
                    required_columns = ["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]
                    if all(col in df_uploaded.columns for col in required_columns):
                        st.session_state['df_config_cache'] = df_uploaded
                        st.toast("✅ 配置文件已加载，请在主界面确认。", icon="📂")
                    else:
                        st.error(f"❌ 格式错误，缺少必要列。")
                except Exception as e:
                    st.error(f"❌ 文件读取失败：{e}")
        
        st.divider()

        # --- 后台基准配置区 ---
        st.subheader("⚙️ 后台基准配置")
        st.caption("基于旗舰站点的供应链与财务参数设定。")
        
        inputs = {}
        with st.expander("🏗️ **CAPEX 明细 (基建设备)**", expanded=False):
            st.markdown("**1. 核心设备**")
            inputs['pile_power_kw'] = st.number_input("主机功率 (kW)", 480, 20)
            inputs['guns_per_pile'] = st.number_input("单机枪数 (把)", 6, 1)
            inputs['price_pile_unit'] = st.number_input("主机单价 (AED)", 200000, 5000)
            trans_type = st.selectbox("变电站规格", ["1000 kVA", "1500 kVA"])
            inputs['trans_val'] = 1000 if "1000" in trans_type else 1500
            inputs['price_trans_unit'] = st.number_input("变电站单价 (AED)", (200000 if inputs['trans_val'] == 1000 else 250000))
            
            st.divider()
            st.markdown("**2. 电力与土建**")
            inputs['cost_dewa_conn'] = st.number_input("DEWA接入费", 200000)
            inputs['cost_hv_cable'] = st.number_input("高压电缆", 20000)
            inputs['cost_lv_cable'] = st.number_input("低压电缆", 80000)
            inputs['cost_civil_work'] = st.number_input("土建施工", 150000)
            inputs['cost_canopy'] = st.number_input("遮阳棚品牌", 80000)
            inputs['cost_design'] = st.number_input("设计顾问", 40000)
            
            st.divider()
            st.markdown("**3. 弱电与杂项**")
            cost_cctv = st.number_input("视频监控", 25000)
            cost_locks = st.number_input("智能地锁", 30000)
            cost_network = st.number_input("站内网络", 15000)
            inputs['cost_weak_current_total'] = cost_cctv + cost_locks + cost_network
            inputs['other_cost_1'] = st.number_input("前期开办费", 30000)
            inputs['other_cost_2'] = st.number_input("不可预见金", 20000)

        with st.expander("🛠️ **OPEX 基准 (固定运营)**", expanded=False):
            inputs['base_rent'] = st.number_input("车位租金 (AED/年)", 96000)
            inputs['base_it_saas'] = st.number_input("IT/SaaS (AED/年)", 50000)
            inputs['base_marketing'] = st.number_input("广告营销 (AED/年)", 50000)
            inputs['base_maintenance'] = st.number_input("维保外包 (AED/年)", 30000)

        with st.expander("📉 **财务参数 (核心假设)**", expanded=True):
            inputs['power_efficiency'] = st.number_input("⚡ 电能效率 (%)", 95.0, 0.5) / 100
            inputs['inflation_rate'] = st.number_input("📈 OPEX 通胀率 (%)", 3.0, 0.5) / 100
            st.divider()
            # --- 新增：动态电价参数 ---
            inputs['price_sale_growth'] = st.number_input("💹 销售电价年增长率 (%)", value=0.0, step=0.5, help="每年销售电价的环比增长") / 100
            inputs['price_cost_growth'] = st.number_input("💹 进货电价年增长率 (%)", value=0.0, step=0.5, help="每年进货成本的环比增长") / 100
            st.divider()
            inputs['tax_rate'] = st.number_input("🏛️ 企业所得税率 (%)", 9.0, 1.0) / 100
            inputs['tax_threshold'] = 375000
            # --- 新增：折旧参数 ---
            inputs['depreciation_years'] = st.number_input("📅 综合资产折旧年限 (年)", value=8, step=1, min_value=1, help="用于计算CAPEX的直线折旧以抵扣税基")
        
        st.markdown("---")
        st.caption("Made for Dubai EV Project Theme")
            
    return inputs

def render_project_inputs_form(backend_inputs):
    """渲染主界面的项目输入表单"""
    st.header("1. 项目规模与周期设定 (Project Setup)")
    inputs = backend_inputs.copy()
    
    # 使用表单包裹，提升交互体验
    with st.form("project_inputs_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### A. 设备数量")
            inputs['qty_piles'] = st.number_input("拟投超充主机 (台)", value=2, step=1)
            inputs['qty_trans'] = st.number_input("拟投变压器 (台)", value=1, step=1)
        with c2:
            st.markdown("##### B. 资金与电价 (基准)")
            inputs['interest_rate'] = st.number_input("资金成本费率 (%)", value=5.0) / 100
            inputs['price_sale'] = st.number_input("销售电价 (AED/kWh)", value=1.20, help="Year 1 基准电价")
            inputs['price_cost'] = st.number_input("进货电价 (AED/kWh)", value=0.44, help="Year 1 基准电价")
        with c3:
            st.markdown("##### C. 周期设定")
            inputs['years_duration'] = st.number_input("运营测算年限 (年)", value=10, min_value=3, max_value=20)
        
        # 表单提交按钮
        submitted = st.form_submit_button("🔄 确认并运行测算 (Run Model)", type="primary", use_container_width=True)

    # 容量校验提示 (在表单外显示)
    total_power = inputs['qty_piles'] * inputs['pile_power_kw']
    total_trans = inputs['qty_trans'] * inputs['trans_val']
    if total_power > total_trans:
        st.warning(f"⚠️ **容量提示**: 当前配置总功率 ({total_power}kW) 已超过变压器容量 ({total_trans}kVA)，请确认需量系数或调整配置。")
    else:
        st.success(f"✅ **配置确认**: {inputs['qty_piles']*inputs['guns_per_pile']}枪 | 总功率 {total_power}kW | 变压器 {total_trans}kVA")
        
    return inputs, submitted

def render_dynamic_table(years_duration):
    st.header("2. 年度运营推演核心表 (Dynamic Table)")
    st.markdown("✍️ **请直接编辑下表**修改每年的“单枪日充电量”和“人力配置”。")
    
    df_input = None
    # 尝试从缓存加载配置，并自适应当前的测算年限
    if st.session_state.get('df_config_cache') is not None:
        df_uploaded = st.session_state['df_config_cache']
        # 确保上传的数据包含必要的列
        required_cols = ["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]
        if not all(col in df_uploaded.columns for col in required_cols):
             st.error("缓存的配置数据缺少必要列，将使用默认值。")
             st.session_state.pop('df_config_cache', None)
             # fallback to default
             df_input = pd.DataFrame({
                "单枪日均充电量 (kWh)": (DEFAULT_PARAMS['daily_kwh'] * 3)[:years_duration],
                "运营人数 (人)": (DEFAULT_PARAMS['staff'] * 3)[:years_duration],
                "人均年薪 (AED)": (DEFAULT_PARAMS['salary'] * 3)[:years_duration]
            })
        else:
            # 数据有效，进行长度适配
            if len(df_uploaded) < years_duration:
                # 数据不够，用最后一行填充
                last_row = df_uploaded.iloc[-1]
                extra_years = years_duration - len(df_uploaded)
                df_extra = pd.DataFrame([last_row] * extra_years)
                df_input = pd.concat([df_uploaded, df_extra], ignore_index=True)
            else:
                # 数据过多，截取
                df_input = df_uploaded.head(years_duration)
    else:
        # 无缓存，使用默认爬坡数据 (扩展到足够长以应对长周期测算)
        long_daily_kwh = DEFAULT_PARAMS['daily_kwh'] + [DEFAULT_PARAMS['daily_kwh'][-1]] * (years_duration)
        long_staff = DEFAULT_PARAMS['staff'] + [DEFAULT_PARAMS['staff'][-1]] * (years_duration)
        long_salary = DEFAULT_PARAMS['salary'] + [DEFAULT_PARAMS['salary'][-1]] * (years_duration)
        
        df_input = pd.DataFrame({
            "单枪日均充电量 (kWh)": long_daily_kwh[:years_duration],
            "运营人数 (人)": long_staff[:years_duration],
            "人均年薪 (AED)": long_salary[:years_duration]
        })
    
    df_input["年份"] = [f"Y{i+1}" for i in range(years_duration)]
    df_input = df_input[["年份", "单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]]

    edited_df = st.data_editor(
        df_input,
        column_config={
            "年份": st.column_config.TextColumn(disabled=True, width="small"),
            "单枪日均充电量 (kWh)": st.column_config.NumberColumn(min_value=0, max_value=1500, step=10, required=True, format="%d kWh"),
            "运营人数 (人)": st.column_config.NumberColumn(min_value=0, step=1, format="%d 人"),
            "人均年薪 (AED)": st.column_config.NumberColumn(format="%d AED")
        },
        hide_index=True, use_container_width=True,
        # 动态调整表格高度，最多显示约 12 行，超过滚动
        height=int(35 * (min(years_duration, 12) + 2))
    )
    return edited_df

def render_financial_report(df_res, total_capex, payback_year, years_duration):
    st.header("📊 财务评估结果 (Financial Report)")
    
    # 计算关键总计指标
    total_net_profit = df_res["净利润"].sum()
    total_fcf = df_res["自由现金流(FCF)"].sum() + total_capex # 加回Y0的投入，计算运营期总FCF
    total_interest = df_res["资金成本(利息)"].sum()

    m1, m2 = st.columns(2)
    m1.metric("💰 初始总投资 (CAPEX)", f"{total_capex:,.0f} AED", help="建设期总投入")
    m2.metric("💸 运营期总净利 (税后)", f"{total_net_profit:,.0f} AED", help="测算期内累计净利润总和")
    m3, m4 = st.columns(2)
    m3.metric("🌊 运营期自由现金流 (FCF)", f"{total_fcf:,.0f} AED", help="测算期内经营活动产生的净现金流总和 (净利润+折旧)")
    if payback_year and payback_year <= years_duration + 1:
        m4.metric("⏱️ 动态回本期 (Payback)", f"{payback_year:.1f} 年", delta="已回本", delta_color="normal", help="基于累计现金流转正的时间点")
    else:
        m4.metric("⏱️ 动态回本期 (Payback)", "未回本", delta="周期外", delta_color="inverse", help="在测算周期内累计现金流未能转正")
    st.write("")

    tab_chart, tab_table = st.tabs(["📈 累计现金流曲线 (J-Curve)", "📄 详细现金流表 (Cash Flow)"])
    with tab_chart:
        st.area_chart(df_res.set_index("年份")["累计现金流"], color="#2a5298", use_container_width=True)
    with tab_table:
        # 展示更详细的财务列
        cols_to_show = ["营收", "成本(OPEX)", "折旧", "息税前利(EBIT)", "税金", "净利润", "自由现金流(FCF)", "累计现金流"]
        st.dataframe(df_res.style.format("{:,.0f}", subset=cols_to_show), use_container_width=True)

def render_download_section(df_res, edited_df, font_prop):
    st.divider()
    with st.container(border=True):
        st.write("📥 **数据存取中心 (Data Center)**")
        c1, c2 = st.columns(2)
        with c1:
            csv_report = df_res.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📄 下载财务评估报告 (.csv)", csv_report, 'dubai_financial_report_v10.csv', 'text/csv', use_container_width=True)
            
            png_buffer = dataframe_to_png(df_res, font_prop)
            st.download_button("🖼️ 下载表格图片 (.png)", png_buffer, 'dubai_financial_report_v10.png', 'image/png', use_container_width=True, help="生成精美的表格图片，已解决中文乱码问题")
            
        with c2:
            csv_config = edited_df[["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]].to_csv(index=False).encode('utf-8-sig')
            st.download_button("💾 保存当前运营配置 (.csv)", csv_config, 'operation_config_v10.csv', 'text/csv', use_container_width=True)

# ==========================================
# 6. 主控制流 (Main Execution)
# ==========================================
def main():
    # 1. 初始化与安全
    st.set_page_config(**PAGE_CONFIG)
    zh_font = load_custom_font()
    check_password()

    # 2. 渲染结构框架
    render_header()
    # 获取侧边栏配置参数
    backend_inputs = render_sidebar_content(10) # 初始默认10年，后续会由表单覆盖

    # 3. 主界面交互与计算流程
    # 渲染表单并获取输入和提交状态
    all_inputs, form_submitted = render_project_inputs_form(backend_inputs)
    
    # 计算 CAPEX (总是显示)
    total_capex = calculate_capex(all_inputs)
    st.info(f"💰 **Year 0 (建设期) 总投入预估：{total_capex:,.0f} AED** (含全套设备、基建、弱电及杂项)")

    # 渲染动态表格 (总是显示，供用户编辑)
    edited_df = render_dynamic_table(all_inputs['years_duration'])

    # 核心计算与报告展示 (仅在首次加载或表单提交后触发)
    # 使用 session state 记录是否需要重新计算，避免表格编辑时的不必要刷新
    if 'calc_trigger' not in st.session_state:
         st.session_state['calc_trigger'] = False
    
    if form_submitted:
         st.session_state['calc_trigger'] = True

    if st.session_state['calc_trigger']:
        # 执行核心财务模型计算
        df_res, payback_year = calculate_financial_model(edited_df, total_capex, all_inputs)

        # 渲染报告与下载区
        render_financial_report(df_res, total_capex, payback_year, all_inputs['years_duration'])
        render_download_section(df_res, edited_df, zh_font)
    else:
        # 首次加载提示
        st.divider()
        st.info("👉 请在上方设定好项目参数和年度运营数据，然后点击 **“🔄 确认并运行测算”** 按钮生成财务报告。")

if __name__ == "__main__":
    main()