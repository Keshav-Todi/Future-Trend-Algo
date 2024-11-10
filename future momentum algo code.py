#pip install delta_rest_client
from delta_rest_client import DeltaRestClient
import pandas as pd
import time
import requests
from datetime import datetime, timedelta
import json
import csv


def place_post_only_order(asset, quantity, side, check_interval=0,type='close'):
    
    global delta_client

    pair='BTCUSDT'
    order=0
    open_order_id=0
    response_list=[{'price': None, 'id': 0}]
    retries=0

    if(quantity<0):
        quantity=quantity*-1

    while True:
        # Fetch the latest bid, ask, and market price
        
        ticker = delta_client.get_ticker(asset)
        product_id = ticker['product_id']
        mark_price_curr = ticker['mark_price']
        quotes_curr =ticker['quotes']
        best_bid=quotes_curr['best_bid']
        best_ask=quotes_curr['best_ask']
        
        #best_bid = get_best_bid(asset)
        #best_ask = get_best_ask(asset)
        
        if(order==0):
            # Determine the appropriate limit price for the order
            if side == 'buy':
                target_price = best_bid  # Place buy order at best bid to be a maker
            elif side == 'sell':
                target_price = best_ask  # Place sell order at best ask to be a maker
            else:
                raise ValueError("Side must be either 'buy' or 'sell'")
        
            print(f'placing order side {side} qty {quantity} target {target_price} ')
            # Place the post-only limit order
            try:
                order_response = delta_client.place_order(
                    product_id=product_id,#str(188001),#product_id_BTCUSDT,
                    size=quantity,
                    side=side,
                    limit_price=target_price,#705#float(mark_price_BTCUSDT)-5000
                    #order_type= "limit_order"
                    post_only='true',
                    )
            
                response_list = [{
                'price': order_response.get("average_fill_price"),
                'id': order_response.get("id")
                }]
            
            except requests.exceptions.HTTPError as e:
                    print(f"HTTPError encountered: {e}. Retrying...")
                    retries += 1
                    #time.sleep(check_interval)
                
            except Exception as e:
                    print(f"An unexpected error occurred: {e}. Retrying...")
                    retries += 1
                    #time.sleep(check_interval)

            print(response_list)
        
        else:
            if  (side=='buy' and float(target_price)<float(best_bid)*(100-0.01)/100.0) or (side=='sell' and float(target_price)>float(best_ask)*(100+0.01)/100.0):
                #print(f"Order {open_order_id} need to be cancelled by me target {target_price} best bid {best_bid} side {side}")
                try:
                    cancel_response = delta_client.cancel_order(product_id, open_order_id)
                    if side == 'buy':
                        print(f"Order {open_order_id} cancelled by me target {target_price} best bid {best_bid} side {side}")
                    else:
                        print(f"Order {open_order_id} cancelled by me target {target_price} best bid {best_bid} side {side}") 

                except requests.exceptions.HTTPError as e:
                    print(f"HTTPError encountered: {e}. Retrying...")
                    retries += 1
                    #time.sleep(check_interval)
                
                except Exception as e:
                    print(f"An unexpected error occurred: {e}. Retrying...")
                    retries += 1
                    #time.sleep(check_interval)
            order=0
            


        # Wait for a short interval to check if the order is filled or canceled
        #time.sleep(check_interval)

        orders = delta_client.get_live_orders()
        #print(orders)
        
        # Check if the order is filled
        if orders is not None and orders!= []:
            #print(orders)
            print(f"Order {response_list[0]['id']} still there not exectuted target {target_price}")
            open_order_id=response_list[0]['id']
            order=1
        
        # If the order is not filled, check if it was canceled by the exchange
        else:
            response=delta_client.get_position(product_id)

            if(type=='open'):
                

                if (response["entry_price"] is None):
                    print(f"Order cancelled or not there target {target_price} ")
                    order=0  # Loop again to place a new order

                if (response["entry_price"] is not None ):
                    print(f"Order size {response['size']} successful price {response['entry_price']} ")
                    order=0
                    break  # Loop again to place a new order
            else:

                if (response["entry_price"] is not None):
                    print(f"Order cancelled or not there target {target_price} ")
                    order=0  # Loop again to place a new order

                if (response["entry_price"] is None ):
                    print(f"Order size {response['size']} successful price {response['entry_price']} ")
                    order=0
                    break  # Loop again to place a new order

    a=1
    #return response_list

"""
delta_client = DeltaRestClient(
base_url='https://api.delta.exchange',#'https://cdn.india.deltaex.org',#
 api_key='',
  api_secret=''
)
"""
#"""
delta_client = DeltaRestClient(
  base_url='https://api.india.delta.exchange',#'https://api.delta.exchange',#'https://cdn.india.deltaex.org',#
  api_key='',
  api_secret=''
  ,raise_for_status=False
  
)
#"""

# Fetch the public IP address
public_ip = requests.get('https://ifconfig.me').text
print("Public IP Address:", public_ip)

asset='BNBUSD'
quantity_ini=1
quantity=quantity_ini
side='sell'
check_interval=0
type='open'
threshold_b=60850#*(10)

threshold_s_up=57600
threshold_b_down=52530

threshold_s=60650#*(-10)
"""
per_prof=2.5*100
per_stop=0.1
"""
thres_prof=0.25


ticker=delta_client.get_ticker(asset)
product_id=ticker['product_id']
response = delta_client.get_position(product_id)

place_post_only_order(asset, quantity, side, check_interval,type)

check_interval=2.5
condition=False
#response = delta_client.get_position(139)
#print(response)#{'entry_price': None, 'size': 0}
while(condition):

    per_prof=2.5*100
    per_stop=0.1
    thres_inc=0

    while(response['entry_price'] is None):

        
        if (float(ticker['mark_price'])>=threshold_b):
            side='buy'
            check_interval=0
            place_post_only_order(asset, quantity, side, check_interval,type)
            b=1
            break
        if (float(ticker['mark_price'])<=threshold_s):
            side='sell'
            check_interval=0
            place_post_only_order(asset, quantity, side, check_interval,type)
            b=1
            break

        ticker=delta_client.get_ticker(asset)
        product_id=ticker['product_id']
        response = delta_client.get_position(product_id)

        print(f'in none checking for order mark pr {float(ticker["mark_price"]):.2f} threshold_b {threshold_b:.2f} threshold_s {threshold_s:.2f}')

        time.sleep(check_interval)

    ticker=delta_client.get_ticker(asset)
    product_id=ticker['product_id']
    response = delta_client.get_position(product_id)
    quantity=response['size']

    if(quantity>0):
        side='buy'
    if(quantity<0):
        side='sell'
        quantity=quantity*-1

    
    check_interval=2.5
    per_loss=0.1

    while (response['entry_price'] is not None):

        #response = delta_client.get_position(139)
        ticker=delta_client.get_ticker(asset)
        best_bid=float(ticker['quotes']['best_bid'])
        best_ask=float(ticker['quotes']['best_ask'])

        if( (float(best_bid)-float(response['entry_price']))<(-float(response['entry_price'])*(per_stop)/100.0) and side=='buy'):
            side='sell'
            type='close'
            print(f"in loss entry {float(response['entry_price']):.2f} best bid  {float(best_bid):.2f}, diff {(float(best_bid)-float(response['entry_price'])):.2f}, t_diff {(-float(response['entry_price'])*(per_stop)/100.0):.2f} closing by {side}")
            check_interval=0
            place_post_only_order(asset, quantity, side, check_interval,type)
            break

        elif( (float(response['entry_price'])-float(best_ask))<(-float(response['entry_price'])*(per_stop)/100.0) and side=='sell'):
            side='buy'
            type='close'
            print(f"in loss entry {float(response['entry_price']):.2f} best ask  {float(best_ask):.2f}, diff {(float(response['entry_price'])-float(best_ask)):.2f}, t_diff {(-float(response['entry_price'])*(per_stop)/100.0):.2f} closing by {side}")
            check_interval=0
            place_post_only_order(asset, quantity, side, check_interval,type)
            break

        else:
            if(side=='buy'):
                pnl=float(best_bid)-float(response['entry_price'])
                pnl_size=pnl*quantity/1000
                print(f"entry {float(response['entry_price']):.2f} best bid {float(best_bid):.2f} | diff {(float(best_bid)-float(response['entry_price'])):.2f}, t_diff {(-float(response['entry_price'])*(per_stop)/100.0):.2f} thres {(float(response['entry_price'])*(thres_prof)/100.0):.2f} | pnl {pnl:.2f} tot_pnl {pnl_size:.2f}")
            else:
                pnl=float(response['entry_price'])-float(best_ask)
                pnl_size=pnl*quantity/1000
                print(f"entry {float(response['entry_price']):.2f} best bid {float(best_ask):.2f} | diff {(float(response['entry_price'])-float(best_ask)):.2f}, t_diff {(-float(response['entry_price'])*(per_stop)/100.0):.2f} thres {(float(response['entry_price'])*(thres_prof)/100.0):.2f} | pnl {pnl:.2f} tot_pnl {pnl_size:.2f}")
        if(pnl>0):
            check_interval=2.5
        else:
            check_interval=1.5

        if( (float(best_bid)-float(response['entry_price']))>(float(response['entry_price'])*(per_prof)/100.0) and side=='buy'):
            side='sell'
            type='close'
            print(f"in profit entry {float(response['entry_price']):.2f} best bid  {float(best_bid):.2f}, diff {(float(best_bid)-float(response['entry_price'])):.2f}, t_diff {(float(response['entry_price'])*(per_prof)/100.0):.2f} closing by {side}")
            check_interval=0
            place_post_only_order(asset, quantity, side, check_interval,type)
            condition=False
            break

        elif( (float(response['entry_price'])-float(best_ask))>(float(response['entry_price'])*(per_prof)/100.0) and side=='sell'):
            side='buy'
            type='close'
            print(f"in profit entry {float(response['entry_price']):.2f} best ask  {float(best_ask):.2f}, diff {(float(response['entry_price'])-float(best_ask)):.2f}, t_diff {(float(response['entry_price'])*(per_prof)/100.0):.2f} closing by {side}")
            check_interval=0
            place_post_only_order(asset, quantity, side, check_interval,type)
            condition=False
            break

        if( (float(best_bid)-float(response['entry_price']))>(float(response['entry_price'])*(thres_prof)/100.0) and side=='buy' and thres_inc==0):
            per_stop=-0.1
            thres_inc=1
            print(f"in thres increase entry {float(response['entry_price']):.2f} best bid  {float(best_bid):.2f}, diff {(float(best_bid)-float(response['entry_price'])):.2f}, t_diff {(float(response['entry_price'])*(thres_prof)/100.0):.2f} closing by {side}")


        elif( (float(response['entry_price'])-float(best_ask))>(float(response['entry_price'])*(thres_prof)/100.0) and side=='sell' and thres_inc==0):
            per_stop=-0.1
            thres_inc=1
            print(f"in threse increase entry {float(response['entry_price']):.2f} best ask  {float(best_ask):.2f}, diff {(float(response['entry_price'])-float(best_ask)):.2f}, t_diff {(float(response['entry_price'])*(thres_prof)/100.0):.2f} closing by {side}")


        time.sleep(check_interval)    
        response = delta_client.get_position(product_id)
        quantity=response['size']
        if(quantity<0):
            quantity=quantity*-1

    ticker=delta_client.get_ticker(asset)
    threshold_b=float(ticker['mark_price'])*(100+0.2)/100
    threshold_s=float(ticker['mark_price'])*(100-0.2)/100
    quantity=quantity_ini
    type='open'

"""
order_response = delta_client.place_order(
            product_id=139,#str(188001),#product_id_BTCUSDT,
            size=1,
            side='buy',
            limit_price=62000,#705#float(mark_price_BTCUSDT)-5000
            #order_type= "limit_order"
            )
"""