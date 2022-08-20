import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title('Inventory Discrepancy')
file_expected = st.file_uploader("Please upload your expected inventory data", type='csv')
file_counted = st.file_uploader("Please upload your current inventory data", type='csv')
st.markdown('---')

if file_counted is not None and file_expected is not None:
    df_expected = pd.read_csv(file_expected, encoding = "ISO-8859-1", dtype=str)
    df_counted = pd.read_csv(file_counted, encoding = "ISO-8859-1", dtype=str)

    #Display datasets
    st.subheader('Display Datasets')

    with st.expander("Expected inventory data"):
        st.subheader('Expected inventory data')
        st.markdown('---')
        st.dataframe(data = df_expected)

    with st.expander("Counted inventory data"):
        st.subheader('Counted inventory data')
        st.markdown('---')
        st.dataframe(data = df_counted)
    st.markdown('---')

    # Cleaning duplicate SKU values
    
    st.subheader('Handling Duplicates')

    if (df_expected.shape[0] != df_expected['Retail_Product_SKU'].nunique()):
        st.write('Expected inventory has duplicates SKU values')
        st.write("-    "+str(df_expected.shape[0] - df_expected['Retail_Product_SKU'].nunique())+ " Retail_Product_SKU values were dropped")
        df_expected = df_expected.drop_duplicates('Retail_Product_SKU') 
    else:
        st.write('Expected inventory has not duplicate SKU values')

    if (df_counted.shape[0] != df_counted['RFID'].nunique()):
        st.write('Counted inventory has duplicates RFID values')
        st.write("-    "+str(df_counted.shape[0]-df_counted['RFID'].nunique())+ " RFID values were dropped")
        df_counted = df_counted.drop_duplicates('RFID')        
    else:
        st.write('Counted inventory has not duplicate RFID values')
    st.markdown('---')

    # Tweak datasets before merge them
    df_B = df_counted.groupby('Retail_Product_SKU').count()[['RFID']].reset_index().rename(columns = {'RFID':"Retail_CCQTY"})

    selected_columns = ['Retail_Product_Color','Retail_Product_Level1', 'Retail_Product_Level1Name','Retail_Product_Level2Name','Retail_Product_Level3Name','Retail_Product_Level4Name','Retail_Product_Name','Retail_Product_SKU','Retail_Product_Size','Retail_Product_Style', 'Retail_SOHQTY']
    df_A = df_expected[selected_columns]

    




