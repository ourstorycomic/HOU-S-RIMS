import pandas as pd
import pyreadstat
import os

# Create a mock dataset
df = pd.DataFrame({
    'Q1': [5, 4, 5, 5, 4, 3, 5, 4, 5, 5],
    'Q2': [5, 5, 4, 5, 4, 2, 5, 4, 5, 4],
    'Q3': [4, 4, 5, 4, 5, 3, 4, 5, 4, 5],
    'Income': [5000, 6000, 4500, 7000, 5500, 3000, 8000, 6500, 4000, 9000]
})

output_path = 'test_spss.sav'
pyreadstat.write_sav(df, output_path)
print(f"Created mock SPSS file at: {os.path.abspath(output_path)}")
