import time
import os
import requests
from dotenv import load_dotenv
from scholarly import scholarly
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import pandas as pd
from utils import load_config

# Load environment variables
load_dotenv()
wait = int(os.getenv("WAIT_TIME", 2)) 
gecko_path = os.getenv("FIREFOX_DRIVER_PATH")

config = load_config('config.yaml')

options = Options()
options.add_argument("--headless")

########################### Read Keywords ###########################
def read_keywords(file_path):
    with open(file_path, 'r') as file:
        keywords = [line.strip() for line in file if line.strip()]
    return keywords

########################### Fetch Paper ###########################
def fetch_paper(keyword, start_year, end_year, count):
    print(f"\n🔍 Searching for: {keyword}")
    papers = []
    try:
        search_query = scholarly.search_pubs(keyword, year_low=start_year, year_high=end_year)
        for _ in range(count):
            try:
                paper = next(search_query)
                papers.append({
                    "title": paper.get("bib", {}).get("title", "N/A"),
                    "url": paper.get("pub_url", "N/A")
                })
            except StopIteration:
                print("⚠️ No more results found.")
                break
    except Exception as e:
        print(f"❌ Error: {e}")
    return papers


########################### Get DOI ###########################
def get_doi_from_title(title):
    url = "https://api.crossref.org/works"
    params = {
        "query.title": title,
        "rows": 1
    }
    headers = {
        "User-Agent": "YourEmail@example.com"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        items = data.get("message", {}).get("items", [])
        if items:
            return items[0].get("DOI", "DOI not found")
        else:
            return "DOI not found"
    except Exception as e:
        return f"Error: {str(e)}"

########################### Get Reference and Citation ###########################
def get_ref_cit(paper_url):
    baseurl = 'https://quillbot.com/citation-generator'
    service = Service(executable_path=gecko_path)
    driver = webdriver.Firefox(service=service, options=options)
    
    ref_text = ""
    cite_text = ""
    
    try:
        driver.get(baseurl)
        driver.implicitly_wait(wait)
        
        try:
            close_button = driver.find_element(By.ID, "close")
            close_button.click()
        except:
            pass

        get_input = driver.find_element(By.XPATH, '//input[@placeholder="Search by title, URL, DOI, ISBN, or keywords"]')
        get_input.send_keys(paper_url)
        
        get_cite_button = driver.find_element(By.XPATH, '//button[span[text()="Cite"]]')
        get_cite_button.click()
        
        ref_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//p[@data-testid="bibliography-entry"]')))
        ref_text = ref_element.text
        
        cite_element = driver.find_elements(By.CSS_SELECTOR, 'span.MuiTypography-root.MuiTypography-bodyMedium.css-hjalds')
        if len(cite_element) >= 2:
            cite_text = cite_element[1].text
        else:
            cite_text = "Citation not found"
    
    except Exception as e:
        print(f"An Error Occurred: {e}")
    
    finally:
        driver.quit()
    
    return ref_text, cite_text

########################### Get Full Citation Info ###########################
def get_citation_info(paper_title, paper_url):
    paper_info = {
        "doi": "Not found",
        "references": "Not available",
        "citations": "Not available"
    }
    
    doi = get_doi_from_title(paper_title)
    paper_info["doi"] = doi

    if doi != "DOI not found" and not doi.startswith("Error"):
        doi_url = f"https://doi.org/{doi}"
        print(f"Attempting to get citation info from DOI: {doi_url}")
        try:
            reference, citation = get_ref_cit(doi_url)
            if reference and citation:
                paper_info["references"] = reference
                paper_info["citations"] = citation
                return paper_info
        except Exception as e:
            print(f"Error while fetching citation info from DOI: {e}")
    
    if paper_url != 'URL not available':
        print(f"Attempting to get citation info from URL: {paper_url}")
        try:
            reference, citation = get_ref_cit(paper_url)
            if reference and citation:
                paper_info["references"] = reference
                paper_info["citations"] = citation
        except Exception as e:
            print(f"Error while fetching citation info from URL: {e}")
    else:
        print("No valid URL available for citation info")
    
    return paper_info

########################### Main Execution ###########################
# def get_ref_citation():
#     input_file = config['KEYWORD_FILE']
#     start_year = 2020
#     end_year = 2025
#     output_csv_path = config['PAPER_CITATION']
#     count=2
    
#     keywords = read_keywords(input_file)
#     output_data = []

#     for keyword in keywords:
#         papers = fetch_paper(keyword, start_year, end_year, count=count)
#         for paper in papers:
#             print(f"\n📄 Result for: {keyword}")
#             print(f"Title: {paper['title']}")
#             print(f"URL: {paper['url']}")
#             print("-" * 80)

#             citation_info = get_citation_info(paper['title'], paper['url'])

#             output_data.append({
#                 "keywords": keyword,
#                 "title": paper['title'],
#                 "url": paper['url'],
#                 "references": citation_info["references"],
#                 "citation": citation_info["citations"]
#             })
#             time.sleep(1)

#     # Sort the data by keyword
#     output_data_sorted = sorted(output_data, key=lambda x: x['keywords'].lower())

#     # Convert to DataFrame and save using pandas
#     df = pd.DataFrame(output_data_sorted)
#     df.to_csv(output_csv_path, index=False, encoding='utf-8')

#     print(f"\n✅ Results saved to {output_csv_path}")


# get_ref_citation()

def get_ref_citation(references: list):
    output_csv_path = config['PAPER_CITATION']
 
    output_data = []
    for item in references:
        output_data.append({
            "keywords"  : item.get("keyword", ""),
            "title"     : item.get("title", ""),
            "references": item.get("reference", ""),
            "citation"  : item.get("citation", ""),
        })
 
    output_data_sorted = sorted(output_data, key=lambda x: x['keywords'].lower())
 
    df = pd.DataFrame(output_data_sorted)
    df.to_csv(output_csv_path, index=False, encoding='utf-8')
 
    print(f"\n✅ {len(output_data_sorted)} references saved to {output_csv_path}")