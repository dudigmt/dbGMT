import pandas as pd
from datetime import datetime

# path excel
EXCEL_PATH = r"Q:\projects\dbGMT\gaji.xlsx"  # ganti

df = pd.read_excel(EXCEL_PATH)

# rename biar konsisten
df = df.rename(columns={
    "NIK": "nik",
    "TahunBulan": "period",
    "GajiPokok": "basic_salary"
})

# parse tanggal (MM/DD/YYYY)
df["period"] = pd.to_datetime(df["period"], format="%m/%d/%Y").dt.date

print(df.head())
print(df.dtypes)
