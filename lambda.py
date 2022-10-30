import yfinance as yf
from datetime import datetime
import boto3
import json
import math
import smtplib, ssl


def lambda_handler(event=None, context=None):
    # prices_data = ['AAPL', 'TWTR', 'TSLA', 'CAKE', 'GOOG', 'AMZN', 'APDN', 'MSFT', 'NFLX', 'WOOF']
    # prices_data = ['AAPL']
    new_ticker = {}
    _TableName_ = "stockWatcher"
    Primary_Column_Name = "tickerSymbol"
    DB = boto3.resource('dynamodb', region_name='us-east-1')
    table = DB.Table(_TableName_)
    customer_table = DB.Table("customers")
    resp = table.scan(AttributesToGet=['tickerSymbol'])
    prices_data = [i['tickerSymbol'] for i in resp['Items']]
    # print(prices_data)
    now = datetime.now()
    old_data=table.scan()
    current_time = now.strftime("%H:%M:%S")
    for ticks in prices_data:
        stock = yf.Ticker(ticks)
        data1 = stock.info
        new_ticker[ticks] = {
            'name': data1['shortName'],
            'price': data1['regularMarketPrice']
        }
        # print(old_data['Items']['tickerSymbol'])
        for item in old_data['Items']:
            if item['tickerSymbol'] == ticks:
                old_price = item['Price']
            
        
        column = ["Name", "Price", "StoredAt","old_price"]
        # if ticks == 'AAPL':
        #     new_ticker[ticks]['price']=500
        response = table.put_item(
            Item={
                Primary_Column_Name: ticks,
                column[0]: new_ticker[ticks]['name'],
                column[1]: str(new_ticker[ticks]['price']),
                column[2]: current_time,
                column[3]: old_price
            }
        )
        response["ResponseMetadata"]["HTTPStatusCode"]
    read=table.scan()
    print(read['Items'])
    customers_email = customer_table.scan(AttributesToGet=['email'])
    # print(customers_email)
    for tick in read['Items']:
        # greater = max(tick['Price'],tick['old_price'])
        old=float(tick['old_price'])
        # print(tick['Name'])
        if(tick['tickerSymbol']=='AAPL'):
            old=1000
        new=float(tick['Price'])
        if(abs((new-old)/(old))*100 >5):
            customers_email = customer_table.scan(AttributesToGet=['email'])
            print("for")
            for email in customers_email['Items']:
                print("hi"+email['email'])
                
                sendermail="srinidhi.claw@gmail.com"
                port = 465  # For SSL
                password = "vvwtucmrvjufbrrl"
                message = "stock " + tick['Name'] + " has changed more than 5%\n"+"old price: "+str(old)+"\nnew price: "+str(new)
                
                # Create a secure SSL context
                context = ssl.create_default_context()
                
                with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                    server.login(sendermail, password)
                    # TODO: Send email here
                    server.sendmail(sendermail, email['email'], message)

            
    
    return {
        "statusCode": 200,
        "body": json.dumps({"statusCode": 200, "data": response["ResponseMetadata"]["HTTPStatusCode"]}),
        "isBase64Encoded": False
    }