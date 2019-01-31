# import libraries
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format
from fuzzywuzzy import fuzz
import time

# load data sets, perform filters and set data types
prop_data = pd.read_csv('./properties.csv')
prop_data['Owner Name 1'] = prop_data['Owner Name 1'].apply(lambda x: str(x))

corps = pd.read_csv('./corps.csv',low_memory=False)
corps['BUSINESS_NAME'] = corps['BUSINESS_NAME'].apply(lambda x: str(x))
corps = corps[(corps['BUSINESS_STATUS'] == 'Active') & (corps['BUSINESS_TYPE'] != 'Trade Name')]

# create instance of function
ratio = fuzz.ratio
set_ratio = fuzz.token_set_ratio

# define matching function
def match_it(series,dataframe):
    matches = []
    append_it = matches.append
    
    for value in series:
        for index,row in dataframe.iterrows():  
            name = row['BUSINESS_NAME']
            
            if (ratio(value,name) < 93) or (set_ratio(value,name) < 97):
                append_it('NA')
            else:
                append_it(row['BUSINESS_ID'])
            
    return pd.Series(matches)

# call function calculating the time it takes to execute
start = time.time()

dataset = prop_data.head(11).assign(BUSINESS_ID=lambda x: match_it(x['Owner Name 1'],corps))

end = time.time()

print(end - start)