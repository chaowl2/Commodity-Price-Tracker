import pandas as pd
import datetime
import ruptures as rpt
import numpy as np
import sys

def commodity_cpd(filename):
    df = pd.read_excel(filename, sheet_name = 'Material $' )
    df = df.loc[:,~df.columns.str.startswith('Unnamed:')]
    df.drop(columns=['Year', 'Month','Combo','RMB/USD','Zinc FCST', 
                     'Current Price Zinc Base', 'RMB/USD FSCT',
                     'Current Price RMB Base', 'Zinc Leekee (ZA3 USD).1'], inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[df['Date'] > datetime.datetime(2007,12,31)]
    df = df.set_index('Date')
    
    # Data is on a daily basis. Aggregate the data on a monthly basis by computing average for the month.
    data_by_month = df.groupby(pd.Grouper(freq="M"))
    df = data_by_month.mean()
    
    # Create an excel file to store computed values
    writer = pd.ExcelWriter('commodity.xlsx')
    
    # Creating a new Sheet for each commodity in the original file
    for col in df.columns:
        tmp = pd.DataFrame(df[col])
        tmp.dropna(inplace=True)
        
        # Choose an appropriate cost function for Change Point Detection (CPD). The cost functions and their definitions can be 
        # found here: https://centre-borelli.github.io/ruptures-docs/user-guide/costs/costrbf/
        model="rbf" # l1 or l2 are other options
        
        # We are using the PELT method to find change points. 
        # This method is used when we dont know the number of change points in the data. Dynp can be used if you know that information.
        algorithm = rpt.Pelt(model=model, jump= 6).fit(tmp) # jump = 6 because we want change detected at a min of 6 month interval.
        result = algorithm.predict(pen=1) # pen is a variable used to penalize overfitting the model. Can be changed as needed.
        print(col, result)
        # Create a label column for each commodity which changes back and forth from 0-1 every time there is a CPD
        # This label is created for the purposes of visualization and creating a dashboard in Power BI
        point = 0
        counter = 0
        tmp.reset_index(inplace=True)
        for i in result:
            while counter < i:
                tmp.at[counter,'label'] = point
                counter +=1
            point = (point+1)%2
        name = col.replace("/","-")
        tmp.to_excel(writer, sheet_name=name[:31], index = False)
    writer.save()

if __name__ == "__main__":
    filename = sys.argv[1]
    commodity_cpd(filename)
