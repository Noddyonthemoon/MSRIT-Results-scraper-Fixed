# MSRIT Results Scraper (Fixed)

## Sample result of a student
![Sample Result of a student](images/sample_result.png)

> ## What's New in this Fork?
>
> - Updated scraping flow to match new session/token handling
> - Implemented newer exam id (`examId`) parameter queries
> - Fixed SSL verification issues via custom context
> - Added `-s/--start` to begin from a specific USN
> - No longer the need to know the branch size, mentioning just -b will fetch the details of all the students. `-y 25 -b IS`
> - 
>
> ## Important Note on `examId` Maintenance
>
> The college's backend now requires an `examId` parameter to fetch results. Currently, the `examId` inside the script is set to `59`. For future semesters, this ID may change. You will need to inspect the network traffic on the official results website to find the new ID and update the `examId=59` variable inside `main.py`.

## Usage

### Clone the repository to the local machine
```bash
$ git clone https://github.com/Noddyonthemoon/MSRIT-Results-scraper-Fixed.git
````

### Change directory

```bash
$ cd MSRIT-Results-scraper-Fixed
```

### Using the tool

```bash
$ python3 main.py -y <year(yy)> -b <branch extension(XX)> -m <max range of USN> -s <starting usn>
```

## Arguments

```bash
-y <year(yy)> 
-b <branch extension(XX)> 
-m <max range of USN > [optional]
-s <starting usn > [optional]
```

---

## Options

```bash
-h, --help            show this help message and exit  
-y YEAR, --year=YEAR  specify the last two digits of the year of admission  
-b BRANCH, --branch=BRANCH  
                      specify the branch extension.
                      ( only -b argument required, for the results of the whole batch of students in the said branch)
-m MAX, --max=MAX     specify the max limit of USNs  
-s START, --start=START  
                      specify the starting USN (default set to 001)
```

---

## Allowed branches for option `-b` or `--branch`

```bash
CS, EC, IS, ME, ML, CH, CV, EE, TI, EI, IM, AT, BT, CY, CI
```

## Example usage

Let us take the example where we want to retrieve the results of students from USN 3 to 12 (3 + 10) in Computer Science (CS) branch who joined the college in the year 2018:

```bash
$ python main.py -y 18 -b CS -m 10 -s 003
# **(OR)**
$ python main.py --year 18 --branch CS --max 10 --start 003
```

---

## Where can I view the results that were fetched?

* The results fetched from the website are stored in a **`results.html`** file in the same directory.
* Open the file **`results.html`** to view the results as a table in your browser.

---

## Points to note

* Make sure that the website is not down for maintenance before using the tool.
* Do not use the tool for disrupting the normal functioning of the website.
* The tool does not store the results anywhere online (results are only fetched on the spot).
* Ensure you have an active internet connection while using the tool.
* Some USNs in the range may not be available due to various reasons.
