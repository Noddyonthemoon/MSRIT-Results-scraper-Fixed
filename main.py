# Command line tool using Python to fetch the results of students from "https://exam.msrit.edu/"
# Refer the readme file for instructions on how to use the tool
# Made by Manish.M

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request
import ssl
import threading
import os
import html
from bs4 import BeautifulSoup

BRANCHES = ["CS", "EC", "IS", "ME", "ML", "CH", "CV", "EE", "TI", "EI", "IM", "AT", "BT", "CY", "CI"]

SSL = ssl.create_default_context()
SSL.check_hostname = False
SSL.verify_mode = ssl.CERT_NONE


def make_usn(year, branch, num):
    return f"1MS{year}{branch}{num:03d}"


def fetch_one(usn):
    url = f"https://exam.msrit.edu/index.php/component/examresult/?usn={usn}&examId=59&task=getResult&bypass=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"})

    try:
        with urllib.request.urlopen(req, context=SSL, timeout=15) as resp:
            page = resp.read().decode("utf-8")
    except Exception:
        return None
    soup = BeautifulSoup(page, "html.parser")

    try:
        name_div = soup.find("div", class_="uk-card uk-card-body stu-data stu-data1")
        name = name_div.find("h3").get_text(strip=True)

        sem_div = soup.find("div", class_="uk-card uk-card-body stu-data stu-data2")
        sem_text = sem_div.find("p").get_text(strip=True)
        sem = "".join(c for c in sem_text if c.isdigit()) or sem_text[-1:]

        data = {"usn": usn, "name": name, "sem": sem, "subjects": []}
        for cls_suffix, key in [
            ("credits-sec1", "credits_registered"),
            ("credits-sec2", "credits_earned"),
            ("credits-sec3", "sgpa"),
            ("credits-sec4", "cgpa"),
        ]:
            div = soup.find("div", class_=f"uk-card uk-card-default uk-card-body {cls_suffix}")
            data[key] = div.find("p").get_text(strip=True) if div else ""

        if table := soup.find("table", class_="uk-table uk-table-striped res-table"):
            for row in table.find_all("tr")[1:]:
                if cells := [td.get_text(strip=True) for td in row.find_all("td")]:
                    data["subjects"].append(cells)
        return data
    except Exception:
        return None


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("MSRIT Exam Results")
        self.geometry("1100x720")
        self.minsize(900, 500)

        self._stop_event = threading.Event()
        self._thread = None
        self._results = []

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Year (YY)").grid(row=0, column=0, sticky="w")
        self.year_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.year_var, width=6).grid(
            row=0, column=1, padx=(4, 16))

        ttk.Label(top, text="Branch").grid(row=0, column=2, sticky="w")
        self.branch_var = tk.StringVar()
        branch_cb = ttk.Combobox(top, textvariable=self.branch_var, values=BRANCHES, state="readonly", width=6)
        branch_cb.grid(row=0, column=3, padx=(4, 16))

        ttk.Label(top, text="Start").grid(row=0, column=4, sticky="w")
        self.start_var = tk.StringVar(value="1")
        ttk.Entry(top, textvariable=self.start_var, width=6).grid(
            row=0, column=5, padx=(4, 16))

        ttk.Label(top, text="Count (blank = auto)").grid(
            row=0, column=6, sticky="w")
        self.count_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.count_var, width=6).grid(
            row=0, column=7, padx=(4, 16))

        btn_frame = ttk.Frame(self, padding=(10, 0, 10, 6))
        btn_frame.pack(fill="x")

        self.fetch_btn = ttk.Button(
            btn_frame, text="Fetch", command=self._on_fetch)
        self.fetch_btn.pack(side="left")

        self.stop_btn = ttk.Button(
            btn_frame, text="Stop", command=self._on_stop, state="disabled")
        self.stop_btn.pack(side="left", padx=6)

        self.export_btn = ttk.Button(
            btn_frame, text="Export HTML", command=self._on_export, state="disabled")
        self.export_btn.pack(side="left", padx=6)

        self.clear_btn = ttk.Button(
            btn_frame, text="Clear", command=self._on_clear)
        self.clear_btn.pack(side="left", padx=6)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(btn_frame, textvariable=self.status_var,
                  foreground="gray").pack(side="right")

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=10)

        tree_frame = ttk.Frame(self, padding=10)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame,
            columns=("usn", "name", "sem", "cr_reg", "cr_earn", "sgpa",
            "cgpa", "subjects"), show="headings", selectmode="browse")

        headings = {
            "usn": ("USN", 110),
            "name": ("Name", 200),
            "sem": ("Sem", 40),
            "cr_reg": ("Cr Reg", 55),
            "cr_earn": ("Cr Earn", 55),
            "sgpa": ("SGPA", 55),
            "cgpa": ("CGPA", 55),
            "subjects": ("Subjects", 480),
        }
        for col, (label, width) in headings.items():
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, minwidth=40)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

    def _validate_inputs(self):
        year = self.year_var.get().strip()
        branch = self.branch_var.get().strip().upper()
        start_str = self.start_var.get().strip()
        count_str = self.count_var.get().strip()

        if not year.isdigit() or len(year) != 2:
            messagebox.showerror(
                "Invalid input", "Year must be exactly 2 digits.")
            return None
        if branch not in BRANCHES:
            messagebox.showerror("Invalid input", "Pick a valid branch.")
            return None
        if not start_str.isdigit() or int(start_str) < 1:
            messagebox.showerror(
                "Invalid input", "Start must be a positive integer.")
            return None

        count = None
        if count_str:
            if not count_str.isdigit() or int(count_str) < 1:
                messagebox.showerror(
                    "Invalid input", "Count must be a positive integer or blank.")
                return None
            count = int(count_str)

        return year, branch, int(start_str), count

    def _on_fetch(self):
        params = self._validate_inputs()
        if params is None:
            return

        self._stop_event.clear()
        self._results.clear()
        self.tree.delete(*self.tree.get_children())

        self.fetch_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.export_btn.config(state="disabled")
        self.progress.start(12)

        self._thread = threading.Thread(
            target=self._fetch_loop, args=params, daemon=True)
        self._thread.start()

    def _fetch_loop(self, year, branch, start, count):
        i = start
        misses = 0

        while not self._stop_event.is_set():
            if count is not None and i >= start + count:
                break
            if count is None and misses >= 5:
                self._post_status("Done.")
                break

            usn = make_usn(year, branch, i)
            self._post_status(f"Fetching {usn}...")

            if data := fetch_one(usn):
                misses = 0
                self._results.append(data)
                self._insert_row(data)
            else:
                misses += 1

            i += 1

        self.after(0, self._fetch_done)

    def _insert_row(self, d):
        subj_str = " | ".join(f"{s[0]}: {s[-1]}" if len(s) >= 2 else ", ".join(s)
            for s in d["subjects"])
        values = (d["usn"], d["name"], d["sem"], d["credits_registered"], d["credits_earned"], d["sgpa"], d["cgpa"], subj_str)

        self.after(0, lambda v=values: self.tree.insert("", "end", values=v))

    def _post_status(self, msg):
        self.after(0, lambda: self.status_var.set(msg))

    def _fetch_done(self):
        self.progress.stop()
        self.fetch_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        if self._results:
            self.export_btn.config(state="normal")
        n = len(self._results)
        self.status_var.set(f"{n} result{'s' if n != 1 else ''} fetched.")

    def _on_stop(self):
        self._stop_event.set()
        self.status_var.set("Stopping...")

    def _on_clear(self):
        self._on_stop()
        self.tree.delete(*self.tree.get_children())
        self._results.clear()
        self.export_btn.config(state="disabled")
        self.status_var.set("Ready")

    def _on_export(self):
        if not self._results:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html")],
            initialfile="results.html",
        )
        if not path:
            return

        rows_html = []
        for d in self._results:
            subj_rows = "".join(
                "<tr>" +
                "".join(f"<td>{html.escape(c)}</td>" for c in s) + "</tr>"
                for s in d["subjects"]
            )
            subj_table = (
                "<table><tr><th>Code</th><th>Subject</th>"
                "<th>Cr Reg</th><th>Cr Earn</th><th>Grade</th></tr>"
                f"{subj_rows}</table>"
            )
            rows_html.append(
                "<tr>"
                f"<td>{html.escape(d['usn'])}</td>"
                f"<td>{html.escape(d['name'])}</td>"
                f"<td>{html.escape(d['sem'])}</td>"
                f"<td>{html.escape(d['credits_registered'])}</td>"
                f"<td>{html.escape(d['credits_earned'])}</td>"
                f"<td>{html.escape(d['sgpa'])}</td>"
                f"<td>{html.escape(d['cgpa'])}</td>"
                f"<td>{subj_table}</td>"
                "</tr>"
            )

        with open(path, "w", encoding="utf-8") as f:
            f.write(
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "<title>MSRIT Results</title><style>"
                "body{font-family:system-ui,sans-serif;margin:20px}"
                "table{border-collapse:collapse;width:100%}"
                "td,th{border:1px solid #ccc;padding:6px 10px;text-align:left}"
                "th{background:#f4f4f4}"
                "</style></head><body>"
                "<h2>MSRIT Exam Results</h2>"
                "<table><tr><th>USN</th><th>Name</th><th>Sem</th>"
                "<th>Cr Reg</th><th>Cr Earn</th><th>SGPA</th><th>CGPA</th>"
                "<th>Subjects</th></tr>"
                + "\n".join(rows_html)
                + "</table></body></html>"
            )
        self.status_var.set(
            f"Exported {len(self._results)} results to {os.path.basename(path)}")


if __name__ == "__main__":
    App().mainloop()
