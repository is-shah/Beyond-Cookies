import time 
import pandas as pd 
import csv 
import logging 
from selenium.webdriver.common.by import By
from datetime import datetime
import bs4 
import os 
from bannerclick.utility.utilityMethods import page_lang , find_btns_by_list ,get_cmp_name_nc
from bannerclick.utility.elementMethods import get_els_from_root , pruning_btns
from bannerclick.utility.textMethods import extend_all_words, concat_with_or, to_xpath_text, to_xpath_class, to_xpath_id
from bannerclick.utility.dictWords import *
from bannerclick.utility.dictpolicy import *
from bannerclick.config import *
from detect_links import *
import bannerclick.config as config
from detect_link import * 

def extract_banner_text(banner_element, shadow_host, driver):

    """Extract text from banner element, handling shadow DOM if necessary"""
    try:
        # Try to get shadow root content if available
        if shadow_host:
            try:
                shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
                if shadow_root:
                    html = shadow_root.get_attribute('innerHTML')
                else:
                    html = banner_element.get_attribute('outerHTML')
            except:
                html = banner_element.get_attribute('outerHTML')
        else:
            html = banner_element.get_attribute('outerHTML')
        
        soup = bs4.BeautifulSoup(html, 'html.parser')
 
        
        # Remove all button elements and their children
        for button in soup.find_all('button'):
            button.decompose()
        

        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        logging.error(f"Error extracting banner text: {e}")
        return ""

# def extract_banner_text(banner_element, shadow_host, driver):
#     """
#     Extract all text from a cookie banner, ensuring:
#     - Shadow DOM is handled
#     - Collapsible sections are expanded
#     - Lazy-loaded or hidden text is included
#     """
#     try:
#         # --- Step 1: Get the correct HTML container (shadow DOM or regular DOM) ---
#         if shadow_host:
#             try:
#                 shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
#                 html = shadow_root.get_attribute('innerHTML') if shadow_root else banner_element.get_attribute('outerHTML')
#             except:
#                 html = banner_element.get_attribute('outerHTML')
#         else:
#             html = banner_element.get_attribute('outerHTML')
        
#         soup = bs4.BeautifulSoup(html, 'html.parser')

#         # --- Step 2: Expand collapsible sections universally (click arrows/toggles) ---
#         try:
#             toggles = banner_element.find_elements(By.XPATH, ".//*[contains(@class,'arrow') or contains(@class,'toggle') or contains(@class,'expand')]")
#             for toggle in toggles:
#                 try:
#                     if "opened" not in toggle.get_attribute("class"):
#                         driver.execute_script("arguments[0].click();", toggle)
#                         time.sleep(0.4)  # Give time for expansion/lazy-load
#                 except:
#                     continue
#         except:
#             pass

#         # After expanding, re-fetch full HTML (in case new nodes loaded)
#         if shadow_host:
#             try:
#                 shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
#                 html = shadow_root.get_attribute('innerHTML') if shadow_root else banner_element.get_attribute('outerHTML')
#             except:
#                 html = banner_element.get_attribute('outerHTML')
#         else:
#             html = banner_element.get_attribute('outerHTML')

#         soup = bs4.BeautifulSoup(html, 'html.parser')

#         # --- Step 3: Remove buttons and interactive junk ---
#         for button in soup.find_all(['button', 'input']):
#             button.decompose()

#         # --- Step 4: Extract visible + hidden text ---
#         text_parts = []
#         for el in soup.find_all(True):  # All tags
#             txt = el.get_text(" ", strip=True)
#             if txt:
#                 text_parts.append(txt)

#         return " ".join(text_parts)

#     except Exception as e:
#         logging.error(f"Error extracting banner text: {e}")
#         return ""


def find_btns_by_list(banner, word_list, lang, html_attr, ):
    nom_words = extend_all_words(word_list, lang)
    con_str = concat_with_or(nom_words)
    btns = []
    try:
        if not html_attr:
            btns = banner.find_elements(By.XPATH, to_xpath_text(con_str))
        else:
            btns.extend(banner.find_elements(By.XPATH, to_xpath_class(con_str)))
            btns.extend(banner.find_elements(By.XPATH, to_xpath_id(con_str)))
    except:
        pass
    pruning_btns(btns)
    return btns


def handle_edge_cases(banner_element,list_of_words,shadow_host=None,non_explicit=False):
    
    btns = find_btns_by_list(banner_element,list_of_words,config.this_lang,non_explicit)

    if shadow_host is not None:
        btns = get_els_from_root(shadow_host,btns)

    return btns 

def structured_button_info(btn):
    """Extract structured information from a button element"""
    return {
        "text": btn.text.strip(),
        "href": btn.get_attribute("href").strip() if btn.get_attribute("href") else None,
        "class": btn.get_attribute("class").strip() if btn.get_attribute("class") else None,
        "id": btn.get_attribute("id").strip() if btn.get_attribute("id") else None,
        "tag" : btn.tag_name.strip() if btn.tag_name else None,
    }
    

def extract_banner_links(banner_element, shadow_host=None):
    """Extract all hyperlinks from banner with their href and text"""
    links = []
    
    logging.getLogger("openwpm").info(f"Languge of website detected: {config.this_lang}")

    if config.this_lang in Policy_words_hyperlinks.keys():
        
        try:
            # Handle shadow DOM if shadow_host is given
            if shadow_host:
                try:
                    shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
                    if shadow_root:
                        a_tags = shadow_root.find_elements(By.TAG_NAME, "a")
                    else:
                        a_tags = banner_element.find_elements(By.TAG_NAME, "a")
                except Exception as e:
                    # Fallback to normal DOM if shadow root access fails
                    a_tags = banner_element.find_elements(By.TAG_NAME, "a")
            else:
                a_tags = banner_element.find_elements(By.TAG_NAME, "a")
            
            # Extract links
            for link in a_tags:
                href = link.get_attribute("href")
                if href:  # Filter out empty or None hrefs
                    link_info = {
                        "text": link.text.strip().lower(),
                        "href": href.strip().lower(),
                    }
                    links.append(link_info)

            links , hash_links = filter_links(links)
            links,Uneven_schema_links = link_segregation(links)

            for link in links:
                logging.getLogger("openwpm").info(f"Link found: {link['text']} - {link['href']}")
            # Match policy links if found
            logging.getLogger("openwpm").info(f"Links found: {len(links)}")

        
            if links or Uneven_schema_links:
                Privacy_Policy = find_policy_link(links, Uneven_schema_links, Policy_token='Privacy Keywords')
                logging.getLogger("openwpm").info(f"Privacy Policy Link: {Privacy_Policy}")
                Cookie_Policy = find_policy_link(links, Uneven_schema_links, Policy_token='Cookie Keywords')
                logging.getLogger("openwpm").info(f"Cookie Policy Link: {Cookie_Policy}")
                Terms_Policy = find_policy_link(links, Uneven_schema_links, Policy_token='Terms Keywords')
                logging.getLogger("openwpm").info(f"Terms Policy Link: {Terms_Policy}")

                output_links = [Privacy_Policy, Cookie_Policy, Terms_Policy]
                Policy_tokens = ['Privacy Keywords', 'Cookie Keywords', 'Terms Keywords']
                Possible_links = []
                for i in range(3):
                    if not output_links[i]:
                       output_links[i] = search_partial_keywords_in_hyperlinks(links, Policy_token=Policy_tokens[i])
                       Possible_links.append(output_links[i])
                    
                for link in Possible_links:
                    logging.getLogger("openwpm").info(f"Possible link found: {link}")

                return output_links
            else:
                response = "No links found in the banner"
                logging.getLogger("openwpm").info(response)
                return response
        
        except Exception as e:
            logging.getLogger("openwpm").error(f"Error extracting links from banner: {e}")
    else :
        output_flag = f"language out of scope: {config.this_lang}"
        logging.getLogger("openwpm").info(output_flag)
        # try for english keywords 
        config.this_lang = 'en'
        flag = [output_flag,extract_banner_links(banner_element, shadow_host)]
        
        return flag

# else:
            #     btns = []

            #     for doc in Standard_docs:
            #         btns.extend(handle_edge_cases(driver,banner_element,doc,shadow_host))

            #     structured_buttons = [structured_button_info(btn) for btn in btns if btn.is_displayed()]
                
            #     return structured_buttons
