import argparse
from pubmedfetcher import fetch_papers, process_papers, save_to_csv

def main():
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed.")
    parser.add_argument("query", type=str, help="Search query for PubMed API.")
    parser.add_argument("-f", "--file", type=str, help="Save results to CSV file instead of printing.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()
    
    xml_data = fetch_papers(args.query, debug=args.debug)
    processed_papers = process_papers(xml_data, debug=args.debug)

    if args.file:
        save_to_csv(processed_papers, args.file)
    else:
        for paper in processed_papers:
            print(paper)

if __name__ == "__main__":
    main()
