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
        self._branch_only_fetch = False   # ← addition: tracks fetch mode
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

        # ── ADDITION: Create Rank List button ──────────────────────────────
        self.ranklist_btn = ttk.Button(
            btn_frame, text="⭐ Create Rank List",
            command=self._on_create_ranklist, state="disabled")
        self.ranklist_btn.pack(side="left", padx=6)
        # ───────────────────────────────────────────────────────────────────

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
        # ── ADDITION: detect branch-only fetch (start=1, count=blank) ─────
        year, branch, start, count = params
        self._branch_only_fetch = (start == 1 and count is None)
        # ──────────────────────────────────────────────────────────────────
        self._stop_event.clear()
        self._results.clear()
        self.tree.delete(*self.tree.get_children())
        self.fetch_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.export_btn.config(state="disabled")
        # ── ADDITION: reset rank list button while fetching ────────────────
        self.ranklist_btn.config(state="disabled")
        # ──────────────────────────────────────────────────────────────────
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
        # ── ADDITION: highlight rank list button only for branch-only fetches
        if self._results and self._branch_only_fetch:
            self.ranklist_btn.config(state="normal")
        # ──────────────────────────────────────────────────────────────────
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
        # ── ADDITION: also reset rank list button on clear ─────────────────
        self.ranklist_btn.config(state="disabled")
        self._branch_only_fetch = False
        # ──────────────────────────────────────────────────────────────────
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

    # ════════════════════════════════════════════════════════════════════════
    # ADDITION: Rank List generation — all new code below, nothing above touched
    # ════════════════════════════════════════════════════════════════════════

    def _cgpa_sort_key(self, d):
        """Return float CGPA for sorting; fallback to 0.0 on parse error."""
        try:
            return float(d["cgpa"])
        except (ValueError, KeyError):
            return 0.0

    def _cgpa_badge_class(self, cgpa_val):
        """Map a CGPA float to the CSS badge class matching the reference HTML."""
        if cgpa_val == 10.0:
            return "b10"
        elif cgpa_val >= 9.5:
            return "b95"
        elif cgpa_val >= 9.0:
            return "b9"
        elif cgpa_val >= 8.0:
            return "b8"
        elif cgpa_val >= 7.0:
            return "b7"
        else:
            return "blow"

    def _row_class(self, rank):
        """Gold/silver/bronze classes for top 3 ranks, matching the reference HTML."""
        if rank == 1:
            return ' class="gold"'
        elif rank == 2:
            return ' class="silver"'
        elif rank == 3:
            return ' class="bronze"'
        return ""

    def _credits_fully_earned(self, d):
        """Return True if credits_registered == credits_earned (no backlogs)."""
        try:
            return int(d["credits_registered"]) == int(d["credits_earned"])
        except (ValueError, KeyError):
            return True

    def _build_ranklist_html(self):
        """
        Build and return the complete rank-list HTML string, exactly matching
        the format of the reference MSRIT_IS_Sem1_RankList.html.
        Students are sorted by CGPA descending; equal CGPA shares the same rank.
        """
        branch   = self.branch_var.get().strip().upper()
        year     = self.year_var.get().strip()
        # Determine semester from first result (all should be same semester)
        sem = self._results[0]["sem"] if self._results else "?"

        # Sort by CGPA descending
        sorted_results = sorted(self._results, key=self._cgpa_sort_key, reverse=True)
        total = len(sorted_results)

        # Assign ranks (equal CGPA = same rank, next rank skips appropriately)
        ranks = []
        current_rank = 1
        for idx, d in enumerate(sorted_results):
            if idx == 0:
                ranks.append(current_rank)
            else:
                if self._cgpa_sort_key(d) == self._cgpa_sort_key(sorted_results[idx - 1]):
                    ranks.append(ranks[-1])          # same rank as previous
                else:
                    ranks.append(idx + 1)            # true positional rank
                    current_rank = idx + 1

        # Build table rows
        rows_html_parts = []
        for rank, d in zip(ranks, sorted_results):
            cgpa_val  = self._cgpa_sort_key(d)
            badge_cls = self._cgpa_badge_class(cgpa_val)
            row_cls   = self._row_class(rank)

            # ⚠ warning marker if credits not fully earned
            warning   = " ⚠" if not self._credits_fully_earned(d) else ""

            rows_html_parts.append(
                f'<tr{row_cls}>'
                f'<td class="rank">{rank}</td>'
                f'<td class="usn">{html.escape(d["usn"])}</td>'
                f'<td>{html.escape(d["name"])}{html.escape(warning)}</td>'
                f'<td>{html.escape(d["credits_registered"])}</td>'
                f'<td>{html.escape(d["credits_earned"])}</td>'
                f'<td>{html.escape(d["sgpa"])}</td>'
                f'<td><span class="badge {badge_cls}">{html.escape(d["cgpa"])}</span></td>'
                f'</tr>'
            )

        rows_html = "\n".join(rows_html_parts)

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>MSRIT {html.escape(branch)} — Semester {html.escape(sem)} Rank List 20{html.escape(year)}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f4f8; padding: 24px; color: #222; }}
  .header {{ background: linear-gradient(135deg, #1a237e, #283593); color: #fff; padding: 20px 28px; border-radius: 10px 10px 0 0; }}
  .header h2 {{ font-size: 20px; font-weight: 700; }}
  .header p {{ font-size: 13px; opacity: 0.85; margin-top: 4px; }}
  .wrapper {{ background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; max-width: 980px; margin: 0 auto; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th {{ background: #1a237e; color: #fff; padding: 10px 14px; text-align: left; font-size: 13px; position: sticky; top: 0; }}
  td {{ border-bottom: 1px solid #eee; padding: 8px 14px; font-size: 13px; vertical-align: middle; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #e8eaf6 !important; transition: 0.1s; }}
  .rank {{ font-weight: 800; font-size: 15px; color: #1a237e; width: 48px; }}
  .usn {{ font-family: monospace; font-size: 12px; color: #555; }}
  .gold td {{ background: #fff8e1; }}
  .silver td {{ background: #f5f5f5; }}
  .bronze td {{ background: #fbe9e7; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 700; letter-spacing: 0.3px; }}
  .b10 {{ background: #1b5e20; color: #fff; }}
  .b95 {{ background: #2e7d32; color: #fff; }}
  .b9  {{ background: #1565c0; color: #fff; }}
  .b8  {{ background: #6a1b9a; color: #fff; }}
  .b7  {{ background: #e65100; color: #fff; }}
  .blow {{ background: #b71c1c; color: #fff; }}
  .legend {{ padding: 10px 16px; font-size: 12px; color: #555; background: #f9f9fb; border-top: 1px solid #eee; }}
  .legend span {{ margin-right: 14px; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h2>🏫 MSRIT — {html.escape(branch)} Branch</h2>
    <p>Semester {html.escape(sem)} · Batch 20{html.escape(year)} · Complete Rank List ({total} Students) · Sorted by CGPA · Equal CGPA = Same Rank</p>
  </div>
  <table>
    <thead>
      <tr>
        <th>Rank</th>
        <th>USN</th>
        <th>Name</th>
        <th>Cr Reg</th>
        <th>Cr Earn</th>
        <th>SGPA</th>
        <th>CGPA</th>
      </tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
  <div class="legend">
    <strong>CGPA bands:</strong>
    <span><span class="badge b10">10.00</span> Perfect</span>
    <span><span class="badge b95">≥9.50</span> Excellent</span>
    <span><span class="badge b9">≥9.00</span> Outstanding</span>
    <span><span class="badge b8">≥8.00</span> Very Good</span>
    <span><span class="badge b7">≥7.00</span> Good</span>
    <span><span class="badge blow">&lt;7.00</span> Below 7</span>
    &nbsp;·&nbsp; ⚠ = Credits not fully earned (backlogs/failures)
  </div>
</div>
</body>
</html>"""

    def _on_create_ranklist(self):
        """Callback for the Create Rank List button."""
        if not self._results:
            return
        branch = self.branch_var.get().strip().upper()
        year   = self.year_var.get().strip()
        sem    = self._results[0]["sem"] if self._results else "X"
        default_name = f"MSRIT_{branch}_Sem{sem}_RankList.html"
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html")],
            initialfile=default_name,
            title="Save Rank List As",
        )
        if not path:
            return
        ranklist_html = self._build_ranklist_html()
        with open(path, "w", encoding="utf-8") as f:
            f.write(ranklist_html)
        self.status_var.set(
            f"Rank list ({len(self._results)} students) saved to {os.path.basename(path)}")

    # ════════════════════════════════════════════════════════════════════════
    # END OF ADDITION
    # ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    App().mainloop()        name_div = soup.find("div", class_="uk-card uk-card-body stu-data stu-data1")
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
