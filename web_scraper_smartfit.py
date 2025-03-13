# This code is a web scraper I made for scraping Brasilian SmartFit franchises.
# I wrote as a task at job but I changed the main strategic takes to keep the company's data privacy
# This code can be optimized and I plan to update it in the near future

import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

pd.set_option('display.max_rows', None)  # Show all lines and rows
pd.set_option('display.max_columns', None)

########### STARTS THE DRIVERS AND OPENS THE INITIAL PAGE FOR SCRAPING ###########

driver = webdriver.Chrome()
url = "https://www.smartfit.com.br/academias"
driver.get(url)

########### DEFINES HOW MANY PIXELS TO SCROLL TO FIND THE "CARREGAR" (LOAD) BUTON ###########

scroll_position = 2000000
scroll_script = f"window.scrollTo(0, {scroll_position});"

########### SCROLLS THE PAGE UNTIL "CARREGAR" BUTON IS CLICKABLE, UNTIL THERE IS NO MORE "CARREGAR"(LOAD) BUTON TO INTERACT ###########
while True:
    try:
        driver.execute_script(scroll_script)
        button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "locations-v4-pagination-button"))
        )
        button.click()
    except TimeoutException:
        print("ALL ELEMENTS LOADED.")
        break

########### LOCATES THE HTML CLASS THAT HAS THE LINKS FOR EACH FRANCHISE UNIT PAGE (THATS NECESSARY BECAUSE THE CNPJ IS ONLY ON THEIR INDIVIDUAL PAGE) ###########
franchise_list=[]
address_list=[]
links_list=[]

franchises_links = driver.find_elements(By.CLASS_NAME,"locations-v4-location-card")
for link in franchises_links:
    link_text = link.find_element(By.CLASS_NAME,"locations-v4-location-card__figure")
    link_text = link_text.get_attribute('href')
    if link_text:
        links_list.append(link_text)
    else:
        links_list.append('LINK DOESNT EXISTS')  

########### LOCATES THE HTML CLASS THAT HAS THE NAMES AND ADDRESSES OF EACH FRANCHISE ###########
name_address = driver.find_elements(By.CLASS_NAME,"locations-v4-location-card")   
for a in name_address:
    b = a.find_elements(By.TAG_NAME, "smart-text")
    count =0

    for c in b:
        # print(c.text)
        if count ==1:
            franchise_list.append(c.text)
            print("FRANCHISE NAME FOUND")
           
        elif count ==2:
            print("ADDRESS FOUND")
            address_list.append(c.text)
            break

        else:
            print("count is 0")
            
        count +=1

########### CREATES A DTAA FRAME WITH THE GATHERED DATA ###########
d = {'FRANCHISE': franchise_list, 'FULL_ADDRESS' : address_list,'LINKS' : links_list}
df = pd.DataFrame(data=d)

# REGEX TO EXTRACT THE CITY FROM THE FULL ADDRESS.
df['CITY'] = df['FULL_ADDRESS'].str.extract(r'- .*?, (\D+) -')
df['CITY'] = df['CITY'].str.lower()

# REGEX TO EXTRACT THE STATE FROM THE FULL ADDRESS.
df['STATE'] = df['FULL_ADDRESS'].str.extract(r'([A-Za-z]{2})$')

df = df.drop_duplicates(subset=['FRANCHISE','FULL_ADDRESS','LINKS'])

links_list = df.loc[df["STATE"] == "SP", "LINKS"]

cnpj_list = []
franchise_name = []     

for link in links_list:
    driver.get(link)

    # Rolls to the botom of the page to load all the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)  # Evita bloqueios

    try:
        nome = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "show-locations-page__show-unit__name"))
        )
        franchise_name.append(nome.get_attribute("innerText").strip())
    except:
        franchise_name.append('Francise not found')

    try:
        cnpj_loja = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "show-locations-page__company__info"))
        )
        cnpj_list.append(cnpj_loja.get_attribute("innerText").strip())
    except:
        cnpj_list.append('CNPJ not found')

data = {'cnpj': cnpj_list}
df_cnpjs = pd.DataFrame(data)

# Make CNPJ a str type 
df_cnpjs['cnpj'] = df_cnpjs['cnpj'].astype(str)

# EXTRACTS only the CNPJ Nummber 
df_cnpjs['cnpj'] = df_cnpjs['cnpj'].str.extract(r'CNPJ: ([\d./-]+)')

# Remove rows that as a empty FRANCHISE name 
df = df[df['FRANCHISE'] != ""]

df.reset_index(drop=True, inplace=True)
df_cnpjs.reset_index(drop=True, inplace=True)

df_full = pd.concat([df,df_cnpjs],axis=1)

df_full.to_excel('leads_smartfit.xlsx', index=False)


