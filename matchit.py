# import libraries
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format
from fuzzywuzzy import fuzz
import re
from random import sample
import json

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
        '.':'',
        '(':'',
        ')':'',
        '[':'',
        ']':'',
        '{':'',
        '}':''
    }

    # transform replace rules for regex understanting
    rep = dict((re.escape(k), v) for k, v in replace_dict.items())

    # create regex patterns
    pattern = re.compile('|'.join(rep.keys()))
    the = re.compile(r'\bthe\b',re.I) # other stop words?
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

# define ngram generator function
def make_ngrams(string, n):
    output = []
    for i in range(len(string)-n+1):
        output.append(string[i:i+n])
    return output

# define matching function
def match_it(series,dataframe):
    matches = []
    append_it = matches.append

    ngram_len = 5
    rand_sample = 4

    for value in series:
        # flag, checks if there is a match
        is_match = False

        # blocking w random n-grams from string
        ngrams = make_ngrams(value,ngram_len) # create ngrams
        ngrams = sample(ngrams,min(len(ngrams),rand_sample)) # grab random sample from ngrams
        ngrams = '|'.join(ngrams) # join ngrams into single string for regex

        # pandas filter to create block
        df = dataframe[dataframe['BUSINESS_NAME'].str.contains(ngrams,case=False,na=False,regex=True)]

        # try simple matching first
        for index,row in df.iterrows(): # iterate over rows
            # check flag, if no matches found yet, keep trying
            if is_match == False:
                name = row['BUSINESS_NAME_clean']

                if (name == value):
                    print(value,name,'PERFECT MATCH')
                    append_it(row['BUSINESS_ID'])
                    is_match = True

            else:
                break

        # try fuzzy matching
        for index,row in df.iterrows(): # iterate over rows
            # check flag, if no matches found yet, keep trying
            if is_match == False:
                name = row['BUSINESS_NAME_clean']

                if (ratio(value,name) > 93) and (set_ratio(value,name) > 96):
                    print(value,name,'FUZZY MATCH')
                    append_it(row['BUSINESS_ID'])
                    is_match = True

            else:
                break

        # after all iterations, if no match is found, return "NA"
        if is_match == False:
            print(value,'NO MATCH')
            append_it('NA')

    # returns pandas Series representing the new column
    return pd.Series(matches)

# load data sets
prop_data = pd.read_csv('./properties.csv',low_memory=False)
corps = pd.read_csv('./corps.csv',low_memory=False)
corps_to_principals = pd.read_csv('./corp_to_principals.csv',low_memory=False)

# run filters, set data types, and perform basic cleaning on strings
prop_data['Owner Name 1_clean'] = prop_data['Owner Name 1'].apply(lambda x: clean_it(str(x)))
corps['BUSINESS_NAME_clean'] = corps['BUSINESS_NAME'].apply(lambda x: clean_it(str(x)))

# call function
dataset = prop_data.assign(BUSINESS_ID=lambda x: match_it(x['Owner Name 1_clean'],corps))

print("TOTAL MATCHES:",str(len(dataset[dataset['BUSINESS_ID'] != 'NA'])))
print("EFFICIENCY:",str(len(dataset[dataset['BUSINESS_ID'] != 'NA'])/len(dataset)))

# create list to append dicts to
json_data = []
append_to_json = json_data.append

for index,row in dataset.iterrows():
    # filter list of dicts for entry w Owner name
    filter_json_data = [obj for obj in json_data if obj['owner_name'] == row['Owner Name 1']]
    # create dict object for property
    prop_obj = {"property_id":row['lookup-id'],"property_real_value":row["Listed Real Value"]}

    # existing dict will receive updates
    if len(filter_json_data) > 0:
        filter_json_data[0]['properties'].append(prop_obj)

        filter_json_data[0]['total_value'] = filter_json_data[0]['total_value'] + row["Listed Real Value"]

        if row['BUSINESS_ID'] != 'NA':
            for principal in list(corps_to_principals[corps_to_principals['BUSINESS_ID'] == row['BUSINESS_ID']].loc[:,'PRINCIPAL_NAME']):
                if principal in filter_json_data[0]['principals']:
                    continue
                else:
                    filter_json_data[0]['principals'].append(principal)

    # new dict object will be appended to list
    else:

        json_obj = {
            "owner_name":row['Owner Name 1'],
            "properties":[prop_obj],
            "total_value":row["Listed Real Value"]
        }

        if row['BUSINESS_ID'] != 'NA':
            json_obj['business_id'] = row['BUSINESS_ID']
            json_obj['principals'] = list(corps_to_principals[corps_to_principals['BUSINESS_ID'] == row['BUSINESS_ID']].loc[:,'PRINCIPAL_NAME'])

        json_data.append(json_obj)

with open('data.json', 'w') as f:
    json.dump(json_data,f,indent=4,sort_keys=True)
