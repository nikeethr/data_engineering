import numpy as np
import pandas as pd


START_DATE='2016-06-01'
END_DATE='2020-03-01'

idx = pd.date_range(START_DATE, END_DATE)
df = pd.DataFrame(np.abs(np.random.normal(loc=0.0, scale=1.0, size=(len(idx),))), index=idx)
df.columns = ['value']
df.index.name = 'date'

df.to_csv('data.csv')
