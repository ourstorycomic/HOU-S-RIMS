# API/main.py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64
import numpy as np
import re
import json
import os

# --- CAU HINH ---
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Tahoma', 'Segoe UI', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# --- LOAD SURVEY MAPPING ---
_MAP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'data.json')
_SURVEY_MAP = {}
try:
    with open(_MAP_PATH, encoding='utf-8') as _f:
        _SURVEY_MAP = json.load(_f)
except Exception:
    _SURVEY_MAP = {}

def get_col_mapping(col):
    """Return {raw_value: label_text} for a column, or {} if not found."""
    col = str(col).strip()
    if col in _SURVEY_MAP:
        return _SURVEY_MAP[col]
    # Try stripping brackets that appear in some column names
    col_stripped = col.strip('[]').strip()
    if col_stripped in _SURVEY_MAP:
        return _SURVEY_MAP[col_stripped]
    return {}

def apply_col_mapping(index, col_mapping):
    """Return list of short display codes and list of full label strings."""
    if not col_mapping:
        return list(index), []
    short_codes = []
    legend_lines = []
    used = set()
    for v in index:
        mapped = col_mapping.get(str(v))
        code = str(v)
        short_codes.append(code)
        if mapped and str(v) not in used:
            legend_lines.append(f"{code} = {mapped}")
            used.add(str(v))
    return short_codes, legend_lines

def add_mapping_legend(fig, ax, legend_lines, title="Chú giải"):
    """Add a text info panel to the right of the axes."""
    if not legend_lines:
        return
    text = title + "\n" + "\n".join(legend_lines)
    fig.text(
        0.98, 0.98, text,
        transform=fig.transFigure,
        fontsize=9,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f8f8',
                  edgecolor='#cccccc', alpha=0.95),
        fontfamily='Arial'
    )
    # Shrink axes to make room
    pos = ax.get_position()
    ax.set_position([pos.x0, pos.y0, pos.width * 0.72, pos.height])

LIKERT_ORDER = [
    "hoan toan khong dong y", "rat khong dong y", "khong dong y", "khong",
    "khong biet", "chua biet", "phan van", "binh thuong", "trung binh",
    "trung lap", "dong y mot phan", "tam dong y", "dong y", "kha dong y",
    "rat dong y", "hoan toan dong y",
    "khong biet gi", "biet rat it", "biet mot chut", "biet", "biet ro", "biet rat ro",
    "hoan toan khong quan trong", "khong quan trong", "quan trong", "rat quan trong",
    "khong bao gio", "hiem khi", "thinh thoang", "thuong xuyen", "luon luon",
    "nam 1", "nam thu 1", "nam 2", "nam thu 2", "nam 3", "nam thu 3", "nam 4", "nam thu 4",
]

def _normalize(s):
    import unicodedata
    s = unicodedata.normalize('NFD', str(s).lower().strip())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s

LIKERT_NORM = [_normalize(k) for k in LIKERT_ORDER]
PALETTE_MAIN = "viridis"
PALETTE_MULTI = "Spectral"

def truncate_label(text, limit=28):
    s = str(text).strip()
    return s[:limit] + "..." if len(s) > limit else s

def sort_values_smart(index):
    norm_idx = [_normalize(str(v)) for v in index]
    scores = []
    for nv in norm_idx:
        found = -1
        for i, key in enumerate(LIKERT_NORM):
            if key in nv or nv in key:
                found = i
                break
        scores.append(found)
    if sum(1 for s in scores if s >= 0) >= max(1, len(index) * 0.3):
        paired = sorted(zip(scores, index), key=lambda x: (x[0] if x[0] >= 0 else 999, str(x[1])))
        return [v for _, v in paired]
    try:
        return sorted(index, key=lambda x: float(str(x).replace(',', '.')))
    except Exception:
        pass
    return list(index)

def get_value_counts(series, top_n=8):
    vc = series.dropna().astype(str).str.strip()
    vc = vc[vc.str.len() > 0]
    counts = vc.value_counts()
    if len(counts) > top_n:
        counts = counts.head(top_n)
    sorted_idx = sort_values_smart(counts.index)
    return counts.reindex(sorted_idx, fill_value=0)

def _fig_to_b64(fig):
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=110, bbox_inches="tight")
    b.seek(0)
    plt.close(fig)
    return f"data:image/png;base64,{base64.b64encode(b.read()).decode('utf-8')}"

def add_bar_labels(ax):
    for container in ax.containers:
        labels = []
        for bar in container:
            h = bar.get_height() if hasattr(bar, 'get_height') else bar.get_width()
            labels.append(str(int(h)) if h > 0 else "")
        ax.bar_label(container, labels=labels, padding=3, fontsize=9)

# 1. COT DUC
def plot_column(df, cols):
    if len(cols) == 1:
        col = cols[0]
        counts = get_value_counts(df[col])
        col_map = get_col_mapping(col)
        short_codes, legend_lines = apply_col_mapping(counts.index, col_map)
        palette = sns.color_palette(PALETTE_MAIN, len(counts))
        fig, ax = plt.subplots(figsize=(max(8, len(counts) * 1.3), 7))
        bars = ax.bar(short_codes, counts.values, color=palette, edgecolor='white', width=0.6)
        ax.set_ylabel("So luong phan hoi", fontsize=11)
        ax.set_title(f"Phan bo: {truncate_label(col, 50)}", fontweight='bold', pad=15)
        ax.set_xticklabels(short_codes, rotation=0, ha='center', fontsize=11)
        for bar, v in zip(bars, counts.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.3,
                    str(int(v)), ha='center', va='bottom', fontweight='bold', fontsize=10)
        add_mapping_legend(fig, ax, legend_lines)
    else:
        counts_list = {}
        for c in cols:
            vc = get_value_counts(df[c])
            counts_list[truncate_label(c, 22)] = vc
        all_vals = []
        for vc in counts_list.values():
            for v in vc.index:
                if v not in all_vals: all_vals.append(v)
        df_chart = pd.DataFrame({col: vc.reindex(all_vals, fill_value=0) for col, vc in counts_list.items()})
        palette = sns.color_palette(PALETTE_MULTI, len(df_chart))
        fig, ax = plt.subplots(figsize=(max(10, len(df_chart.columns)*1.5), 8))
        df_chart.T.plot(kind='bar', ax=ax, color=palette, edgecolor='white', width=0.75)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha='right', fontsize=9)
        ax.set_ylabel("So luong phan hoi", fontsize=11)
        ax.set_title("So sanh phan bo cac cau hoi", fontweight='bold', pad=15)
        ax.legend(title="Muc do", bbox_to_anchor=(1.01,1), loc='upper left', frameon=False, fontsize=9)
        add_bar_labels(ax)
    plt.tight_layout()
    return fig

# 2. THANH NGANG
def plot_bar(df, cols):
    if len(cols) == 1:
        col = cols[0]
        counts = get_value_counts(df[col])
        col_map = get_col_mapping(col)
        short_codes, legend_lines = apply_col_mapping(counts.index, col_map)
        palette = sns.color_palette(PALETTE_MAIN, len(counts))
        fig, ax = plt.subplots(figsize=(10, max(5, len(counts)*0.7+1)))
        bars = ax.barh(short_codes, counts.values, color=palette, edgecolor='white', height=0.6)
        ax.set_xlabel("So luong phan hoi", fontsize=11)
        ax.set_title(f"Phan bo: {truncate_label(col, 50)}", fontweight='bold', pad=15)
        for bar, v in zip(bars, counts.values):
            ax.text(bar.get_width()+0.2, bar.get_y()+bar.get_height()/2,
                    str(int(v)), va='center', fontweight='bold', fontsize=10)
        ax.invert_yaxis()
        add_mapping_legend(fig, ax, legend_lines)
    else:
        counts_list = {}
        for c in cols:
            vc = get_value_counts(df[c])
            counts_list[truncate_label(c, 25)] = vc
        all_vals = []
        for vc in counts_list.values():
            for v in vc.index:
                if v not in all_vals: all_vals.append(v)
        df_chart = pd.DataFrame({col: vc.reindex(all_vals, fill_value=0) for col, vc in counts_list.items()})
        palette = sns.color_palette(PALETTE_MULTI, len(df_chart))
        fig, ax = plt.subplots(figsize=(10, max(6, len(df_chart.columns)*0.9+2)))
        df_chart.T.plot(kind='barh', ax=ax, color=palette, edgecolor='white', width=0.75)
        ax.set_xlabel("So luong phan hoi", fontsize=11)
        ax.set_title("So sanh phan bo cac cau hoi", fontweight='bold', pad=15)
        ax.legend(title="Muc do", bbox_to_anchor=(1.01,1), loc='upper left', frameon=False, fontsize=9)
        ax.invert_yaxis()
    plt.tight_layout()
    return fig

# 3. TRON
def plot_pie(df, cols):
    col = cols[0]
    counts = get_value_counts(df[col], top_n=10)
    col_map = get_col_mapping(col)
    short_codes, legend_lines = apply_col_mapping(counts.index, col_map)
    # Use mapped label if available, else short code
    display_labels = []
    for code in short_codes:
        mapped = col_map.get(str(code))
        display_labels.append(mapped if mapped else code)
    palette = sns.color_palette(PALETTE_MULTI, len(counts))
    fig, ax = plt.subplots(figsize=(10, 7))
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=None, autopct='%1.1f%%',
        startangle=90, colors=palette,
        pctdistance=0.78, wedgeprops={'edgecolor':'white','linewidth':1.5})
    for at in autotexts:
        at.set_fontsize(9); at.set_fontweight('bold')
    ax.legend(wedges, [f"{truncate_label(l,30)} ({int(v)})" for l,v in zip(display_labels, counts.values)],
              loc='center left', bbox_to_anchor=(1,0.5), frameon=False, fontsize=10)
    ax.set_title(truncate_label(col, 55), fontweight='bold', pad=15)
    plt.tight_layout()
    return fig

# 4. VONG / DONUT
def plot_donut(df, cols):
    col = cols[0]
    counts = get_value_counts(df[col], top_n=10)
    col_map = get_col_mapping(col)
    short_codes, legend_lines = apply_col_mapping(counts.index, col_map)
    display_labels = []
    for code in short_codes:
        mapped = col_map.get(str(code))
        display_labels.append(mapped if mapped else code)
    palette = sns.color_palette(PALETTE_MULTI, len(counts))
    fig, ax = plt.subplots(figsize=(10, 7))
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=None, autopct='%1.1f%%',
        startangle=90, colors=palette,
        pctdistance=0.80, wedgeprops={'edgecolor':'white','linewidth':2,'width':0.55})
    for at in autotexts:
        at.set_fontsize(9); at.set_fontweight('bold')
    ax.text(0, 0, f"n={counts.sum()}", ha='center', va='center', fontsize=13, fontweight='bold', color='#333')
    ax.legend(wedges, [f"{truncate_label(l,30)} ({int(v)})" for l,v in zip(display_labels, counts.values)],
              loc='center left', bbox_to_anchor=(1,0.5), frameon=False, fontsize=10)
    ax.set_title(truncate_label(col, 55), fontweight='bold', pad=15)
    plt.tight_layout()
    return fig

def _get_shared_mapping(cols, df):
    """Get a shared mapping for multiple columns (first col's mapping used for value labels)."""
    for c in cols:
        m = get_col_mapping(c)
        if m:
            return m
    return {}

# 5. GHEP NHOM
def plot_grouped(df, cols):
    counts_list = {}
    for c in cols:
        vc = get_value_counts(df[c], top_n=7)
        counts_list[truncate_label(c, 22)] = vc
    all_vals = []
    for vc in counts_list.values():
        for v in vc.index:
            if v not in all_vals: all_vals.append(v)
    col_map = _get_shared_mapping(cols, df)
    # Map column index (value labels) using mapping
    mapped_vals = [col_map.get(str(v), str(v)) for v in all_vals]
    df_chart = pd.DataFrame({col: vc.reindex(all_vals, fill_value=0) for col, vc in counts_list.items()})
    df_chart.index = mapped_vals
    df_plot = df_chart.T
    palette = sns.color_palette(PALETTE_MULTI, len(df_plot.columns))
    fig, ax = plt.subplots(figsize=(max(10, len(df_plot)*1.4), 8))
    df_plot.plot(kind='bar', ax=ax, color=palette, edgecolor='white', width=0.8)
    ax.set_xticklabels([truncate_label(l, 20) for l in df_plot.index], rotation=35, ha='right', fontsize=9)
    ax.set_ylabel("So luong phan hoi", fontsize=11)
    ax.set_title("Bieu do Cot Ghep Nhom", fontweight='bold', pad=15)
    ax.legend(title="Muc do", bbox_to_anchor=(1.01,1), loc='upper left', frameon=False, fontsize=9)
    add_bar_labels(ax)
    plt.tight_layout()
    return fig

# 6. COT CHONG DOC
def plot_stacked(df, cols):
    counts_list = {}
    for c in cols:
        vc = get_value_counts(df[c], top_n=7)
        counts_list[truncate_label(c, 22)] = vc
    all_vals = []
    for vc in counts_list.values():
        for v in vc.index:
            if v not in all_vals: all_vals.append(v)
    col_map = _get_shared_mapping(cols, df)
    mapped_vals = [col_map.get(str(v), str(v)) for v in all_vals]
    df_chart = pd.DataFrame({col: vc.reindex(all_vals, fill_value=0) for col, vc in counts_list.items()})
    df_chart.index = mapped_vals
    totals = df_chart.T.sum(axis=1).replace(0, 1)
    df_pct = (df_chart.T.div(totals, axis=0) * 100)
    palette = sns.color_palette(PALETTE_MULTI, len(df_pct.columns))
    fig, ax = plt.subplots(figsize=(max(10, len(df_pct)*1.4), 8))
    df_pct.plot(kind='bar', stacked=True, ax=ax, color=palette, edgecolor='white', width=0.7)
    ax.set_xticklabels([truncate_label(l, 20) for l in df_pct.index], rotation=35, ha='right', fontsize=9)
    ax.set_ylabel("Ti le (%)", fontsize=11)
    ax.set_ylim(0, 110)
    ax.set_title("Bieu do Cot Chong (%)", fontweight='bold', pad=15)
    ax.legend(title="Muc do", bbox_to_anchor=(1.01,1), loc='upper left', frameon=False, fontsize=9)
    for container in ax.containers:
        labels_ = [f'{v:.0f}%' if v >= 7 else '' for v in container.datavalues]
        ax.bar_label(container, labels=labels_, label_type='center', fontsize=9, fontweight='bold')
    plt.tight_layout()
    return fig

# 7. COT CHONG NGANG
def plot_stacked_h(df, cols):
    counts_list = {}
    for c in cols:
        vc = get_value_counts(df[c], top_n=7)
        counts_list[truncate_label(c, 30)] = vc
    all_vals = []
    for vc in counts_list.values():
        for v in vc.index:
            if v not in all_vals: all_vals.append(v)
    col_map = _get_shared_mapping(cols, df)
    mapped_vals = [col_map.get(str(v), str(v)) for v in all_vals]
    df_chart = pd.DataFrame({col: vc.reindex(all_vals, fill_value=0) for col, vc in counts_list.items()})
    df_chart.index = mapped_vals
    totals = df_chart.T.sum(axis=1).replace(0, 1)
    df_pct = (df_chart.T.div(totals, axis=0) * 100)
    palette = sns.color_palette(PALETTE_MULTI, len(df_pct.columns))
    fig, ax = plt.subplots(figsize=(11, max(5, len(df_pct)*0.8+1)))
    df_pct.plot(kind='barh', stacked=True, ax=ax, color=palette, edgecolor='white', width=0.7)
    ax.set_xlabel("Ti le (%)", fontsize=11)
    ax.set_xlim(0, 110)
    ax.set_title("Bieu do Cot Chong Ngang (%)", fontweight='bold', pad=15)
    ax.legend(title="Muc do", bbox_to_anchor=(1.01,1), loc='upper left', frameon=False, fontsize=9)
    ax.invert_yaxis()
    for container in ax.containers:
        labels_ = [f'{v:.0f}%' if v >= 7 else '' for v in container.datavalues]
        ax.bar_label(container, labels=labels_, label_type='center', fontsize=9, fontweight='bold')
    plt.tight_layout()
    return fig

# 8. DUONG
def plot_line(df, cols):
    palette = sns.color_palette(PALETTE_MULTI, len(cols))
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, col in enumerate(cols):
        counts = get_value_counts(df[col], top_n=10)
        labels = [truncate_label(l, 18) for l in counts.index]
        ax.plot(labels, counts.values, marker='o', linewidth=2.2,
                color=palette[i], label=truncate_label(col, 25))
        for x, y in zip(labels, counts.values):
            ax.annotate(str(int(y)), (x, y), textcoords="offset points",
                        xytext=(0,8), ha='center', fontsize=9)
    ax.set_ylabel("So luong phan hoi", fontsize=11)
    ax.set_title("Bieu do Duong", fontweight='bold', pad=15)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha='right', fontsize=9)
    if len(cols) > 1:
        ax.legend(bbox_to_anchor=(1.01,1), loc='upper left', frameon=False, fontsize=9)
    plt.tight_layout()
    return fig

# 9. MIEN
def plot_area(df, cols):
    palette = sns.color_palette(PALETTE_MULTI, len(cols))
    fig, ax = plt.subplots(figsize=(12, 6))
    all_vals = []
    counts_dict = {}
    for col in cols:
        vc = get_value_counts(df[col], top_n=10)
        counts_dict[col] = vc
        for v in vc.index:
            if v not in all_vals: all_vals.append(v)
    x = range(len(all_vals))
    labels = [truncate_label(str(v), 18) for v in all_vals]
    for i, col in enumerate(cols):
        y = [counts_dict[col].get(v, 0) for v in all_vals]
        ax.fill_between(x, y, alpha=0.35, color=palette[i])
        ax.plot(x, y, marker='o', linewidth=2, color=palette[i], label=truncate_label(col, 25))
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)
    ax.set_ylabel("So luong phan hoi", fontsize=11)
    ax.set_title("Bieu do Mien", fontweight='bold', pad=15)
    if len(cols) > 1:
        ax.legend(bbox_to_anchor=(1.01,1), loc='upper left', frameon=False, fontsize=9)
    plt.tight_layout()
    return fig

CHART_MAP = {
    'column':    plot_column,
    'bar':       plot_bar,
    'pie':       plot_pie,
    'donut':     plot_donut,
    'grouped':   plot_grouped,
    'stacked':   plot_stacked,
    'stacked_h': plot_stacked_h,
    'line':      plot_line,
    'area':      plot_area,
}

def plot_multiple(df, plots_req):
    images = []
    for req in plots_req:
        cols = req.get('cols', [])
        if not cols and 'col' in req:
            cols = [req['col']]
        chart_type = req.get('type', 'column')
        if not cols: continue
        cols = [c for c in cols if c in df.columns]
        if not cols: continue
        fig = None
        try:
            fn = CHART_MAP.get(chart_type, plot_column)
            fig = fn(df, cols)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"Loi ve {chart_type}: {e}")
            fig, ax = plt.subplots(figsize=(7, 2))
            ax.text(0.5, 0.5, f"Loi ve bieu do:\n{e}", ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
        if fig:
            images.append(_fig_to_b64(fig))
    return images
