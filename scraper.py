import requests
from bs4 import BeautifulSoup
import time

def scrape_yellow_pages(keyword, location, max_pages):
    base_url = f"https://www.yellowpages.com.au/search/listings?clue={keyword}&locationClue={location}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    }
    listings = []
    seen_businesses = set()  # Set to track unique businesses by name
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}&pageNumber={page}"
        print(f"Scraping {url}")
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve data from {url}")
            continue
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        for item in soup.find_all("div", class_=["FreeListing", "PaidListing"]):  # Adjusted the class to match actual content containers
            try:
                business_name = item.find("h3", class_="MuiTypography-root").text.strip()
                if business_name in seen_businesses:  # Skip duplicates
                    continue
                seen_businesses.add(business_name)  # Mark as seen
                
                phone = item.find("button", class_="ButtonPhone")
                phone_number = phone.text.strip() if phone else "N/A"
                website_tag = item.find("a", class_="ButtonWebsite")
                website_url = website_tag['href'] if website_tag else "N/A"
                address_tag = item.find("p", class_="MuiTypography-body2") or item.find("a", class_="MuiLink-root")
                address = address_tag.text.strip() if address_tag else "N/A"
                
                listings.append({
                    "Business Name": business_name,
                    "Phone": phone_number,
                    "Website": website_url,
                    "Address": address
                })
                
            except AttributeError as e:
                print(f"An error occurred while extracting details for an item: {e}")
        
        # Optional delay to avoid being blocked
        time.sleep(2)
    
    return listings

# Flask Application (app.py)
from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
from scraper import scrape_yellow_pages  # Import the updated scraper function

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get user input from the form
        keyword = request.form.get('keyword')
        location = request.form.get('location')
        max_pages = int(request.form.get('max_pages'))

        # Call the updated scraper function
        listings = scrape_yellow_pages(keyword, location, max_pages)

        # Save results to a CSV file
        output_file = 'yellow_pages_results.csv'
        df = pd.DataFrame(listings)
        df.to_csv(output_file, index=False)

        # Return a JSON response indicating success
        return jsonify({"status": "success"})

    return render_template('index.html')

@app.route('/download')
def download():
    output_file = 'yellow_pages_results.csv'
    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
