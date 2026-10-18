
import pandas as pd
import streamlit as st

from agentguard.db import connect_mongodb
from agentguard.diagnosis import diagnose_anomaly
from textwrap import dedent
from agentguard.assistant import answer_question
# ============================================================
# 1. PAGE CONFIGURATION AND STYLE
# ============================================================

st.set_page_config(
    page_title="AgentGuard | Infrastructure Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ag-bg: #0b1020;
        --ag-sidebar: #0d1527;
        --ag-card: #111b30;
        --ag-card-hover: #16233a;
        --ag-border: #26334d;
        --ag-text: #edf2ff;
        --ag-muted: #95a4bd;
        --ag-indigo: #818cf8;
        --ag-cyan: #22d3ee;
        --ag-mint: #5eead4;
        --ag-red: #fb7185;
        --ag-amber: #fbbf24;
    }

    .stApp {
        background: var(--ag-bg);
        color: var(--ag-text);
    }

    [data-testid="stAppViewContainer"] {
        background: var(--ag-bg);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: var(--ag-sidebar);
        border-right: 1px solid var(--ag-border);
    }

    [data-testid="stSidebar"] > div:first-child {
        background: var(--ag-sidebar);
    }

    .block-container {
        max-width: 1600px;
        padding-top: 1.7rem;
        padding-bottom: 2.8rem;
    }

    h1, h2, h3 {
        color: var(--ag-text) !important;
        letter-spacing: -0.025em;
    }

    p, label, span {
        color: inherit;
    }

    .ag-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 4px 22px 4px;
        border-bottom: 1px solid var(--ag-border);
        margin-bottom: 20px;
    }

    .ag-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 43px;
        height: 43px;
        border-radius: 13px;
        color: white;
        font-size: 23px;
        font-weight: 800;
        background: linear-gradient(
            140deg, #6366f1 0%, #0891b2 100%
        );
        box-shadow: 0 6px 24px #6366f133;
    }

    .ag-brand-name {
        font-size: 19px;
        font-weight: 750;
        color: var(--ag-text);
        line-height: 1.3;
    }

    .ag-brand-subtitle {
        color: var(--ag-muted);
        font-size: 11px;
        margin-top: 3px;
        letter-spacing: 0.06em;
    }

    .ag-eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.13em;
        color: var(--ag-cyan);
        font-size: 10px;
        font-weight: 800;
        margin-bottom: 7px;
    }

    .ag-page-title {
        color: var(--ag-text);
        font-size: clamp(27px, 3vw, 35px);
        font-weight: 780;
        letter-spacing: -0.04em;
        margin: 0;
    }

    .ag-page-subtitle {
        color: var(--ag-muted);
        font-size: 13px;
        margin-top: 7px;
        line-height: 1.6;
    }

    .ag-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        flex-wrap: wrap;
        margin-bottom: 24px;
    }

    .ag-connection {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid var(--ag-border);
        border-radius: 999px;
        padding: 8px 13px;
        background: var(--ag-card);
        color: var(--ag-muted);
        font-size: 12px;
        white-space: nowrap;
    }

    .ag-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .ag-dot-live {
        background: var(--ag-mint);
        box-shadow: 0 0 11px #5eead466;
    }

    .ag-dot-stale {
        background: var(--ag-amber);
    }

    .ag-dot-error {
        background: var(--ag-red);
    }

    div[data-testid="stMetric"] {
        background: var(--ag-card);
        border: 1px solid var(--ag-border);
        border-radius: 15px;
        padding: 17px 18px;
        min-height: 116px;
    }

    div[data-testid="stMetricLabel"] {
        color: var(--ag-muted);
        font-size: 12px;
    }

    div[data-testid="stMetricValue"] {
        color: var(--ag-text);
        font-size: 27px;
        font-weight: 750;
    }

    div[data-testid="stMetricDelta"] {
        font-size: 11px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--ag-border);
        border-radius: 15px;
        background: var(--ag-card);
    }

    .ag-section-label {
        color: var(--ag-muted);
        text-transform: uppercase;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.12em;
        margin-bottom: 10px;
    }

    .ag-host-name {
        color: var(--ag-text);
        font-weight: 750;
        font-size: 17px;
        overflow-wrap: anywhere;
    }

    .ag-host-meta {
        color: var(--ag-muted);
        font-size: 11px;
        margin-top: 4px;
    }

    .ag-status-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 4px 9px;
        font-size: 10px;
        font-weight: 750;
        letter-spacing: 0.04em;
        border: 1px solid var(--ag-border);
    }

    .ag-status-good {
        color: var(--ag-mint);
        background: #5eead410;
        border-color: #5eead433;
    }

    .ag-status-warning {
        color: var(--ag-amber);
        background: #fbbf2410;
        border-color: #fbbf2433;
    }

    .ag-status-bad {
        color: var(--ag-red);
        background: #fb718510;
        border-color: #fb718533;
    }

    .stButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 650;
        border: 1px solid #6366f177;
        transition: all 0.15s ease;
    }

    .stButton > button[kind="primary"] {
        color: white;
        background: linear-gradient(
            110deg, #6366f1 0%, #4f72d8 100%
        );
    }

    .stButton > button[kind="primary"]:hover {
        border-color: var(--ag-cyan);
        box-shadow: 0 5px 20px #6366f133;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 5px;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label {
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 10px 12px;
        color: #c0cde2;
        transition: all 0.15s ease;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:has(
        input:checked
    ) {
        background: #6366f11a;
        border-color: #818cf855;
        color: white;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: #ffffff09;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--ag-border);
        border-radius: 11px;
        overflow: hidden;
    }

    [data-baseweb="select"] > div {
        background: #101a2d;
        border-color: var(--ag-border);
        border-radius: 9px;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: #101a2d;
        border-color: var(--ag-border);
        border-radius: 9px;
    }

    hr {
        border-color: var(--ag-border);
        margin-top: 20px;
        margin-bottom: 20px;
    }

    .ag-footer {
        border-top: 1px solid var(--ag-border);
        padding-top: 17px;
        margin-top: 28px;
        font-size: 11px;
        color: var(--ag-muted);
    }

    @media (max-width: 800px) {
        .block-container {
            padding: 1rem 1rem 2rem 1rem;
        }

        .ag-page-title {
            font-size: 27px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 2. SIDEBAR NAVIGATION
# ============================================================

st.sidebar.markdown(
    """
    <div class="ag-brand">
        <div class="ag-logo">A</div>
        <div>
            <div class="ag-brand-name">AgentGuard</div>
            <div class="ag-brand-subtitle">
                INFRASTRUCTURE INTELLIGENCE
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.caption("WORKSPACE")

pages = {
    "Overview": "◈  Overview",
    "Metrics": "⌁  Metrics",
    "AI Investigation": "✳  AI Investigation",
    "Ask AgentGuard": "✦  Ask AgentGuard",
    "Anomalies": "△  Anomalies",
    "Actions & Audit": "▤  Actions & Audit",
}

selected_page = st.sidebar.radio(
    "Navigate",
    options=list(pages.keys()),
    format_func=lambda page: pages[page],
    label_visibility="collapsed",
    key="agentguard_page",
)

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    <div style="
        background: #111b30;
        border: 1px solid #26334d;
        border-radius: 12px;
        padding: 13px;
    ">
        <div style="
            color: #22d3ee;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.1em;
        ">COLLECTOR</div>
        <div style="
            color: #edf2ff;
            font-size: 13px;
            font-weight: 700;
            margin-top: 5px;
        ">IBM LinuxONE</div>
        <div style="
            color: #95a4bd;
            font-size: 11px;
            margin-top: 4px;
        ">Metrics stored in MongoDB Atlas</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.caption("AgentGuard Z · Datathon prototype")


# ============================================================
# 3. DATA ACCESS
# ============================================================

TELEMETRY_FIELDS = [
    "host_id",
    "timestamp",
    "cpu_usage_percent",
    "cpu_freq_mhz",
    "cpu_temp_celsius",
    "load_avg_1m",
    "load_avg_5m",
    "load_avg_15m",
    "mem_usage_percent",
    "mem_total_mb",
    "mem_used_mb",
    "mem_available_mb",
    "swap_usage_percent",
    "swap_used_mb",
    "disk_usage_percent",
    "disk_total_gb",
    "disk_used_gb",
    "disk_read_mb_s",
    "disk_write_mb_s",
    "net_download_mbps",
    "net_upload_mbps",
    "net_errors_in",
    "net_errors_out",
    "net_drops_in",
    "net_drops_out",
    "proc_count",
    "active_users",
    "uptime_seconds",
]


def fetch_dashboard_data():
    """Fetch recent telemetry and related records from Atlas."""

    client, database = connect_mongodb()

    try:
        telemetry = list(
            database["telemetry"]
            .find(
                {"schema_version": 1},
                {
                    "_id": 0,
                    **{field: 1 for field in TELEMETRY_FIELDS},
                },
            )
            .sort("timestamp", -1)
            .limit(300)
        )

        telemetry.reverse()

        anomalies = list(
            database["anomalies"]
            .find(
                {},
                {
                    "telemetry_id": 0,
                    "feature_values": 0,
                },
            )
            .sort("detected_at", -1)
            .limit(100)
        )

        diagnoses = list(
            database["diagnoses"]
            .find(
                {},
                {
                    "anomaly_id": 1,
                    "host_id": 1,
                    "created_at": 1,
                    "model": 1,
                    "diagnosis_text": 1,
                    "evidence_record_count": 1,
                    "status": 1,
                },
            )
            .sort("created_at", -1)
            .limit(100)
        )

        actions = list(
            database["actions"]
            .find({})
            .sort("created_at", -1)
            .limit(100)
        )

        return telemetry, anomalies, diagnoses, actions

    finally:
        client.close()


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def display_metric(value, suffix="", decimals=1):
    if value is None:
        return "—"

    try:
        if pd.isna(value):
            return "—"

        return f"{float(value):,.{decimals}f}{suffix}"

    except (TypeError, ValueError):
        return "—"


def get_dataframe(telemetry):
    dataframe = pd.DataFrame(telemetry)

    if dataframe.empty:
        return dataframe

    dataframe["timestamp"] = pd.to_datetime(
        dataframe["timestamp"],
        utc=True,
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=["timestamp", "host_id"]
    )

    return dataframe.sort_values("timestamp").reset_index(
        drop=True
    )


def telemetry_age_seconds(timestamp):
    if timestamp is None:
        return None

    timestamp = pd.to_datetime(
        timestamp,
        utc=True,
        errors="coerce",
    )

    if pd.isna(timestamp):
        return None

    now = pd.Timestamp.now(tz="UTC")
    return max(0.0, (now - timestamp).total_seconds())


def recent_anomaly_count(anomalies, minutes=60):
    if not anomalies:
        return 0

    timestamps = pd.to_datetime(
        [item.get("detected_at") for item in anomalies],
        utc=True,
        errors="coerce",
    )

    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(
        minutes=minutes
    )

    return int((timestamps >= cutoff).sum())


def prepare_anomaly_table(anomalies):
    rows = []

    for anomaly in anomalies:
        rows.append(
            {
                "Host": anomaly.get("host_id", "Unknown"),
                "Anomaly Time": anomaly.get("timestamp"),
                "Detected At": anomaly.get("detected_at"),
                "Score": anomaly.get("anomaly_score"),
                "Status": anomaly.get("status", "detected"),
            }
        )

    return pd.DataFrame(rows)


def get_anomaly_label(anomaly):
    score = anomaly.get("anomaly_score")

    if score is None:
        score_text = "N/A"
    else:
        score_text = f"{score:.4f}"

    timestamp = anomaly.get("timestamp")

    if timestamp is not None:
        timestamp_text = str(timestamp)
    else:
        timestamp_text = "Unknown time"

    return (
        f"{anomaly.get('host_id', 'Unknown host')} | "
        f"Score {score_text} | {timestamp_text}"
    )


def get_saved_diagnosis(diagnoses, anomaly_id):
    for diagnosis in diagnoses:
        saved_anomaly_id = diagnosis.get("anomaly_id")

        if str(saved_anomaly_id) == str(anomaly_id):
            return diagnosis

    return None


def page_header(title, subtitle, freshness=None):
    if freshness is None:
        status_class = "ag-dot-stale"
        status_text = "Awaiting telemetry"
    elif freshness <= 30:
        status_class = "ag-dot-live"
        status_text = "Live telemetry"
    else:
        status_class = "ag-dot-stale"
        status_text = "Telemetry is stale"

    header_html = (
        '<div class="ag-topbar">'
        '<div>'
        '<div class="ag-eyebrow">'
        'AGENTGUARD / INFRASTRUCTURE'
        '</div>'
        f'<h1 class="ag-page-title">{title}</h1>'
        f'<div class="ag-page-subtitle">{subtitle}</div>'
        '</div>'
        '<div class="ag-connection">'
        f'<span class="ag-dot {status_class}"></span>'
        f'<span>{status_text}</span>'
        '<span style="margin-left: 4px;">&bull; Atlas</span>'
        '</div>'
        '</div>'
    )

    st.markdown(
        header_html,
        unsafe_allow_html=True,
    )

# ============================================================
# 5. OVERVIEW PAGE
# ============================================================

def render_overview(dataframe, anomalies, diagnoses):
    latest_time = None

    if not dataframe.empty:
        latest_time = dataframe["timestamp"].max()

    freshness = telemetry_age_seconds(latest_time)

    page_header(
        "Infrastructure Overview",
        "A live operational view of server health, resource usage, "
        "and ML-detected anomalies.",
        freshness,
    )

    if dataframe.empty:
        st.info(
            "No usable telemetry found. Start the LinuxONE "
            "collector to send records to Atlas."
        )
        return

    numeric_cpu = pd.to_numeric(
        dataframe["cpu_usage_percent"],
        errors="coerce",
    )

    numeric_memory = pd.to_numeric(
        dataframe["mem_usage_percent"],
        errors="coerce",
    )

    host_count = dataframe["host_id"].nunique()
    alert_count = recent_anomaly_count(anomalies, 60)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Hosts Observed", host_count)
    col2.metric("Anomalies · 1 hour", alert_count)
    col3.metric(
        "Average CPU",
        display_metric(numeric_cpu.mean(), "%"),
    )
    col4.metric(
        "Average Memory",
        display_metric(numeric_memory.mean(), "%"),
    )

    st.markdown("### Host Inventory")
    st.caption(
        "Status is based on telemetry freshness, not a "
        "full infrastructure health check."
    )

    latest_per_host = (
        dataframe.sort_values("timestamp")
        .groupby("host_id", as_index=False)
        .tail(1)
        .sort_values("host_id")
    )

    columns = st.columns(
        min(3, max(1, len(latest_per_host)))
    )

    for index, (_, host) in enumerate(
        latest_per_host.iterrows()
    ):
        age = telemetry_age_seconds(host["timestamp"])

        if age is not None and age <= 30:
            status_text = "RECEIVING DATA"
            status_class = "ag-status-good"
        else:
            status_text = "STALE"
            status_class = "ag-status-warning"

        column = columns[index % len(columns)]

        with column:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="ag-section-label">
                        MONITORED HOST
                    </div>
                    <div class="ag-host-name">
                        {host['host_id']}
                    </div>
                    <div style="margin: 11px 0;">
                        <span class="ag-status-pill {status_class}">
                            {status_text}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.metric(
                    "CPU",
                    display_metric(
                        host.get("cpu_usage_percent"), "%"
                    ),
                )

                st.metric(
                    "Memory",
                    display_metric(
                        host.get("mem_usage_percent"), "%"
                    ),
                )

                st.metric(
                    "Disk",
                    display_metric(
                        host.get("disk_usage_percent"), "%"
                    ),
                )

                st.caption(
                    "Last received: "
                    + host["timestamp"].strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    )
                )

    st.markdown("### Performance Trends")

    recent = dataframe.tail(120).set_index("timestamp")

    left, right = st.columns(2)

    with left:
        st.markdown("**CPU and Memory**")

        cpu_memory_columns = [
            field
            for field in [
                "cpu_usage_percent",
                "mem_usage_percent",
            ]
            if field in recent.columns
        ]

        if cpu_memory_columns:
            st.line_chart(
                recent[cpu_memory_columns],
                height=270,
            )

    with right:
        st.markdown("**Network Throughput**")

        network_columns = [
            field
            for field in [
                "net_download_mbps",
                "net_upload_mbps",
            ]
            if field in recent.columns
        ]

        if network_columns:
            st.line_chart(
                recent[network_columns],
                height=270,
            )
        else:
            st.info("Network throughput is not available.")

    left, right = st.columns(2)

    with left:
        st.markdown("**Recent ML Anomalies**")

        if anomalies:
            st.dataframe(
                prepare_anomaly_table(anomalies).head(8),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No anomaly records have been saved.")

    with right:
        st.markdown("**Latest AI Investigation**")

        if diagnoses:
            latest_diagnosis = diagnoses[0]

            st.caption(
                f"Host: {latest_diagnosis.get('host_id', 'Unknown')}"
            )

            st.markdown(
                (latest_diagnosis.get("diagnosis_text") or "")[:900]
            )

            if len(latest_diagnosis.get("diagnosis_text") or "") > 900:
                st.caption("Open AI Investigation to view the full result.")
        else:
            st.info(
                "No saved diagnoses yet. Open AI Investigation "
                "to investigate an anomaly."
            )


# ============================================================
# 6. METRICS PAGE
# ============================================================

def render_metrics(dataframe):
    freshness = None

    if not dataframe.empty:
        freshness = telemetry_age_seconds(
            dataframe["timestamp"].max()
        )

    page_header(
        "Metrics Explorer",
        "Explore recent CPU, memory, disk, process, and network "
        "telemetry stored in MongoDB Atlas.",
        freshness,
    )

    if dataframe.empty:
        st.info("No telemetry data is available.")
        return

    hosts = sorted(
        dataframe["host_id"].dropna().unique().tolist()
    )

    selected_host = st.selectbox(
        "Select monitored host",
        hosts,
        key="metrics_host",
    )

    host_df = dataframe[
        dataframe["host_id"] == selected_host
    ].copy()

    st.caption(
        f"Showing {len(host_df)} of the most recent available "
        f"records for {selected_host}."
    )

    if host_df.empty:
        st.info("No records are available for this host.")
        return

    latest = host_df.iloc[-1]

    cols = st.columns(4)

    cols[0].metric(
        "CPU",
        display_metric(
            latest.get("cpu_usage_percent"), "%"
        ),
    )
    cols[1].metric(
        "Memory",
        display_metric(
            latest.get("mem_usage_percent"), "%"
        ),
    )
    cols[2].metric(
        "Disk",
        display_metric(
            latest.get("disk_usage_percent"), "%"
        ),
    )
    cols[3].metric(
        "Processes",
        display_metric(latest.get("proc_count")),
    )

    chart = host_df.set_index("timestamp")

    st.markdown("### Resource Utilization")

    resource_fields = [
        field
        for field in [
            "cpu_usage_percent",
            "mem_usage_percent",
            "disk_usage_percent",
        ]
        if field in chart.columns
    ]

    if resource_fields:
        st.line_chart(chart[resource_fields], height=320)

    left, right = st.columns(2)

    with left:
        st.markdown("### Network")

        fields = [
            field
            for field in [
                "net_download_mbps",
                "net_upload_mbps",
            ]
            if field in chart.columns
        ]

        if fields:
            st.line_chart(chart[fields], height=280)
        else:
            st.info("Network throughput is unavailable.")

    with right:
        st.markdown("### Disk I/O")

        fields = [
            field
            for field in [
                "disk_read_mb_s",
                "disk_write_mb_s",
            ]
            if field in chart.columns
        ]

        if fields:
            st.line_chart(chart[fields], height=280)
        else:
            st.info("Disk I/O readings are unavailable.")

    st.markdown("### Detailed Telemetry")

    display_columns = [
        field
        for field in [
            "timestamp",
            "host_id",
            "cpu_usage_percent",
            "cpu_freq_mhz",
            "mem_usage_percent",
            "mem_available_mb",
            "disk_usage_percent",
            "disk_read_mb_s",
            "disk_write_mb_s",
            "net_download_mbps",
            "net_upload_mbps",
            "load_avg_1m",
            "proc_count",
            "uptime_seconds",
        ]
        if field in host_df.columns
    ]

    st.dataframe(
        host_df[display_columns].sort_values(
            "timestamp", ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 7. ANOMALY CENTER
# ============================================================

def render_anomalies(anomalies):
    page_header(
        "Anomaly Center",
        "Review unusual observations detected by Isolation Forest.",
    )

    if not anomalies:
        st.info(
            "No anomalies have been stored yet. Ensure monitor.py "
            "is running and processing new telemetry."
        )
        return

    count = len(anomalies)
    recent_count = recent_anomaly_count(anomalies, 60)

    col1, col2, col3 = st.columns(3)
    col1.metric("Stored Detections", count)
    col2.metric("Detected · 1 hour", recent_count)
    col3.metric(
        "Distinct Hosts",
        len(
            {
                item.get("host_id")
                for item in anomalies
                if item.get("host_id")
            }
        ),
    )

    st.markdown("### Detection History")

    table = prepare_anomaly_table(anomalies)

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Isolation Forest flags unusual observations; it does not "
        "establish that a system failure or attack occurred."
    )


# ============================================================
# 8. AI INVESTIGATION
# ============================================================

def render_ai_investigation(anomalies, diagnoses):
    page_header(
        "AI Investigation",
        "Use Gemini to interpret a detected anomaly against recent "
        "telemetry and generate evidence-based recommendations.",
    )

    if not anomalies:
        st.info(
            "There are no anomaly records available to investigate. "
            "Run the monitoring process and wait for a detection."
        )
        if diagnoses:
            st.markdown("### Previous Investigations")

            for item in diagnoses[:5]:
                host = item.get("host_id", "Unknown host")
                created_at = item.get("created_at", "Unknown time")
                diagnosis_text = dedent(
                    item.get("diagnosis_text") or ""
                ).strip()

                with st.expander(f"{host} · {created_at}"):
                    if diagnosis_text:
                        st.markdown(diagnosis_text)
                    else:
                        st.info("No diagnosis text was saved for this record.")

        return

    anomaly_lookup = {
        str(item["_id"]): item
        for item in anomalies
        if "_id" in item
    }

    if not anomaly_lookup:
        st.warning("No valid anomaly IDs were found.")
        return

    selected_id = st.selectbox(
        "Select an anomaly",
        options=list(anomaly_lookup.keys()),
        format_func=lambda item_id: get_anomaly_label(
            anomaly_lookup[item_id]
        ),
        key="investigation_anomaly_id",
    )

    anomaly = anomaly_lookup[selected_id]

    with st.container(border=True):
        st.markdown("### Selected Event")

        left, right = st.columns(2)

        left.metric(
            "Anomaly Score",
            display_metric(
                anomaly.get("anomaly_score"),
                decimals=4,
            ),
        )

        right.metric(
            "Host",
            anomaly.get("host_id", "Unknown"),
        )

        st.caption(
            "This score represents the model's decision function; "
            "it is not a probability of compromise."
        )

    if st.button(
        "✳  Investigate with AI",
        type="primary",
        use_container_width=True,
        key="run_ai_investigation",
    ):
        with st.spinner(
            "Analyzing anomaly evidence with Gemini..."
        ):
            try:
                result = diagnose_anomaly(selected_id)

                st.session_state["agentguard_diagnosis"] = result
                st.session_state["agentguard_diagnosis_id"] = (
                    selected_id
                )

                st.success("Investigation completed and saved.")

            except Exception as error:
                st.error(
                    f"Diagnosis failed: {type(error).__name__}: {error}"
                )

    saved_result = None

    session_result = st.session_state.get(
        "agentguard_diagnosis"
    )

    session_anomaly_id = st.session_state.get(
        "agentguard_diagnosis_id"
    )

    if (
        session_result
        and str(session_anomaly_id) == selected_id
    ):
        saved_result = session_result
    else:
        stored_diagnosis = get_saved_diagnosis(
            diagnoses,
            anomaly["_id"],
        )

        if stored_diagnosis:
            saved_result = {
                "diagnosis_text": stored_diagnosis.get(
                    "diagnosis_text", ""
                )
            }

    if saved_result:
        st.markdown("### Investigation Findings")

        st.markdown(
            saved_result.get("diagnosis_text", "")
        )

        st.caption(
            "AI findings are hypotheses based on available evidence. "
            "Verify recommendations before taking action."
        )

    else:
        st.info(
            "No saved diagnosis for this anomaly yet. Click "
            "'Investigate with AI' to generate one."
        )

    if diagnoses:
        st.markdown("### Previous Investigations")

        for item in diagnoses[:5]:
            with st.expander(
                f"{item.get('host_id', 'Unknown host')} · "
                f"{item.get('created_at', 'Unknown time')}"
            ):
                st.markdown(
                    item.get("diagnosis_text", "")
                )


# ============================================================
# 9. ACTIONS AND AUDIT
# ============================================================

def render_actions(actions):
    page_header(
        "Actions & Audit",
        "Review recorded corrective-action decisions and their results.",
    )

    st.warning(
        "The approval and execution workflow is not yet wired to the "
        "dashboard. This section displays recorded action documents "
        "only; it does not execute or approve system commands."
    )

    if not actions:
        st.info(
            "No action audit records have been created yet. "
            "We will populate this page when the controlled action "
            "workflow is implemented."
        )
        return

    rows = []

    for action in actions:
        rows.append(
            {
                "Host": action.get("host_id", "Unknown"),
                "Action": action.get(
                    "action_name",
                    action.get("action", "Unknown"),
                ),
                "Decision": action.get(
                    "decision",
                    action.get("status", "Unknown"),
                ),
                "Requested At": action.get(
                    "created_at",
                    action.get("timestamp"),
                ),
                "Result": action.get("result", "Not recorded"),
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


def render_ask_agentguard(dataframe):
    page_header(
        "Ask AgentGuard",
        "Ask questions about server health, anomalies, and "
        "recommended troubleshooting steps.",
    )

    # Show basic context for the current conversation.
    col1, col2, col3 = st.columns(3)

    col1.metric("Recent Records Loaded", len(dataframe))

    if not dataframe.empty:
        latest_time = dataframe["timestamp"].max()
        col2.metric(
            "Latest Telemetry",
            latest_time.strftime("%H:%M:%S UTC"),
        )

        col3.metric(
            "Monitored Hosts",
            dataframe["host_id"].nunique(),
        )
    else:
        col2.metric("Latest Telemetry", "Unavailable")
        col3.metric("Monitored Hosts", 0)

    st.divider()

    st.markdown("### Conversation")
    st.caption(
        "Ask about current metrics, previous anomalies, "
        "or the next troubleshooting step."
    )

    if "agentguard_chat_history" not in st.session_state:
        st.session_state["agentguard_chat_history"] = [
            {
                "role": "assistant",
                "content": (
                    "Hi! I'm AgentGuard. I can help you understand "
                    "the monitoring data currently stored in Atlas. "
                    "Ask me about server health, detected anomalies, "
                    "or what to investigate next."
                ),
            }
        ]

    # Display previous messages.
    for message in st.session_state["agentguard_chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept the user's question.
    question = st.chat_input(
        "Ask AgentGuard about your server...",
        key="agentguard_question",
    )

    if question:
        previous_history = list(
            st.session_state["agentguard_chat_history"]
        )

        st.session_state["agentguard_chat_history"].append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner(
                "AgentGuard is analyzing the latest evidence..."
            ):
                try:
                    answer = answer_question(
                        question,
                        previous_history,
                    )

                except Exception as error:
                    answer = (
                        f"**Unable to answer right now.**\n\n"
                        f"Error: {type(error).__name__}: {error}"
                    )

            st.markdown(answer)

        st.session_state["agentguard_chat_history"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

    if st.button(
        "Clear conversation",
        key="clear_agentguard_chat",
    ):
        st.session_state["agentguard_chat_history"] = [
            {
                "role": "assistant",
                "content": (
                    "Conversation cleared. What would you like "
                    "to investigate?"
                ),
            }
        ]
        st.rerun()
# ============================================================
# 10. REFRESHABLE MAIN VIEW
# ============================================================

@st.fragment(run_every=15)
def render_current_page(page):
    try:
        telemetry, anomalies, diagnoses, actions = (
            fetch_dashboard_data()
        )

        dataframe = get_dataframe(telemetry)

    except Exception as error:
        page_header(
            page,
            "Unable to load monitoring data.",
        )

        st.error(
            f"Database error: {type(error).__name__}: {error}"
        )

        return

    if page == "Overview":
        render_overview(dataframe, anomalies, diagnoses)

    elif page == "Metrics":
        render_metrics(dataframe)

    elif page == "AI Investigation":
        render_ai_investigation(anomalies, diagnoses)
        
    elif page == "Ask AgentGuard":
        render_ask_agentguard(dataframe)

    elif page == "Anomalies":
        render_anomalies(anomalies)

    elif page == "Actions & Audit":
        render_actions(actions)

    st.markdown(
        """
        <div class="ag-footer">
            AGENTGUARD Z &nbsp; · &nbsp;
            IBM LINUXONE &nbsp; · &nbsp;
            MONGODB ATLAS
            <span style="float:right;">
                Refresh interval: 5 seconds
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_current_page(selected_page)
