import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import chart_studio as cs
import plotly.offline as po
import plotly.graph_objs as gobj
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

header = st.beta_container()
data = st.beta_container()

with header:
    st.title('Welcome to Customer Live Value')


with data:
    st.header('Online Reatil Data')
    st.text('I found the dataset on kaggle')
    Rtl_data = pd.read_csv('data/OnlineRetail.csv', encoding = 'unicode_escape')
    st.write(Rtl_data.head())

    country_cust_data=Rtl_data[['Country','CustomerID']].drop_duplicates()
    countries = country_cust_data.groupby(['Country'])['CustomerID'].aggregate('count').reset_index().sort_values('CustomerID', ascending=False)
    st.text('The data is concentrated around UK')
    dist = pd.DataFrame(country_cust_data['Country'].value_counts())
    st.bar_chart(dist)

    #Keep only United Kingdom data
    Rtl_data = Rtl_data.query("Country=='United Kingdom'").reset_index(drop=True)

    #Check for missing values in the dataset
    Rtl_data.isnull().sum(axis=0)

    #Remove missing values from CustomerID column, can ignore missing values in description column
    Rtl_data = Rtl_data[pd.notnull(Rtl_data['CustomerID'])]

    #Validate if there are any negative values in Quantity column
    Rtl_data.Quantity.min()

    #Validate if there are any negative values in UnitPrice column
    Rtl_data.UnitPrice.min()

    #Filter out records with negative values
    Rtl_data = Rtl_data[(Rtl_data['Quantity']>0)]

    #Convert the string date field to datetime
    Rtl_data['InvoiceDate'] = pd.to_datetime(Rtl_data['InvoiceDate'])

    #Add new column depicting total amount
    Rtl_data['TotalAmount'] = Rtl_data['Quantity'] * Rtl_data['UnitPrice']
    st.text('After Cleaning the data and taking only UK data')

    st.write(Rtl_data.head())

    st.header('RFM Modelling')

    #Recency = Latest Date - Last Inovice Data, Frequency = count of invoice no. of transaction(s), Monetary = Sum of Total 
    #Amount for each customer

    #Set Latest date 2011-12-10 as last invoice date was 2011-12-09. This is to calculate the number of days from recent purchase
    Latest_Date = dt.datetime(2011,12,10)

    #Create RFM Modelling scores for each customer
    RFMScores = Rtl_data.groupby('CustomerID').agg({'InvoiceDate': lambda x: (Latest_Date - x.max()).days, 'InvoiceNo': lambda x: len(x), 'TotalAmount': lambda x: x.sum()})

    #Convert Invoice Date into type int
    RFMScores['InvoiceDate'] = RFMScores['InvoiceDate'].astype(int)

    #Rename column names to Recency, Frequency and Monetary
    RFMScores.rename(columns={'InvoiceDate': 'Recency', 
                            'InvoiceNo': 'Frequency', 
                            'TotalAmount': 'Monetary'}, inplace=True)

    st.write(RFMScores.reset_index().head())
    
    #Recency distribution plot
    x = RFMScores['Recency']
    sns.distplot(x)
    sns.set(style="ticks", context="talk")
    plt.style.use("dark_background")
    st.text('Recency distribution Plot')
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

    st.text('Frequency distribution plot, taking observations which have frequency less than 1000')
    x = RFMScores.query('Frequency < 1000')['Frequency']
    sns.distplot(x)
    st.pyplot()

    st.text('Monateray distribution plot, taking observations which have monetary value less than 10000')
    x = RFMScores.query('Monetary < 10000')['Monetary']
    sns.distplot(x)
    st.pyplot()

    #Split into four segments using quantiles
    quantiles = RFMScores.quantile(q=[0.25,0.5,0.75])
    quantiles = quantiles.to_dict()

    st.write(quantiles)

    #Functions to create R, F and M segments
    def RScoring(x,p,d):
        if x <= d[p][0.25]:
            return 1
        elif x <= d[p][0.50]:
            return 2
        elif x <= d[p][0.75]: 
            return 3
        else:
            return 4
        
    def FnMScoring(x,p,d):
        if x <= d[p][0.25]:
            return 4
        elif x <= d[p][0.50]:
            return 3
        elif x <= d[p][0.75]: 
            return 2
        else:
            return 1
    
    st.text('Calculate Add R, F and M segment value columns in the existing dataset to show R, F and M segment values')
    RFMScores['R'] = RFMScores['Recency'].apply(RScoring, args=('Recency',quantiles,))
    RFMScores['F'] = RFMScores['Frequency'].apply(FnMScoring, args=('Frequency',quantiles,))
    RFMScores['M'] = RFMScores['Monetary'].apply(FnMScoring, args=('Monetary',quantiles,))
    st.write(RFMScores.head())

    #Calculate and Add RFMGroup value column showing combined concatenated score of RFM
    RFMScores['RFMGroup'] = RFMScores.R.map(str) + RFMScores.F.map(str) + RFMScores.M.map(str)

    st.text('Calculate and Add RFMScore value column showing total sum of RFMGroup values')
    RFMScores['RFMScore'] = RFMScores[['R', 'F', 'M']].sum(axis = 1)
    st.write(RFMScores.head())

    st.text('#Assign Loyalty Level to each customer')
    Loyalty_Level = ['Platinum', 'Gold', 'Silver', 'Bronze']
    Score_cuts = pd.qcut(RFMScores.RFMScore, q = 4, labels = Loyalty_Level)
    RFMScores['RFM_Loyalty_Level'] = Score_cuts.values
    mod1 = RFMScores.head()
    # st.write(mod1)

    st.text('#Validate the data for RFMGroup = 111')
    mod2 = RFMScores[RFMScores['RFMGroup']=='111'].sort_values('Monetary', ascending=False).reset_index().head(10)
    # st.write(mod2)


    st.text('#Recency Vs Frequency')
    graph = RFMScores.query("Monetary < 50000 and Frequency < 2000")

    plot_data = [
        gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Bronze'")['Recency'],
            y=graph.query("RFM_Loyalty_Level == 'Bronze'")['Frequency'],
            mode='markers',
            name='Bronze',
            marker= dict(size= 7,
                line= dict(width=1),
                color= 'blue',
                opacity= 0.8
            )
        ),
            gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Silver'")['Recency'],
            y=graph.query("RFM_Loyalty_Level == 'Silver'")['Frequency'],
            mode='markers',
            name='Silver',
            marker= dict(size= 9,
                line= dict(width=1),
                color= 'green',
                opacity= 0.5
            )
        ),
            gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Gold'")['Recency'],
            y=graph.query("RFM_Loyalty_Level == 'Gold'")['Frequency'],
            mode='markers',
            name='Gold',
            marker= dict(size= 11,
                line= dict(width=1),
                color= 'red',
                opacity= 0.9
            )
        ),
        gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Platinum'")['Recency'],
            y=graph.query("RFM_Loyalty_Level == 'Platinum'")['Frequency'],
            mode='markers',
            name='Platinum',
            marker= dict(size= 13,
                line= dict(width=1),
                color= 'black',
                opacity= 0.9
            )
        ),
    ]

    plot_layout = gobj.Layout(
            yaxis= {'title': "Frequency"},
            xaxis= {'title': "Recency"},
            title='Segments'
        )
    fig = gobj.Figure(data=plot_data, layout=plot_layout)
    # po.iplot(fig)
    st.plotly_chart(fig)
    st.text('#Frequency Vs Monetary')
    graph = RFMScores.query("Monetary < 50000 and Frequency < 2000")

    plot_data = [
        gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Bronze'")['Frequency'],
            y=graph.query("RFM_Loyalty_Level == 'Bronze'")['Monetary'],
            mode='markers',
            name='Bronze',
            marker= dict(size= 7,
                line= dict(width=1),
                color= 'blue',
                opacity= 0.8
            )
        ),
            gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Silver'")['Frequency'],
            y=graph.query("RFM_Loyalty_Level == 'Silver'")['Monetary'],
            mode='markers',
            name='Silver',
            marker= dict(size= 9,
                line= dict(width=1),
                color= 'green',
                opacity= 0.5
            )
        ),
            gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Gold'")['Frequency'],
            y=graph.query("RFM_Loyalty_Level == 'Gold'")['Monetary'],
            mode='markers',
            name='Gold',
            marker= dict(size= 11,
                line= dict(width=1),
                color= 'red',
                opacity= 0.9
            )
        ),
        gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Platinum'")['Frequency'],
            y=graph.query("RFM_Loyalty_Level == 'Platinum'")['Monetary'],
            mode='markers',
            name='Platinum',
            marker= dict(size= 13,
                line= dict(width=1),
                color= 'black',
                opacity= 0.9
            )
        ),
    ]

    plot_layout = gobj.Layout(
            yaxis= {'title': "Monetary"},
            xaxis= {'title': "Frequency"},
            title='Segments'
        )
    fig = gobj.Figure(data=plot_data, layout=plot_layout)
    st.plotly_chart(fig)

    st.text('#Recency Vs Monetary')
    graph = RFMScores.query("Monetary < 50000 and Frequency < 2000")

    plot_data = [
        gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Bronze'")['Recency'],
            y=graph.query("RFM_Loyalty_Level == 'Bronze'")['Monetary'],
            mode='markers',
            name='Bronze',
            marker= dict(size= 7,
                line= dict(width=1),
                color= 'blue',
                opacity= 0.8
            )
        ),
            gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Silver'")['Recency'],
            y=graph.query("RFM_Loyalty_Level == 'Silver'")['Monetary'],
            mode='markers',
            name='Silver',
            marker= dict(size= 9,
                line= dict(width=1),
                color= 'green',
                opacity= 0.5
            )
        ),
            gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Gold'")['Recency'],
            y=graph.query("RFM_Loyalty_Level == 'Gold'")['Monetary'],
            mode='markers',
            name='Gold',
            marker= dict(size= 11,
                line= dict(width=1),
                color= 'red',
                opacity= 0.9
            )
        ),
        gobj.Scatter(
            x=graph.query("RFM_Loyalty_Level == 'Platinum'")['Recency'],
            y=graph.query("RFM_Loyalty_Level == 'Platinum'")['Monetary'],
            mode='markers',
            name='Platinum',
            marker= dict(size= 13,
                line= dict(width=1),
                color= 'black',
                opacity= 0.9
            )
        ),
    ]

    plot_layout = gobj.Layout(
            yaxis= {'title': "Monetary"},
            xaxis= {'title': "Recency"},
            title='Segments'
        )
    fig = gobj.Figure(data=plot_data, layout=plot_layout)
    st.plotly_chart(fig)

    st.header('K-Means Clustering')
    #Handle negative and zero values so as to handle infinite numbers during log transformation
    def handle_neg_n_zero(num):
        if num <= 0:
            return 1
        else:
            return num
    #Apply handle_neg_n_zero function to Recency and Monetary columns 
    RFMScores['Recency'] = [handle_neg_n_zero(x) for x in RFMScores.Recency]
    RFMScores['Monetary'] = [handle_neg_n_zero(x) for x in RFMScores.Monetary]

    st.text('#Perform Log transformation to bring data into normal or near normal distribution')
    Log_Tfd_Data = RFMScores[['Recency', 'Frequency', 'Monetary']].apply(np.log, axis = 1).round(3)

    Recency_Plot = Log_Tfd_Data['Recency']
    ax = sns.distplot(Recency_Plot)
    st.pyplot()

    st.text('#Data distribution after data normalization for Frequency')
    Frequency_Plot = Log_Tfd_Data.query('Frequency < 1000')['Frequency']
    ax = sns.distplot(Frequency_Plot)
    st.pyplot()

    st.text('#Data distribution after data normalization for Monetary')
    Monetary_Plot = Log_Tfd_Data.query('Monetary < 10000')['Monetary']
    ax = sns.distplot(Monetary_Plot)
    st.pyplot()




    #Bring the data on same scale
    scaleobj = StandardScaler()
    Scaled_Data = scaleobj.fit_transform(Log_Tfd_Data)

    #Transform it back to dataframe
    Scaled_Data = pd.DataFrame(Scaled_Data, index = RFMScores.index, columns = Log_Tfd_Data.columns)

    sum_of_sq_dist = {}
    for k in range(1,15):
        km = KMeans(n_clusters= k, init= 'k-means++', max_iter= 1000)
        km = km.fit(Scaled_Data)
        sum_of_sq_dist[k] = km.inertia_
        
    st.text('#Plot the graph for the sum of square distance values and Number of Clusters')
    sns.pointplot(x = list(sum_of_sq_dist.keys()), y = list(sum_of_sq_dist.values()))
    plt.xlabel('Number of Clusters(k)')
    plt.ylabel('Sum of Square Distances')
    plt.title('Elbow Method For Optimal k')
    st.pyplot()

    KMean_clust = KMeans(n_clusters= 3, init= 'k-means++', max_iter= 1000)
    KMean_clust.fit(Scaled_Data)

    st.text('#Find the clusters for the observation given in the dataset')
    RFMScores['Cluster'] = KMean_clust.labels_
    # st.write(RFMScores.head())

    plt.figure(figsize=(7,7))

    st.text('##Scatter Plot Frequency Vs Recency')
    Colors = ["red", "green", "blue"]
    RFMScores['Color'] = RFMScores['Cluster'].map(lambda p: Colors[p])
    ax = RFMScores.plot(    
        kind="scatter", 
        x="Recency", y="Frequency",
        figsize=(10,8),
        c = RFMScores['Color']
    )
    st.pyplot()

