#API/analysis.py
import pandas as pd
import scipy.stats as stats
import numpy as np
from API.main import MAPPING_CONFIG

def clean_and_map(df, col):
    """Làm sạch và map dữ liệu về dạng chữ để hiển thị"""
    col_str = str(col).strip()
    mapped = df[col].astype(str)
    if col_str in MAPPING_CONFIG:
        mapping = MAPPING_CONFIG[col_str]
        safe_map = {str(k): v for k, v in mapping.items()}
        safe_map.update({int(k): v for k, v in mapping.items() if str(k).isdigit()})
        mapped = df[col].apply(lambda x: safe_map.get(str(x).replace('.0',''), str(x)))
    return mapped

def run_advanced_analysis(df, cols):
    """
    ENGINE PHÂN TÍCH SPSS: Descriptive, Chi-Square, ANOVA, Correlation
    """
    output = []
    output.append("=== KẾT QUẢ PHÂN TÍCH DỮ LIỆU (SPSS/PYTHON ENGINE) ===")
    
    # 1. thống kê mô tả
    output.append("\n[1] THỐNG KÊ MÔ TẢ (FREQUENCIES & DESCRIPTIVES)")
    valid_numeric_cols = []
    
    for c in cols:
        series = clean_and_map(df, c)
        counts = series.value_counts().sort_index()
        total = len(series)
        
        output.append(f"\n--- Biến: {c} (N={total}) ---")
        for idx, val in counts.items():
            pct = (val/total)*100
            output.append(f"   {idx}: {val} ({pct:.1f}%)")
        
        try:
            num_series = pd.to_numeric(df[c], errors='coerce').dropna()
            if len(num_series) > total * 0.7 and len(num_series.unique()) > 1:
                mean = num_series.mean()
                std = num_series.std()
                median = num_series.median()
                output.append(f"   >> [Mean]: {mean:.2f} | [Std.Dev]: {std:.2f} | [Median]: {median}")
                valid_numeric_cols.append(c)
        except: pass

    # 2. Kkiểm định mối liên hệ
    if len(cols) >= 2:
        output.append("\n[2] KIỂM ĐỊNH GIẢ THUYẾT (HYPOTHESIS TESTING)")
        col1 = cols[0]
        col2 = cols[1]
        
        # A. CHI-SQUARE Cho biến định danh
        s1 = clean_and_map(df, col1)
        s2 = clean_and_map(df, col2)
        
        if s1.nunique() < 20 and s2.nunique() < 20:
            crosstab = pd.crosstab(s1, s2)
            output.append(f"\n>>> Bảng chéo (Crosstab) giữa [{col1}] và [{col2}]:")
            output.append(crosstab.to_string())
            
            try:
                chi2, p, dof, expected = stats.chi2_contingency(crosstab)
                sig = "SIGNIFICANT (Có ý nghĩa)" if p < 0.05 else "NOT SIGNIFICANT (Không ý nghĩa)"
                star = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
                
                output.append(f"\n>>> KIỂM ĐỊNH PEARSON CHI-SQUARE:")
                output.append(f"   - Chi-square val: {chi2:.3f}")
                output.append(f"   - Df (Bậc tự do): {dof}")
                output.append(f"   - P-value (Sig.): {p:.5f} {star}")
                output.append(f"   => KẾT LUẬN: {sig}")
            except Exception as e: output.append(f"(Không thể chạy Chi-square: {e})")

        # B. ANOVA TEST so sánh trung bình
        if col2 in valid_numeric_cols:
            try:
                groups = []
                group_labels = []
                # Gom nhóm dữ liệu
                for name, group in df.groupby(col1):
                    vals = pd.to_numeric(group[col2], errors='coerce').dropna()
                    if len(vals) > 5: # Cần ít nhất 5 mẫu để test
                        groups.append(vals)
                        group_labels.append(name)
                
                if len(groups) >= 2:
                    f_val, p_val = stats.f_oneway(*groups)
                    star = "***" if p_val < 0.001 else ("**" if p_val < 0.01 else ("*" if p_val < 0.05 else ""))
                    
                    output.append(f"\n>>> ONE-WAY ANOVA (So sánh trung bình):")
                    output.append(f"   - Biến phân nhóm: {col1}")
                    output.append(f"   - Biến phụ thuộc (Số): {col2}")
                    output.append(f"   - F-statistic: {f_val:.3f}")
                    output.append(f"   - P-value (Sig.): {p_val:.5f} {star}")
                    if p_val < 0.05:
                        output.append("   => KẾT LUẬN: Có sự khác biệt có ý nghĩa thống kê giữa các nhóm.")
                    else:
                        output.append("   => KẾT LUẬN: Không có sự khác biệt (Các nhóm giống nhau).")
            except: pass

    return "\n".join(output)