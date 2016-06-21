import splinter
import pickle
import time
import smtplib
from email.mime.text import MIMEText
import numpy as np

def visit_stock_webpage(stock_num):
    """
    visit certain stock page data
    :param stock_num: the stock number
    :return: the stock webpage
    """
    browser = splinter.Browser()
    browser.visit('http://www.hon4u.com/Quotes/StartPage.aspx')
    browser.fill('qAuto2', stock_num)  # fill in search box the stock number.
    browser.find_by_id('Button1').click()
    return browser

def get_stock_price(browser):
    """
    get the current stock price from the stock webpage data
    :param browser: the browser instance of stock webpage
    :return: current price
    """
    time.sleep(5)
    price = browser.find_by_xpath('//*[@id="ActionName1"]/table/tbody/tr/td[5]')
    return float(price.first.text)

def get_all_stock_prices(stock_list):
    """
    loop over stocks in stock_lists scrap their data and return their prices
    """
    prices = dict()
    for stock_num in stock_list:
        browser = visit_stock_webpage(stock_num)
        prices[stock_num] = get_stock_price(browser)
        browser.quit()
    return prices

def save_baseline_data(prices):
    " save today stocks prices for comparison in the future"
    today = time.strftime("%d%m%Y")
    pickle.dump(prices, open("baseline_"+today+".p", "wb"))

def get_baseline_data(baseline_date):
    " load stocks prices for comparison to a given date in the past"
    baseline_file = "baseline_"+ baseline_date + ".p"
    return pickle.load( open(baseline_file, "rb" ))

def check_changes(baseline_prices, current_prices, threshold):
    """
    compare current to baseline prices and check if given % threshold is exceeded"
    :param baseline_prices: from previous date in which data was saved
    :param current_prices: from today
    :param threshold: the % of stock change from baseline we want to get notification about
    :return: exceed_thresh: boolean (True if threshold exceeded, False if not), value_change: the % of value change
    """
    value_change, exceed_thresh = dict(), dict()
    for stock_num in stock_list:
        base_price = baseline_prices[stock_num]
        curr_price = current_prices[stock_num]
        if base_price !=0:
            value_change[str(stock_num)] = 100*float((curr_price-base_price)/base_price)
        else:
            value_change[str(stock_num)] = np.nan
        if np.abs(curr_price-base_price) > base_price*threshold:
            exceed_thresh[str(stock_num)] = True
        else:
            exceed_thresh[str(stock_num)] = False
    return exceed_thresh, value_change

def prep_report(stocks_mapping, prices_changes, exceed_thresh):
    """
    prepare the stocks data report in txt file
    :param stocks_mapping: map stock name to stock number (dict)
    :param prices_changes: stock number and price (dict)
    :param exceed_thresh: stock number and if it exceeded threshold (dict)
    :return:
    """
    txt = open('temp', 'r+')
    for k,v in stocks_mapping.iteritems():
        line = "{:<10} : {:05.2f} | {}".format(k, prices_changes[str(v)], exceed_thresh[str(v)])
        txt.write(line)
    return txt

def send_notification(report, emails):
    " send change report in email"
    msg = MIMEText(report.read())
    report.close()
    server = smtplib.SMTP('gmail-smtp-in.l.google.com:25')
    server.starttls()
    # server.login('username','password')
    server.sendmail(emails['from'], emails['to'], msg.as_string())
    server.quit()

# TODO: without login
# http://stackoverflow.com/questions/24270715/send-anonymous-mail-from-local-pc
# http://stackoverflow.com/questions/9763455/how-to-send-a-mail-directly-to-smtp-server-without-authentication

# params:
baseline_date     = '12062016'  # baseline date for peaking prices
threshold         = .25         # percentage change in price
save_baseline     = False        # True - get baseline data and save it, False - load previous
notification      = 'all'       # 'all' = whether exceeds thresh, and value changes, 'thresh' - only if exceed thresh, 'value_change'
notification_freq = 'weekly'
emails            = {'from': 'shirisimon85@gmail.com', 'to': 'shirisimon85@gmail.com'}

# load stocks_data
stocks_mapping = pickle.load(open("stocks_mapping.p", "rb"))
stock_list = stocks_mapping.values()
# save baseline
if save_baseline:
    baseline_prices = get_all_stock_prices(stock_list)
    save_baseline_data(baseline_prices)
else:
    baseline_prices = get_baseline_data(baseline_date)
# check for prices changes:
current_prices = baseline_prices # get_all_stock_prices(stock_list)
exceed_thresh, prices_changes = check_changes(baseline_prices, current_prices, threshold)
# prep and send report
report = prep_report(stocks_mapping, prices_changes, exceed_thresh)
send_notification(report, emails)


# TODO:
# add send notification function and debug
# add gold
# check how to run frequently and from where, how to set the frequency check parameter...
# make a website to publish