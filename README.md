# MSRIT-Results-scraper ( fixed ) (Only the result_cmd_tool.py fixed)
<br>
<b>Sample result of a student</b>
<br>

![Sample Result of a student](https://github.com/Manish-M2018/MSRIT-Results-scraper/blob/master/images/sample_result.png)

Note: The usn, name, cgpa, sgpa and grade fields are blurred in the pic for privacy reasons

## 🛠️ What's New in this Fork?
The original tool broke due to backend infrastructure and security updates on the college website. This fork revives the project with the following critical compatibility fixes:
* **Authentication Flow Update:** Adapted the scraping mechanism to smoothly interface with the latest server-side session and token requirements.
* **Dynamic Query Payload:** Accommodates the new backend API requirement to specify exact exam cycle parameters when querying databases.
* **Connection Stability:** Bypasses `[SSL: CERTIFICATE_VERIFY_FAILED]` errors (common on macOS/Linux Python environments) by utilizing a custom SSL context. 
* **Header Configurations:** Integrates standard browser routing headers to ensure stable connectivity and prevent automated request blocking.
* **Parser Improvements:** Fixed dictionary generation bugs in the HTML parser to prevent crashes during data extraction.
* **Starting USN parameter:** Added a simple -s, --start parameter to start retreiving result from a certain usn instead of starting from 001 every single time

## ⚠️ Important Note on examId Maintenance
The college's backend now requires an examId parameter to fetch results. Currently, the examId inside the script is set to 59.

For future semesters, this ID will change. You will need to inspect the network traffic on the official results website to find the new ID and update the examId=59 variable inside results_cmd_tool.py to keep the tool functional.



# Usage

<b>Clone the repository to the local machine</b> <br>
<pre>
git clone https://github.com/Manish-M2018/MSRIT-Results-scraper.git
</pre>

<b> Change directory </b> <br>
<pre>
cd MSRIT-Results-scraper
</pre>

<b> Using the tool </b> <br>
<pre>
python3 results_cmd_tool.py -y &lt;year(yy)&gt; -b &lt;branch extension(XX)&gt; -m &lt;max range of USN -s &lt; starting usn&gt; 
</pre>

<b> Arguments </b> <br>
<pre> 
-y &lt;year(yy)&gt; -b &lt;branch extension(XX)&gt; -m &lt;max range of USN &lt; starting usn &gt; 
</pre>  
 
<b> Options </b> <br>
<pre>
  -h, --help            show this help message and exit  <br>
  -y YEAR, --year=YEAR  specify the last two digits of the year <br>
  -b BRANCH, --branch=BRANCH
                        specify the branch extension  <br>
  -m MAX, --max=MAX     specify the max limit of USNs <br>
  -s START, --start= START  specify the starting USN (simple alternative for single student result) <br>
</pre>

<b> Allowed branches for option -b or --branch</b> <br>
<pre>
CS, EC, IS, ME, ML, CH, CV, EE, TI, EI, IM, AT, BT
</pre>

<b> Example usage </b> <br>
Let us take the example where we want to retrieve the results of the students from USN 3 to 12 (3 + 10) in Computer Science (CS) branch who joined the college in the year 2018<br>
<pre>
python results_cmd_tool.py -y 18 -b CS -m 10 -s 003
</pre>
<b>(OR)</b> <br>
<pre>
python results_cmd_tool.py --year 18 --branch CS --max 10 --start 003
</pre>

# Where can I view the results that were fetched?
- The results that were fetched from the website is stored in a file called <b>results.html</b> in the same directory
- Open the file <b>results.html</b> in order to view the results in a tabular format on the browser

# Points to note
- Make sure that the website is not down for maintenance before using the tool
- Do not use the tool for disrupting the normal functioning of the website
- The tool does not store the results anywhere online (results are fetched on the spot)
- Make sure you have an active internet connection while using the tool 
- Some USNs in the range may not be available due to various reasons

<br><br>

