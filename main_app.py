import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

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

    st.subheader('Inventory Discrepancy')

    # Tweak datasets before merge them
    df_B = df_counted.groupby('Retail_Product_SKU').count()[['RFID']].reset_index().rename(columns = {'RFID':"Retail_CCQTY"})

    selected_columns = ['Retail_Product_Color','Retail_Product_Level1', 'Retail_Product_Level1Name','Retail_Product_Level2Name','Retail_Product_Level3Name','Retail_Product_Level4Name','Retail_Product_Name','Retail_Product_SKU','Retail_Product_Size','Retail_Product_Style', 'Retail_SOHQTY']
    df_A = df_expected[selected_columns]

    #Merge datasets
    df_discrepancy = pd.merge(df_A, df_B, how='outer', left_on='Retail_Product_SKU', right_on = 'Retail_Product_SKU', indicator = True)

    df_discrepancy['Retail_CCQTY'] = df_discrepancy['Retail_CCQTY'].fillna(0).astype(int)
    df_discrepancy["Retail_SOHQTY"] = df_discrepancy["Retail_SOHQTY"].fillna(0).astype(int)

    #Create Diff column which is the difference between Retail_CCQTY and Retail SOHQTY
    df_discrepancy["Diff"] = df_discrepancy["Retail_CCQTY"] - df_discrepancy["Retail_SOHQTY"]

    #Create Unders column which is the absolute value of Diff values that are less than 0
    df_discrepancy.loc[df_discrepancy["Diff"]<0, "Unders"] = df_discrepancy["Diff"] * (-1)

    #Unders column fill NaN values with 0's and set type to int
    df_discrepancy["Unders"] = df_discrepancy["Unders"].fillna(0).astype(int)

    #Create Overs column which is the Diff values that are greater than 0
    df_discrepancy.loc[df_discrepancy["Diff"]>0, "Overs"] = df_discrepancy["Diff"]

    #Overs column fill NaN values with 0's and set type to int
    df_discrepancy["Overs"] = df_discrepancy["Overs"].fillna(0).astype(int)

    #Create Match column which stores a 0 if the inventories does not match and a 1 if the inventories match
    df_discrepancy.loc[df_discrepancy['Diff'] == 0, 'Match'] = 1
    df_discrepancy.loc[df_discrepancy['Diff'] != 0, 'Match'] = 0
    df_discrepancy["Match"] = df_discrepancy["Match"].astype(int)

    #SKUSide column show which sku inventory as values > 0
    df_discrepancy.loc[(df_discrepancy['Retail_CCQTY'] > 0) & (df_discrepancy['Retail_SOHQTY'] == 0), 'SKUSide'] = 'CC Only'
    df_discrepancy.loc[(df_discrepancy['Retail_SOHQTY'] > 0) & (df_discrepancy['Retail_CCQTY'] == 0), 'SKUSide'] = 'SOH Only'
    df_discrepancy.loc[(df_discrepancy['Retail_SOHQTY'] > 0) & (df_discrepancy['Retail_CCQTY'] > 0), 'SKUSide'] = 'SOH & CC'

    #Accuracy Calculation
    df_discrepancy['SKUAccuracy'] = df_discrepancy['Match'] / df_discrepancy['Retail_SOHQTY']
    df_discrepancy.loc[df_discrepancy['SKUAccuracy'] == np.inf, 'SKUAccuracy'] = 0

    df_discrepancy['ItemAccuracy'] = df_discrepancy['Retail_CCQTY'] / df_discrepancy['Retail_SOHQTY']
    df_discrepancy.loc[df_discrepancy['ItemAccuracy'] == np.inf, 'ItemAccuracy'] = 0

    df_discrepancy['UnitLevelAccuracy'] = (df_discrepancy['Retail_SOHQTY'] - df_discrepancy['Unders'] - df_discrepancy['Overs'] ) / df_discrepancy['Retail_SOHQTY']
    df_discrepancy.loc[df_discrepancy['UnitLevelAccuracy'] == -np.inf, 'UnitLevelAccuracy'] = 0


    options = st.multiselect(
     'Group by',
     selected_columns[:-1],
     ['Retail_Product_Color','Retail_Product_Level1'])
    
    df_grouped = df_discrepancy.groupby(by = options).sum().reset_index()    
    st.dataframe(df_grouped)

    st.markdown('---')

    # Inventory Discrepancy data display
    st.subheader('Inventory Discrepancy Chart')

    #Dropdown
    option = st.selectbox(
        'Display by',
        selected_columns[:-1]
    )

    #Bar Chart
    fig = px.histogram(df_discrepancy, x=option, y=["Retail_SOHQTY", "Retail_CCQTY"],
             barmode='group', 
             text_auto=True,                           
             height=600)    

    fig.update_yaxes(title_text = 'Inventory stock')

    # Plot
    st.plotly_chart(fig, use_container_width=True)    

    # Accuracy chart
    st.subheader('Inventory Accuracy Chart')

    #Bar Chart
    fig_accuracy = px.histogram(df_discrepancy, x=option, y=['SKUAccuracy','ItemAccuracy','UnitLevelAccuracy'],
             barmode='group', 
             text_auto=True,                           
             height=600)    

    fig_accuracy.update_yaxes(title_text = 'Accuracy')

    # Plot!
    st.plotly_chart(fig_accuracy, use_container_width=True)
    st.markdown('---')    
    st.markdown("<h3 style='text-align: center; color: white;'>Cristopher Ortiz </h3>", unsafe_allow_html=True)








    

    