# Command line tool using Python to fetch the results of students from "https://exam.msrit.edu/"
# Refer the readme file for instructions on how to use the tool
# Made by Manish.M

import urllib.request
import ssl
from bs4 import BeautifulSoup
import argparse
import os

branches = ['CS', 'EC', 'IS', 'ME', 'ML', 'CH', 'CV', 'EE', 'TI', 'EI', 'IM', 'AT', 'BT', "CY", "CI"]
exam_id = "59"


def fetch_results(usn):
    query_url = f"https://exam.msrit.edu/index.php/component/examresult/?usn={usn}&examId={exam_id}&task=getResult&bypass=1"

    req = urllib.request.Request(query_url)
    req.add_header(
        'User-Agent',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            result_page = response.read().decode("utf-8")
    except Exception as e:
        print(f"Network error for {usn}: {e}")
        return None

    soup = BeautifulSoup(result_page, 'html.parser')

    try:
        name = soup.find("div", {"class": "uk-card uk-card-body stu-data stu-data1"}).find('h3').get_text(strip=True)
        sem = soup.find("div", {"class": "uk-card uk-card-body stu-data stu-data2"}).find('p').get_text(strip=True)
        credits_registered = soup.find("div", {"class": "uk-card uk-card-default uk-card-body credits-sec1"}).find('p').get_text(strip=True)
        credits_earned = soup.find("div", {"class": "uk-card uk-card-default uk-card-body credits-sec2"}).find('p').get_text(strip=True)
        sgpa = soup.find("div", {"class": "uk-card uk-card-default uk-card-body credits-sec3"}).find('p').get_text(strip=True)
        cgpa = soup.find("div", {"class": "uk-card uk-card-default uk-card-body credits-sec4"}).find('p').get_text(strip=True)

        row = f"""
        <tr>
            <td>{usn}</td>
            <td>{name}</td>
            <td>{sem}</td>
            <td>{credits_registered}</td>
            <td>{credits_earned}</td>
            <td>{sgpa}</td>
            <td>{cgpa}</td>
            <td>
                <table>
                    <tr>
                        <th>Code</th>
                        <th>Subject</th>
                        <th>Creds registered</th>
                        <th>Creds earned</th>
                        <th>Grade</th>
                    </tr>
        """

        res = soup.find("table", {"class": "uk-table uk-table-striped res-table"}).find_all("tr")[1:]
        for item in res:
            td_data = item.find_all('td')
            row += "<tr>"
            for x in td_data:
                row += f"<td>{x.get_text(strip=True)}</td>"
            row += "</tr>"

        row += """
                </table>
            </td>
        </tr>
        """
    except Exception:
        error_filename = f"error_log_{usn}.html"
        with open(error_filename, "w", encoding="utf-8") as err_file:
            err_file.write(result_page)

        print(f"{usn} not found or blocked. Check {error_filename}")
        return None

    return row


def validate_parameters(year, branch, max_range, start):
    if not year or not branch or not max_range:
        raise ValueError("year, branch and max are required")
    branch = branch.upper()

    if not year.isdigit() or len(year) != 2:
        raise ValueError("Enter only last 2 digits for year, like 22")

    if branch not in branches:
        raise ValueError("Invalid branch: " + " ".join(branches))

    if not max_range.isdigit():
        raise ValueError("max range must be an integer")

    if not start.isdigit():
        raise ValueError("start must be an integer")


def make_usn(y, b, n):
    return f'1MS{y}{b}{n:03d}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--year', required=True, help='last 2 digits of year')
    parser.add_argument('-b', '--branch', required=True, help='branch code')
    parser.add_argument('-m', '--max', dest='max_range', required=True, help='number of results to fetch')
    parser.add_argument('-s', '--start', default='1', help='starting USN')

    args = parser.parse_args()

    try:
        validate_parameters(args.year, args.branch, args.max_range, args.start)
    except ValueError as e:
        print(e)
        return

    branch = args.branch.upper()
    html_text = """
    <html>
    <head>
        <title>Results</title>
        <style>
            td, th {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }
            table {
                border-collapse: collapse;
            }
        </style>
    </head>
    <body>
        <table>
            <tr>
                <th>USN</th>
                <th>Name</th>
                <th>Sem</th>
                <th>Creds registered</th>
                <th>Creds earned</th>
                <th>SGPA</th>
                <th>CGPA</th>
                <th>Subject-wise results</th>
            </tr>
    """

    with open('results.html', 'w', encoding='utf-8') as f:
        f.write(html_text)

        start_val = int(args.start)
        max_val = int(args.max_range)

        for i in range(start_val, start_val + max_val):
            usn = make_usn(args.year, branch, i)
            print(f"Fetching {usn}...")
            r = fetch_results(usn)

            if r:
                f.write(r)
                print(f"Saved {usn}")
                error_file = f"error_log_{usn}.html"
                if os.path.exists(error_file):
                    os.remove(error_file)

        f.write("""
        </table>
    </body>
    </html>
    """)

    print("Done.")


if __name__ == '__main__':
    main()
