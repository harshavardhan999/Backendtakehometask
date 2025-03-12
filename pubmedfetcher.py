import requests
import csv
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

ACADEMIC_KEYWORDS = ["university", "college", "institute", "lab", "hospital", "school", "clinic", "medical center"]
COMPANY_KEYWORDS = ["pharma", "biotech", "therapeutics", "biosciences", "genomics"]

def fetch_papers(query: str, max_results: int = 100, debug: bool = False) -> str:
    """Fetches research papers from PubMed API and returns full XML data."""
    
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": f"{query} NOT retracted[Publication Type]",
        "retmode": "json",
        "retmax": max_results
    }

    response = requests.get(search_url, params=params)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} - {response.text}")

    paper_ids = response.json().get("esearchresult", {}).get("idlist", [])

    if debug:
        print(f"Found {len(paper_ids)} papers: {paper_ids}")

    if not paper_ids:
        return ""

    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    response = requests.get(fetch_url, params={"db": "pubmed", "id": ",".join(paper_ids), "retmode": "xml"})

    if response.status_code != 200:
        raise Exception(f"Error fetching paper details: {response.status_code} - {response.text}")

    return response.text

def process_papers(xml_data: str, debug: bool = False) -> List[Dict[str, Any]]:
    """Processes XML papers, extracting authors and affiliations."""
    
    if not xml_data:
        return []

    root = ET.fromstring(xml_data)
    results = []

    for article in root.findall(".//PubmedArticle"):
        paper_id = article.find(".//PMID").text
        title = article.find(".//ArticleTitle").text if article.find(".//ArticleTitle") is not None else "No Title"

        # Skip retracted papers
        if any(pub.text.lower() in ["retracted publication", "retraction of publication"] for pub in article.findall(".//PublicationType")) or "retracted:" in title.lower():
            continue
        
        pub_date = article.find(".//PubDate/Year")
        pub_date = pub_date.text if pub_date is not None else "Unknown"
        
        authors, non_academic_authors, company_affiliations = [], [], set()

        for author in article.findall(".//Author"):
            last_name = author.find("LastName")
            first_name = author.find("ForeName")
            name = f"{first_name.text} {last_name.text}" if first_name is not None and last_name is not None else "Unknown"
            authors.append(name)

            affiliation = author.find(".//AffiliationInfo/Affiliation")
            if affiliation is not None:
                affiliation_text = affiliation.text.lower()

                if not any(keyword in affiliation_text for keyword in ACADEMIC_KEYWORDS):
                    non_academic_authors.append(name)

                if any(keyword in affiliation_text for keyword in COMPANY_KEYWORDS):
                    company_affiliations.add(affiliation.text)

        results.append({
            "PubmedID": paper_id,
            "Title": title,
            "Publication Date": pub_date,
            "Authors": ", ".join(authors),
            "Non-academic Author(s)": ", ".join(non_academic_authors) if non_academic_authors else "None",
            "Company Affiliation(s)": ", ".join(company_affiliations) if company_affiliations else "None",
            "Corresponding Author Email": "N/A"
        })

    if debug:
        print(f"Processed {len(results)} papers.")

    return results

def save_to_csv(data: List[Dict[str, Any]], filename: str):
    """Saves results to CSV."""
    if not data:
        print("No data to save.")
        return
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    print(f"Data saved to {filename}")
