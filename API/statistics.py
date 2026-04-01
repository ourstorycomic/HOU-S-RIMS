# API/statistics.py
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm

def calculate_reliability(df, cols):
    """
    Calculate Cronbach's Alpha for a set of columns.
    Formula: alpha = (k / (k - 1)) * (1 - sum(item_variances) / total_variance)
    """
    if not cols or len(cols) < 2:
        return {"error": "Cần ít nhất 2 cột để tính độ tin cậy."}
    
    # Lấy dữ liệu và loại bỏ các dòng có giá trị NaN
    data = df[cols].dropna()
    if len(data) < 2:
        return {"error": "Không đủ dữ liệu sau khi loại bỏ giá trị trống."}
    
    # Đảm bảo dữ liệu là số
    try:
        data = data.apply(pd.to_numeric)
    except Exception:
        return {"error": "Dữ liệu phải là dạng số (Likert scale) để tính Cronbach's Alpha."}

    k = data.shape[1]
    item_variances = data.var(ddof=1).sum()
    total_variance = data.sum(axis=1).var(ddof=1)
    
    if total_variance == 0:
        alpha = 0
    else:
        alpha = (k / (k - 1)) * (1 - (item_variances / total_variance))
    
    # Đánh giá độ tin cậy
    status = "Rất tốt" if alpha >= 0.8 else ("Tốt" if alpha >= 0.7 else ("Chấp nhận được" if alpha >= 0.6 else "Không đạt"))
    
    return {
        "alpha": round(alpha, 3),
        "item_count": k,
        "sample_size": len(data),
        "status": status,
        "item_stats": data.describe().round(2).to_dict()
    }

def calculate_correlation(df, cols):
    """
    Calculate Pearson correlation matrix for selected columns.
    """
    if not cols or len(cols) < 2:
        return {"error": "Cần ít nhất 2 cột để tính tương quan."}
    
    data = df[cols].dropna()
    try:
        data = data.apply(pd.to_numeric)
    except Exception:
        return {"error": "Dữ liệu phải là dạng số để tính tương quan."}
        
    corr_matrix = data.corr(method='pearson').round(3)
    
    # Chuyển đổi sang định dạng dễ hiển thị ở Frontend
    result = []
    columns = corr_matrix.columns.tolist()
    for i, col in enumerate(columns):
        row = {"column": col}
        for target in columns:
            row[target] = corr_matrix.loc[col, target]
        result.append(row)
        
    return {
        "columns": columns,
        "matrix": result
    }

def calculate_regression(df, target_col, predictor_cols):
    """
    Perform Multiple Linear Regression.
    """
    if not target_col or not predictor_cols:
        return {"error": "Thiếu biến phụ thuộc hoặc biến độc lập."}
    
    all_cols = [target_col] + predictor_cols
    data = df[all_cols].dropna()
    
    try:
        data = data.apply(pd.to_numeric)
    except Exception:
        return {"error": "Dữ liệu phải là dạng số để chạy hồi quy."}
        
    Y = data[target_col]
    X = data[predictor_cols]
    X = sm.add_constant(X) # Thêm hằng số (Intercept)
    
    model = sm.OLS(Y, X).fit()
    
    summary_data = {
        "r_squared": round(model.rsquared, 3),
        "adj_r_squared": round(model.rsquared_adj, 3),
        "f_pvalue": round(model.f_pvalue, 4),
        "coefficients": []
    }
    
    # Lấy thông số từng biến
    params = model.params
    pvalues = model.pvalues
    std_err = model.bse
    
    for name in params.index:
        summary_data["coefficients"].append({
            "variable": name,
            "coefficient": round(params[name], 3),
            "std_err": round(std_err[name], 3),
            "p_value": round(pvalues[name], 4),
            "sig": "*" if pvalues[name] < 0.05 else ""
        })
        
    return summary_data

def calculate_chi2(df, col1, col2):
    """
    Perform Pearson Chi-Square test of independence.
    """
    if not col1 or not col2:
        return {"error": "Cần chọn 2 cột để chạy Chi-Square."}
    
    data = df[[col1, col2]].dropna()
    crosstab = pd.crosstab(data[col1], data[col2])
    
    try:
        chi2, p, dof, expected = stats.chi2_contingency(crosstab)
        
        # Chuyển đổi crosstab sang list of dicts để dễ hiển thị
        matrix = []
        for index, row in crosstab.iterrows():
            r = {"row": str(index)}
            for col in crosstab.columns:
                r[str(col)] = int(row[col])
            matrix.append(r)
            
        return {
            "chi2": float(chi2),
            "p_value": float(p),
            "dof": int(dof),
            "sig": "Có ý nghĩa" if p < 0.05 else "Không có ý nghĩa",
            "columns": [str(c) for c in crosstab.columns],
            "matrix": matrix,
            "col1": col1,
            "col2": col2
        }
    except Exception as e:
        return {"error": f"Lỗi tính toán Chi-Square: {str(e)}"}

def calculate_anova(df, group_col, value_col):
    """
    Perform One-Way ANOVA.
    """
    if not group_col or not value_col:
        return {"error": "Cần chọn biến phân nhóm và biến giá trị."}
        
    data = df[[group_col, value_col]].dropna()
    try:
        data[value_col] = pd.to_numeric(data[value_col])
    except:
        return {"error": "Biến giá trị phải là dạng số để chạy ANOVA."}
        
    groups = []
    labels = []
    group_stats = []
    
    for name, group in data.groupby(group_col):
        vals = group[value_col].values
        if len(vals) >= 2:
            groups.append(vals)
            labels.append(str(name))
            group_stats.append({
                "group": str(name),
                "n": int(len(vals)),
                "mean": float(round(np.mean(vals), 3)),
                "std": float(round(np.std(vals, ddof=1), 3))
            })
            
    if len(groups) < 2:
        return {"error": "Cần ít nhất 2 nhóm có dữ liệu để chạy ANOVA."}
        
    try:
        f_val, p_val = stats.f_oneway(*groups)
        return {
            "f_statistic": float(round(f_val, 3)),
            "p_value": float(round(p_val, 4)),
            "sig": "Có ý nghĩa" if p_val < 0.05 else "Không có ý nghĩa",
            "group_stats": group_stats,
            "group_col": group_col,
            "value_col": value_col
        }
    except Exception as e:
        return {"error": f"Lỗi tính toán ANOVA: {str(e)}"}

def calculate_descriptive_detailed(df, cols):
    """
    Get detailed descriptive statistics for selected columns.
    """
    if not cols:
        return {"error": "Chưa chọn cột."}
        
    results = []
    for col in cols:
        try:
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(series) > 0:
                results.append({
                    "column": col,
                    "n": int(len(series)),
                    "mean": float(round(series.mean(), 3)),
                    "median": float(round(series.median(), 3)),
                    "std": float(round(series.std(), 3)),
                    "min": float(round(series.min(), 3)),
                    "max": float(round(series.max(), 3)),
                    "skewness": float(round(series.skew(), 3)),
                    "kurtosis": float(round(series.kurtosis(), 3))
                })
        except: continue
        
    return {"stats": results}
