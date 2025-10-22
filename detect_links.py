import bannerclick.config as config
from bannerclick.utility.dictpolicy import *
from urllib.parse import urlparse 
import logging
# regex patterns 
import re 
PARTIAL_POLICY_TITLES = [
    'policy', 'policies', 'cookie', 'security',
    'statement', 'terms', 'notice']

EXACT_POLICY_TITLES = [
    "privacy policy", "privacy statement", "privacy", "privacy notice",
    "cookie policy", "your privacy", "your privacy rights"]


def get_abs_link(href, top_url, sanitize=True):
    if href == "#":
        return href
    if sanitize:
        href = sanitize_link(href)
    try:
        return urljoin(top_url, href)
    except ValueError:
        pass


def remove_white_space(text):
    """Remove new lines and tabs."""
    return text.strip().replace("\r", "").replace("\n", "").replace("\t", "")


def sanitize_link(href):
    # some sites link to both site.com/privacy and site.com/privacy/
    href = href.rstrip('/').strip()
    return remove_white_space(href)


def is_internal_http_link(href, page_domain):
    if href.startswith("tel:") or href == "#":
        return False
    try:
        parsed = urlparse(href)
    except ValueError:
        return False
    if not parsed.scheme:  # relative link
        return True
    if parsed.scheme in ["http", "https"]:  # absolute http(s) link
        return get_tld_or_host(href) == page_domain


def filter_common_crawl_links(links):
    return [
        link for link in links
        if "text" in link and "path" in link and
           link["path"] == "A@/href" and
           link["url"] and
           not link["text"].startswith("http")
    ]


def get_partial_matching_link(links_dict):
    privacy_links = {text: link for text, link in  getattr(links_dict,iteritems)()
        if "privacy" in text}

    if not privacy_links:
        return None

    for keyword in PARTIAL_POLICY_TITLES:
        tmp_links = [
            link for text, link in  getattr(privacy_links,iteritems)() if keyword in text]
        if tmp_links:
            return tmp_links[0]
    return None


def search_hypertext(link,Policy_token : str ,source_dict=Policy_words_hypertext):
    logging.getLogger('openwpm').info('Hypertext function instatiated')
    entire_link_info = {}
    if link['text'] is None  or link['text'] == '':
        logging.getLogger('openwpm').info('No text found in the link')
        return entire_link_info
    
    for key , val in source_dict[config.this_lang][Policy_token].items():
        #substring search in the text
        if key in link['text']:
            entire_link_info = {
                key : {link['text'] : link['href']}
            }
            break
        # if the key is not in the text, check if the value is in the text
      
        elif val.lower() in link['text']:
            entire_link_info = {
                key : {link['text'] : link['href']}
            }
            break 
            
    return entire_link_info    




def get_non_policy_link(links_dict, page_url):
    page_domain = get_tld_or_host(page_url)
    for text, link in getattr(links_dict,iteritems)():
        if "privacy" in text or not is_internal_http_link(
                link["url"], page_domain):
            continue
        return get_abs_link(link["url"], page_url)
 

def search_function(link,Policy_token : str,source_dict=Policy_words_hyperlinks) :
    entire_info = {}
    logging.getLogger('openwpm').info('hyperlink function instatiated')
    for key,val in source_dict[config.this_lang][Policy_token].items():
        if key in link['href']:
           entire_info = {
                key : {link['text'] : link['href']}
                }
          
           break
        elif val.lower() in link['href']:
            entire_info = {
                key : {link['text'] : link['href']}
            }
 
            break
        
    return entire_info 


def remove_cmp_links(links):
    
    Uneven_schema_links = []
    valid_links = []
    
    for link in links:
        try :
            parsed = urlparse(link['href'])        
            if parsed.scheme in ['http','https'] :
                valid_links.append(link)

            elif parsed.scheme == '':
                # inner pages 
                current_url = config.driver.current_url
                parsed = urlparse(current_url)
                updated_href = f"{parsed.scheme}://{parsed.netloc}{link['href']}"
                link['href'] = updated_href
                valid_links.append(link)

            else :
                Uneven_schema_links.append(link)
                logging.getLogger('openwpm').info('Uneven schema links found')
                # logging.getLogger('openwpm').info('exceptional schemas are there ')
        except Exception :
            continue

    return valid_links, Uneven_schema_links

def eliminate_links(links,Already_found_link):
    key = list(Already_found_link.keys())[0]
    index = next((i for i, val in enumerate(links) if val == Already_found_link[key]), None)
    if index is not None:
        links.pop(index)
        logging.getLogger('openwpm').info(f'Link {Already_found_link[key]} eliminated from the list')
    else:
        logging.getLogger('openwpm').info('Link not found in the list to eliminate')

def search_partial_keywords_in_hyperlinks(links,Policy_token : str):
    
    Possible_links = []
    
    for link in links:
        
        if search_function(link,Policy_token,source_dict=Partial_keyword_match):
            Possible_links.append(search_function(link,Policy_token,source_dict=Partial_keyword_match))
        elif search_hypertext(link,Policy_token,source_dict=Partial_keyword_match):
            Possible_links.append(search_hypertext(link,Policy_token,source_dict=Partial_keyword_match))
    
    return Possible_links


def search_in_hyperlinks(links,Policy_token : str):
    
    Policy_link = {}
    
    for link in links:
        if Policy_link:
            break 
        elif search_function(link,Policy_token):
            Policy_link = search_function(link,Policy_token)
        elif search_hypertext(link,Policy_token):
            Policy_link = search_hypertext(link,Policy_token)
    
    if Policy_link:
        eliminate_links(links, Policy_link)
    return Policy_link
                     




def filter_links(links):
    real_links = []
    zone_out_links = []
    for link in links:
        url = link['href']
        # either link is a placeholder or text is invisible - bot detections possibilities
        if not url or url.startswith("#") or url.endswith("#") or url == "/" or link['text'] is None or link['text'] == '' or is_fragment_link(url):
            zone_out_links.append(link)
        else:
            real_links.append(link)
    return real_links, zone_out_links

def is_fragment_link(href: str) -> bool:
    """Return True if href is just an internal fragment (https://domain.com/#section, etc.)"""
    parsed = urlparse(href)
    return bool(parsed.fragment) and (parsed.path == '' or parsed.path == '/') and parsed.netloc


def link_segregation(links):
    uneven_schema_links = []
    valid_links = []
    
    for link in links:
        try:
            parsed = urlparse(link['href'])
            current_domain = urlparse(config.driver.current_url).netloc.lower()
            
            if len(valid_links) == 3:
                break
            elif parsed.scheme in ['http', 'https'] and (parsed.netloc.lower() == current_domain):
                valid_links.append(link)
            elif not parsed.scheme:
                # inner pages - relative URLs
                current_url = config.driver.current_url
                parsed_current = urlparse(current_url)
                # updated_href = f"{parsed_current.scheme}://{parsed_current.netloc}{link['href']}"
                # link['href'] = updated_href
                valid_links.append(link)
            else:
                uneven_schema_links.append(link)
                # logging.getLogger('openwpm').info('Uneven schema links found')
                # logging.getLogger('openwpm').info('exceptional schemas are there')
        except Exception:
            continue
    
    return valid_links, uneven_schema_links




def find_policy_link(links,Uneven_schema_links,Policy_token : str):
 
    Policy_link = search_in_hyperlinks(links,Policy_token)
    if not Policy_link and Uneven_schema_links:
        logging.getLogger('openwpm').info('Search in Uneven schema links')
        for link in Uneven_schema_links:
            if search_hypertext(link,Policy_token):
                Policy_link = search_hypertext(link,Policy_token)
                break

    return Policy_link
