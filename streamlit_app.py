import streamlit as st
import pandas as pd

import matplotlib.pyplot as plt
import numpy as np
import time
import requests
import io

from pathlib import Path

# --- Defs
@st.cache_data()
def get_health():
    '''This function checks the health of the Render service for predictions.'''
    return requests.get(url = 'https://ml-ops-69kd.onrender.com/health')

@st.cache_data()
def get_predictions(uploaded_file):
    '''
    This function is activated by the 'Get Predictions!' button.
    It takes the 'uploaded_file' with predictions and POST it as payload to a Render Service.
    Then returns the result as the pandas dataframe
    '''

    # uploaded_file_df = pd.read_csv(uploaded_file)
    try:
        for column in ['id', 'Time', 'IsFraud']:
            df_for_payload = uploaded_file.drop(column, axis=1)
    except:
        df_for_payload = uploaded_file
    rows = df_for_payload.to_dict(orient = 'records') # adjusting format
    payload = {'records' : rows} # adjusting format

    response = requests.post(
        url = 'https://ml-ops-69kd.onrender.com/predict',
        json = payload
    )
    return response


# --- Layout

st.write(
    '''
    ## Credit Card Fraud Detection Predictions
'''
)

health = get_health().json()
st.caption(':gray[Service Status = ' + "'" + health['status'] + "']")


uploaded_file = st.file_uploader('Choose formatted file to get predictions', type='csv')

if uploaded_file is not None: # need for handle error, when there is not file
    '#### Your dataframe for predictions'

    file_bytes = uploaded_file.getvalue()
    uploaded_dataframe = pd.read_csv(io.BytesIO(file_bytes))

    # Toggle: uploaded dataframe
    show_table1 = st.toggle('Show your dataframe for predictions', value=True)
    table_box1 = st.empty()
    with table_box1:
        if show_table1:
            st.write(uploaded_dataframe)


predictions_result = st.container()
predictions_response = None

if uploaded_file is not None:
    with predictions_result:
        '#### Predictions for your dataframe'
        predictions_response = get_predictions(uploaded_dataframe)
        predictions_dataframe = pd.DataFrame(predictions_response.json()).rename(
            columns={
                'probabilities' : 'Probability',
                'labels': 'Fraud'
            })
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric('Number of observations', len(predictions_dataframe))
        col2.metric('Number of frauds', len(predictions_dataframe[predictions_dataframe['Fraud']==1]))

        mean_probability = sum(predictions_dataframe['Probability'])/len(predictions_dataframe)*100
        col3.metric('Mean probability of fraud', f'{mean_probability:.2f}%')
        df_merge = pd.concat([uploaded_dataframe, predictions_dataframe], axis='columns')

        # Slider
        threshold_pct = st.slider('Fraud threshold, %', min_value = 0.0, max_value=100.0, value=0.0, step = 0.05)
        threshold = threshold_pct / 100
        # Slice visuals
        sliced_df = df_merge[df_merge['Probability'] >= threshold]
        # new card #4
        col4.metric('Above threshold', len(sliced_df))

        # st.caption(':gray[Sorted by Probability: highest-risk rows first.]')
        st.write('Sorted by Probability: highest-risk rows first.')

        # transactions table toggle
        show_table2 = st.toggle('Show transactions above threshold table.', value = False)
        table_box2 = st.empty()
        with table_box2:
            if show_table2:
                st.dataframe(sliced_df[['id', 'Probability', 'Transaction_Amount', 'Fraud']].sort_values(by='Probability', ascending=False),
                            hide_index = True)
   

        '##### Transaction Amount vs Probability'
        st.caption('High-probability, high-amount points in the top-right warrant manual review. Points above threshold are red.')
        # st.caption('Only points above the selected threshold are shown')
        df_plot = df_merge.copy()
        df_plot['RiskFlag'] = np.where(df_plot['Probability'] >= threshold, "#ff4b4b", "#6092b9")
        st.scatter_chart(
            data = df_plot,
            x = 'Probability',
            y = 'Transaction_Amount',
            color = 'RiskFlag'
        )
        # st.pyplot(plt.scatter(predictions_dataframe['Probability'], uploaded_dataframe['Transaction_Amount']))
        # st.write(get_predictions(uploaded_dataframe).json())

example_dataframe2 = pd.DataFrame(
    # np.random.randn(5,28),
    np.concatenate(
        (np.random.randn(5,28), np.random.uniform(0,1000, size=(5,1))),
        axis=1
        ),
    columns = tuple('feat%d' % col for col in range(1,29,1)) + ('Transaction_Amount',)
)

example_dataframe = st.container()
# example_dataframe2 

# remove example, if the user succeeded with getting predictions 
with example_dataframe:
    if predictions_response is not None and predictions_response.status_code == 200:
        example_dataframe = None
    else:
        '### Example of dataframe for attachment'
        st.dataframe(example_dataframe2)

with st.expander('Interactive Power BI dashboard'):
    'Some metrics from the train dataset'
    st.markdown(
        '''
    <iframe title="sample pbi report" width="672" height="440"
    src="https://app.powerbi.com/view?r=eyJrIjoiOGMyZmJiMWQtYTE1Ni00Njc2LThlOGEtN2NiZmZhMDY0NzA0IiwidCI6IjdhZjZjNzMyLTAwMDQtNDhiMC1iMTM0LTQ4ZmVjNmE5ZTk3NSIsImMiOjl9"
    frameborder="0" allowFullScreen="true">
    </iframe>
    '''

    , unsafe_allow_html=True

    )

    url = 'https://app.powerbi.com/view?r=eyJrIjoiOGMyZmJiMWQtYTE1Ni00Njc2LThlOGEtN2NiZmZhMDY0NzA0IiwidCI6IjdhZjZjNzMyLTAwMDQtNDhiMC1iMTM0LTQ4ZmVjNmE5ZTk3NSIsImMiOjl9'
