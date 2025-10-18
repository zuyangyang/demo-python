def buy_stock(prices):
    ret = 0

    if len(prices) < 2:
        return ret
    
    min_price = prices[0]
    for price in prices[1:]:
        ret = max(ret, price - min_price)
        min_price = min(min_price, price)
    
    return ret

print(buy_stock([7, 1, 5, 3, 6, 4]))