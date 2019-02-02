# import libraries
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format
from fuzzywuzzy import fuzz
import re
import time
# define cleaning function
def clean_it(string):
    # define replace rules
    replace_dict = {
        '/':' ',
        '-':' ',
        '*':'',
        '&':'',
        ',':'',
        '#':'',
        '.':''
    }

    # transform replace rules for regex understanting
    rep = dict((re.escape(k), v) for k, v in replace_dict.items())

    # create regex patterns
    pattern = re.compile('|'.join(rep.keys()))
    the = re.compile(r'\bthe\b',re.I)
    multiple_spaces = re.compile(r'\s{2,}')

    # run replace
    cleaned_text = pattern.sub(lambda x: replace_dict[x.group(0)],string)
    cleaned_text = the.sub('',cleaned_text)
    cleaned_text = re.sub(multiple_spaces,' ',cleaned_text)
    cleaned_text = cleaned_text.strip()

    #  return new string
    return cleaned_text.lower()

# create instance of function from fuzzywuzzy module
ratio = fuzz.ratio
set_ratio = fuzz.token_set_ratio

# define matching function
def match_it(series,dataframe):
    matches = []
    append_it = matches.append

    for value in series:
        # create block
        startswith = value[:7]
        df = dataframe[dataframe['BUSINESS_NAME'].str.contains(startswith,case=False,na=False)]

        for index,row in df.iterrows():
            name = row['BUSINESS_NAME_clean']

            # simple matching
            if (name == value):
                append_it(row['BUSINESS_ID'])

            # fuzzy matching
            elif (ratio(value,name) < 93) or (set_ratio(value,name) < 97):
                append_it('NA')
            else:
                append_it(row['BUSINESS_ID'])

    return pd.Series(matches)

start = time.time()
# load data sets
prop_data = pd.read_csv('./properties.csv')
corps = pd.read_csv('./corps.csv',low_memory=False)

# run filters, set data types, and perform basic cleaning on strings
prop_data['Owner Name 1_clean'] = prop_data['Owner Name 1'].apply(lambda x: clean_it(str(x)))
# corps = corps[(corps['BUSINESS_STATUS'] == 'Active') & (corps['BUSINESS_TYPE'] != 'Trade Name')]
corps['BUSINESS_NAME_clean'] = corps['BUSINESS_NAME'].apply(lambda x: clean_it(str(x)))

# call function

dataset = prop_data.head(11).assign(BUSINESS_ID=lambda x: match_it(x['Owner Name 1_clean'],corps))
print(time.time() - start)
