# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import pathlib
import json


# Token Data
tokens = {
    '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2': 'WETH', 
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': 'USDC',
    '0xdAC17F958D2ee523a2206206994597C13D831ec7': 'USDT',
    '0x6B175474E89094C44Da98b954EedeAC495271d0F': 'DAI',
    '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984': 'UNI',
    '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599': 'WBTC',
    '0x514910771AF9Ca656af840dff83E8264EcF986CA': 'LINK',
    '0x4Fabb145d64652a948d72533023f6E7A623C7C53': 'BUSD',
    '0x0000000000085d4780B73119b644AE5ecd22b376': 'TUSD',
    '0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0': 'MATIC',
    '0x8E870D67F660D95d5be530380D0eC0bd388289E1': 'PAX',
    '0xc00e94Cb662C3520282E6f5717214004A7f26888': 'COMP',
    '0x956F47F50A910163D8BF957Cf5846D573E7f87CA': 'FEI',
    '0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2': 'MKR',
    '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE': 'SHIB',
    '0x4d224452801ACEd8B2F0aebE155379bb5D594381': 'APE',
    '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9': 'AAVE',
    '0x50D1c9771902476076eCFc8B2A83Ad6b9355a4c9': 'FTX Token',
    '0x111111111117dC0aa78b770fA6A738034120C302': '1INCH',
    '0x0C10bF8FcB7Bf5412187A595ab97a3609160b5c6': 'USDD',
    '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39': 'HEX',
    '0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72': 'ENS',
    '0x06af07097c9eeb7fd685c692751d5c66db49c215': 'CHAI',
    '0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D': 'renBTC'
    }

# Set the tokens to generate the config for
poolSlice = [
    '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 
    '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
    '0x514910771AF9Ca656af840dff83E8264EcF986CA',
    '0x50D1c9771902476076eCFc8B2A83Ad6b9355a4c9',
    '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39']


# Pool Data
pool_path = pathlib.Path('./Berno Daten/dataV2')
pool_filename = 'poolData.csv'
pool_file = pathlib.Path(pool_path/pool_filename)

# reserves / price / pool / blockNumber / logIndex
poolDF = pd.read_csv(pool_file)



'''
getReserves

INPUT: 
    start: Blocknumber. We look through data in blocks [start, start + 100000] per call.
    reserves: Information on reserves in pool with an activity more recent than block
        'start + 100000'.
    
OUTPUT:
    reserves: Updated dictionary including information with reserves of pools with
        an activity more recent than block 'start'

'''

def getReserves(start = 14800000, reserves = False):
    
    print(start)
    
    if not reserves:
        reserves = {}
        for index, poolInfo in poolDF.iterrows():
            reserves[poolInfo['pool']] = {
                'reserves': 0,
                'token0': poolInfo['token0'],
                'token1': poolInfo['token1']
            }
        
    # Open the reserves info
    reserve_path = pathlib.Path('./Berno Daten/dataV2/reserves')
    reserve_filename = 'reserves' + str(start) + '-' + str(start + 99999) + '.csv'
    reserve_file = pathlib.Path(reserve_path/reserve_filename)

    # reserves / price / pool / blockNumber / logIndex
    reservesDF = pd.read_csv(reserve_file)
    
    reservesDF.set_index(['pool'], inplace=True)
    
    for pool in reserves:
        if not reserves[pool]['reserves'] and pool in reservesDF.index:
            reserveHistory = reservesDF.loc[pool]
                
            # the exception handels reserves history of length one, as those
            # are converted directly into float instead of a list?
            try:
                reserves[pool]['reserves'] = reserveHistory.reserves.tolist()[0]
            except TypeError:
                reserves[pool]['reserves'] = reserveHistory.reserves
                
            print('updated pool:', pool, 'with reserves', reserves[pool]['reserves'])
    
    return reserves


'''
getWeights
        
INPUT:  
    start: Blocknumber. We look through data in blocks [start, start + 100000] per call.
    weights: for any ordered pair of tokens a number of trades of a certain size
OUTPUT:
    weights: the weights dictionary with values for each ordered pair of tokens
        increased by how many trades of that type occured between blocks 'start' and
        'start + 100000'.
'''

def getWeights(start = 14800000, weights = False):
    
    if not weights:
        weights = {}
        for token in tokenSlice:
            token1 = token.lower()
            weights[token1] = {
                'symb': tokenSlice[token]
            }
            for token2 in tokenSlice:
                token2 = token2.lower()
                weights[token1][token2] = {
                    'totalVol': 0,
                    'buckets' : {
                        'bucket0': {
                            'count':    0,
                            'rangeLow':0,
                            'rangeUp': 32,
                            'tradesize':10
                        },
                        'bucket1': {
                            'count':    0,
                            'rangeLow':32,
                            'rangeUp': 320,
                            'tradesize':100
                        },
                        'bucket2':  {
                            'count':    0,
                            'rangeLow':320,
                            'rangeUp': 3200,
                            'tradesize':1000
                        },
                        'bucket3':  {
                            'count':    0,
                            'rangeLow':3200,
                            'rangeUp': 32000,
                            'tradesize':10000
                        },
                        'bucket4':  {
                            'count':    0,
                            'rangeLow':32000,
                            'rangeUp': -1,
                            'tradesize':100000
                        }
                    }
                }

    # Open the swap info
    swap_path = pathlib.Path('./Berno Daten/dataV2/volumeData')
    swap_filename = 'swaps' + str(start) + '-' + str(start + 99999) + '.csv'
    swap_file = pathlib.Path(swap_path/swap_filename)

    # tradeVol / tokenIn / tokenOut / blockNumber / logIndex / transactionHash
    df = pd.read_csv(swap_file)

    for index, trade in df.iterrows():
        tokenIn = trade['tokenIn']
        tokenOut = trade['tokenOut']
        tradeVol = trade['tradeVol']
            
            
        if (tokenOut in weights) and (tokenIn in weights):          
                
            weights[tokenIn][tokenOut]['totalVol'] += tradeVol
            
            buckets = weights[tokenIn][tokenOut]['buckets']
            for bucket in buckets:
                if buckets[bucket]['rangeLow'] <= tradeVol and (tradeVol < buckets[bucket]['rangeUp'] or -1 == buckets[bucket]['rangeUp']):
                    buckets[bucket]['count'] += 1
                    
    return weights



'''
MAIN CODE:
    
gets weights and reserves for pools between blocks 'start' and 'end' and saves
    the information in the 'config.json' file.
'''

start = 10100000
step = 100000
end = 12800000

weights = False
reserves= False
size = len(poolSlice)
tokenSlice = {}
for pool in poolSlice:
    tokenSlice[pool] = tokens[pool]

for blocks in range(start, end, step):
    print(blocks)
    weights = getWeights(blocks, weights)
    reserves = getReserves(end - (blocks - start), reserves)
  

filename = 'config.json'
file = pathlib.Path(filename)
with open(file, "w") as f:
    config = {
        'blocks': {
            'start': start,
            'end': end
        },
        'size': size,
        'weights': weights,
        'reserves': reserves
    }
    json.dump(config, f)
    
    