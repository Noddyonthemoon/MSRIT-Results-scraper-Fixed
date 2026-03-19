# Command line tool using Python to fetch the results of students from "https://exam.msrit.edu/"
# Refer the readme file for instructions on how to use the tool
# Made by Manish.M

import urllib.parse
import urllib.request
import ssl
from bs4 import BeautifulSoup
import optparse
import os

branches = ['CS', 'EC', 'IS', 'ME', 'ML', 'CH', 'CV', 'EE', 'TI', 'EI', 'IM', 'AT', 'BT']

def fetch_results(usn):
    final_res = "<tr>"
    
    # --- FIX: Using the direct GET URL found in the website's HTML ---
    # This bypasses the need for POST form submission, cookies, and tokens
    query_url = f"https://exam.msrit.edu/index.php/component/examresult/?usn={usn}&examId=59&task=getResult&bypass=1"

    req = urllib.request.Request(query_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            result_page = response.read().decode("utf-8")
    except Exception as e:
        print(f"Network error for {usn}: {e}")
        return None

    soup = BeautifulSoup(result_page, 'html.parser')
    
    try:
        name = soup.find("div", {"class": "uk-card uk-card-body stu-data stu-data1"}).find('h3').get_text(strip=True)
        sem = soup.find("div", {"class": "uk-card uk-card-body stu-data stu-data2"}).find('p').get_text(strip=True)[-1:]
        credits_registered = soup.find("div", {"class": "uk-card uk-card-default uk-card-body credits-sec1"}).find('p').get_text(strip=True)
        credits_earned = soup.find("div", {"class": "uk-card uk-card-default uk-card-body credits-sec2"}).find('p').get_text(strip=True)
        sgpa = soup.find("div", {"class": "uk-card uk-card-default uk-card-body credits-sec3"}).find('p').get_text(strip=True)
        cgpa = soup.find("div", {"class": "uk-card uk-card-default uk-card-body credits-sec4"}).find('p').get_text(strip=True)

        final_res += "<td>" + usn + "</td>" + "<td>" + name + "</td>" + "<td>" + sem + "</td>" + "<td>" + credits_registered + "</td>"
        final_res += "<td>" + credits_earned + "</td>" + "<td>" + sgpa + "</td>" + "<td>" + cgpa + "</td>"
        final_res += "<td><table><tr><th>Code</th><th>Subject</th><th>Creds registered</th><th>Creds earned</th><th>Grade</th></tr>"

        res = soup.find("table", {"class": "uk-table uk-table-striped res-table"}).find_all("tr")[1:]
        results = []
        for item in res:
            r = []
            td_data = item.find_all('td')
            final_res += "<tr>"
            for x in td_data:
                r.append(x.get_text(strip=True))
                final_res += "<td>" + x.get_text(strip=True) + "</td>"
            final_res += "</tr>"
            results.append(r)

        final_res += "</table></td></tr>"

    except Exception as e:
        # --- DEBUGGER: If scraping fails, save the page so we can see why ---
        error_filename = f"error_log_{usn}.html"
        with open(error_filename, "w", encoding="utf-8") as err_file:
            err_file.write(result_page)
        
        print(f"{usn} not found or blocked. Checked saved file: {error_filename} to see server response.")
        return None

    return final_res


def is_int(y):
    try:
        int(y)
        return True
    except ValueError:
        return False


def validate_parameters(year, branch, max_range, start, parser):
    if not year or not branch or not max_range or not start:
        print(parser.usage)
        exit(0)
    else:
        branch = branch.upper()
        
        if is_int(year):
            if len(year) == 2:
                pass
            else:
                print("Enter only the last 2 digits for year (yy)")
                exit(1)
        else:
            print("The year should be an integer")
            exit(2)
        
        if branch in branches:
            pass
        else:
            print("Enter a valid branch extension such as: ")
            print(" ".join(branches))
            exit(3)

        if is_int(max_range):
            pass
        else:
            print("Enter a valid integer for max range of USNs")
            exit(4)
            
        if is_int(start):
            pass
        else:
            print("Enter a valid integer for starting USN")
            exit(5)


def make_usn(y, b, n):
    usn = '1MS' + y + b 
    num = str(n)

    if len(num) < 2:
        usn = usn + '00' + num
    elif len(num) < 3:
        usn = usn + '0' + num
    else:
        usn = usn + num

    return usn


def main():
    parser = optparse.OptionParser('Usage: ' + '-y <year(yy)> -b <branch extension(XX)> -m <max range of USN> -s <start USN>')
    parser.add_option('-y', '--year', dest='year', action="store", type='string', help='specify the last two digits of the year')
    parser.add_option('-b', '--branch', dest='branch', action="store", type='string', help='specify the branch extension')
    parser.add_option('-m','--max', dest='max', action="store", type='string', help='specify the number of results to fetch')
    parser.add_option('-s','--start', dest='start', action="store", type='string', default='1', help='specify the starting USN')
    (options, args) = parser.parse_args()

    year = options.year
    branch = options.branch
    max_range = options.max
    start = options.start

    validate_parameters(year, branch, max_range, start, parser)
    
    branch = branch.upper()

    text = """<html>
            <head>
                <title>Results</title>
                <style>
                    td, th {
                         border: 1px solid #dddddd;
                         text-align: left;
                         padding: 8px;
                    }
                </style>
            </head>
            <body>
                <table>
                    <tr><th>USN</th><th>Name</th><th>Sem</th><th>Creds registered</th><th>Creds earned</th><th>SGPA</th><th>CGPA</th><th>Subject-wise results</th></tr>"""

    with open('results.html', 'w', encoding='utf-8') as f:
        f.write(text)

        # Updated loop to use the starting parameter
        start_val = int(start)
        for i in range(start_val, start_val + int(max_range)):
            usn = make_usn(year, branch, i)
            print(f"Fetching results for {usn}...")
            r = fetch_results(usn)
            
            if r:
                f.write(r)
                print(f"Successfully wrote {usn} to results.html")
                # Clean up error file if successful on a retry
                if os.path.exists(f"error_log_{usn}.html"):
                    os.remove(f"error_log_{usn}.html")

        closing_text = """          </table>
                        </body>
                    </html>
        """
        f.write(closing_text)

    print("\nProcess finished.")


if __name__ == '__main__':
    main()
