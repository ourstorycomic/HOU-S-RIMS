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

# --- CẤU HÌNH ---
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'Tahoma']
plt.rcParams['axes.unicode_minus'] = False

def truncate_label(text, limit=10): # <--- GIẢM CÒN 10 KÝ TỰ
    s = str(text).strip()
    if len(s) > limit: return s[:limit] + "..."
    return s

def clean_data_numeric(series):
    if pd.api.types.is_numeric_dtype(series): return series
    series_str = series.astype(str).str.lower().str.strip()
    def map_val(text):
        m = re.search(r'^(\d)', text)
        if m: return int(m.group(1))
        if 'hoàn toàn' in text or 'rất' in text: return 5 if 'không' not in text else 1
        if 'không' in text or 'chưa' in text: return 2
        if 'phân vân' in text or 'bình thường' in text: return 3
        if 'đồng ý' in text or 'quan trọng' in text or 'hài lòng' in text: return 4
        return np.nan
    mapped = series_str.apply(map_val)
    if mapped.notna().sum() > len(series) * 0.1: return mapped
    return None

def _fig_to_b64(fig):
    b = io.BytesIO()
    # bbox_inches='tight' giúp không bị cắt mất chữ ở rìa
    fig.savefig(b, format="png", dpi=100, bbox_inches="tight")
    b.seek(0); plt.close(fig)
    return f"data:image/png;base64,{base64.b64encode(b.read()).decode('utf-8')}"

# --- VẼ CỘT ĐỨNG (DỌC) ---
def plot_column_vertical(df, cols):
    means = {}
    for c in cols:
        mapped = clean_data_numeric(df[c])
        if mapped is not None: means[c] = mapped.mean()
    
    fig, ax = plt.subplots(figsize=(max(8, len(cols)*1.5), 7))
    colors = sns.color_palette("viridis", len(cols) if means else 1)

    if means:
        s = pd.Series(means).sort_values()
        bars = ax.bar(range(len(s)), s.values, color=colors)
        ax.set_xticks(range(len(s)))
        ax.set_xticklabels([truncate_label(l, 15) for l in s.index], rotation=0, ha='center')
        ax.set_ylabel("Điểm TB")
        ax.set_title("Điểm Trung Bình (Cột)", fontweight='bold')
        for bar in bars:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height(), f'{bar.get_height():.2f}', ha='center', va='bottom', fontweight='bold')
    else:
        counts = df[cols[0]].value_counts().head(8)
        sns.barplot(x=[truncate_label(l, 10) for l in counts.index], y=counts.values, ax=ax, palette="viridis")
        ax.set_ylabel("Số lượng")
        ax.set_title(f"Thống kê: {truncate_label(cols[0], 15)}", fontweight='bold')
        ax.bar_label(ax.containers[0])
    return fig

# --- VẼ THANH NGANG (NGANG) ---
def plot_bar_horizontal(df, cols):
    means = {}
    for c in cols:
        mapped = clean_data_numeric(df[c])
        if mapped is not None: means[c] = mapped.mean()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    if means:
        s = pd.Series(means).sort_values()
        colors = sns.color_palette("viridis", len(cols))
        ax.barh(range(len(s)), s.values, color=colors)
        ax.set_yticks(range(len(s)))
        ax.set_yticklabels([truncate_label(l, 20) for l in s.index])
        ax.set_xlabel("Điểm TB")
        ax.set_title("Điểm Trung Bình (Ngang)", fontweight='bold')
        ax.bar_label(ax.containers[0], fmt=' %.2f')
    else:
        counts = df[cols[0]].value_counts().head(10)
        sns.barplot(y=[truncate_label(l, 20) for l in counts.index], x=counts.values, ax=ax, palette="viridis", orient='h')
        ax.set_title(f"Thống kê: {truncate_label(cols[0], 30)}", fontweight='bold')
        ax.bar_label(ax.containers[0])
    
    plt.subplots_adjust(left=0.25) # Tăng lề trái
    return fig

# --- VẼ GHÉP NHÓM (DỌC - ĐẢO TRỤC) ---
def plot_grouped_inverted(df, cols):
    data = {}
    for c in cols:
        counts = df[c].astype(str).value_counts(normalize=True).head(5) * 100
        data[c] = counts
    if not data: return None
    
    df_chart = pd.DataFrame(data).fillna(0)
    df_chart.index = [truncate_label(i, 10) for i in df_chart.index] # Cắt cực ngắn
    df_chart.columns = [truncate_label(c, 15) for c in df_chart.columns]

    fig, ax = plt.subplots(figsize=(max(10, len(df_chart.index)*1.5), 7))
    colors = sns.color_palette("Spectral", n_colors=len(df_chart.columns))
    
    df_chart.plot(kind='bar', stacked=False, ax=ax, color=colors, edgecolor='white', width=0.8, rot=0)
    
    ax.set_xticklabels(df_chart.index, rotation=0, ha='center')
    ax.set_ylabel("Tỷ lệ (%)")
    ax.legend(title="Câu hỏi", bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=3, frameon=False)
    ax.set_title("Phân bố chi tiết", fontweight='bold', pad=20)
    
    for c in ax.containers:
        labels = [f'{v.get_height():.0f}' if v.get_height()>5 else '' for v in c]
        ax.bar_label(c, labels=labels, fontsize=9, padding=2)
        
    plt.subplots_adjust(bottom=0.25)
    return fig

# --- VẼ CỘT CHỒNG (NGANG) ---
def plot_stacked_horizontal(df, cols):
    data = {}
    for c in cols:
        counts = df[c].astype(str).value_counts(normalize=True).head(5) * 100
        data[c] = counts
    if not data: return None
    df_chart = pd.DataFrame(data).T.fillna(0)
    
    # [FIX] SET CỨNG LABEL Ở ĐÂY VÀ CẮT CỰC NGẮN (10 chars)
    short_labels = [truncate_label(i, 10) for i in df_chart.index]

    fig, ax = plt.subplots(figsize=(11, max(6, len(cols)*0.9)))
    colors = sns.color_palette("Spectral", n_colors=len(df_chart.columns))
    
    df_chart.plot(kind='barh', stacked=True, ax=ax, color=colors, edgecolor='white', width=0.7)
    
    ax.set_yticks(range(len(short_labels)))
    ax.set_yticklabels(short_labels) # Ép dùng label ngắn

    ax.legend(bbox_to_anchor=(0.5, -0.1), loc='upper center', ncol=5, frameon=False)
    ax.set_title("Phân bố (Cột chồng)", fontweight='bold', pad=20)
    
    for c in ax.containers:
        labels = [f'{v.get_width():.0f}%' if v.get_width()>5 else '' for v in c]
        ax.bar_label(c, labels=labels, label_type='center', color='black', fontsize=9)
        
    plt.subplots_adjust(bottom=0.15, left=0.25) # Tăng lề trái mạnh
    return fig

def plot_multiple(df, plots_req):
    images = []
    for req in plots_req:
        cols = req.get('cols', [])
        type_chart = req.get('type', 'bar')
        if not cols: continue
        try:
            fig = None
            if type_chart == 'column':     fig = plot_column_vertical(df, cols)
            elif type_chart == 'bar':      fig = plot_bar_horizontal(df, cols)
            elif type_chart == 'grouped':  fig = plot_grouped_inverted(df, cols)
            elif type_chart == 'stacked':  fig = plot_stacked_horizontal(df, cols)
            elif type_chart in ['pie', 'donut']:
                counts = df[cols[0]].value_counts().head(8)
                fig, ax = plt.subplots(figsize=(9, 6))
                labels = [truncate_label(l, 15) for l in counts.index]
                ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90)
                if type_chart=='donut': fig.gca().add_artist(plt.Circle((0,0),0.7,fc='white'))
                ax.set_title(truncate_label(cols[0], 30), fontweight='bold')

            if fig is None:
                fig, ax = plt.subplots(figsize=(8,6))
                counts = df[cols[0]].value_counts().head(5)
                sns.barplot(x=[truncate_label(l, 10) for l in counts.index], y=counts.values, ax=ax)
                ax.set_title("Thống kê", fontweight='bold')

            images.append(_fig_to_b64(fig))
        except Exception as e:
            fig, ax = plt.subplots(figsize=(5,1)); ax.text(0.5,0.5,f"Lỗi: {e}"); ax.axis('off')
            images.append(_fig_to_b64(fig))
    return images