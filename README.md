# Capstone A — FreshMart Retail Chain: Sales Intelligence Pipeline

**Naresh IT · Python for Full Stack Data Science with AI & Generative AI · Lead Trainer: Ajit Byru**

You are building the tool FreshMart's owner will run every month. The package is the product; the notebook is the findings.

## Files
| Path | What it is |
|---|---|
| `data/sales_2025.csv` | ~40,000 receipt lines — deliberately messy |
| `data/products.csv` · `stores.csv` · `promotions.csv` | Reference tables |
| `freshmart/loader.py` | `SalesLoader` — **stubs to complete** (validation, exceptions, generator) |
| `freshmart/cleaner.py` | `QualityLog` (done) · `clean_products`, `clean_sales` — **rules to write** |
| `freshmart/report.py` | `timed` decorator and five analysis functions — **to implement** |
| `freshmart/__main__.py` | CLI — **wire it up** |
| `freshmart_analysis_student.ipynb` | Your findings notebook; it imports the package |

## Definition of done
- [ ] `SalesLoader` raises `DataFileError` / `SchemaError` correctly; `stream_sales()` yields chunks
- [ ] Every cleaning rule calls `log.add(problem, rows, fix, why)`; the log has ≥ 8 rows
- [ ] Final clean shape and total revenue match the acceptance numbers given in class
- [ ] Q1–Q5 answered with a chart and a one-sentence reading each; Q6 is your own
- [ ] `python -m freshmart report --store 4` runs and prints three tables
- [ ] Recommendation paragraph (120–180 words) to the owner
- [ ] Notebook runs top-to-bottom in a fresh kernel; five slides; two-minute pitch

## Rules
No `sklearn`, no models. AI assistants for syntax and error messages only — the viva tests design decisions.

## Grading (20)
Data-quality log 4 · Guided questions 6 · Own question 3 · Engineering (package + CLI + README) 3 · Reproducibility 2 · Viva & pitch 2

## Interview questions you will be asked
1. Why a class for the loader and plain functions for the cleaner?
2. How did you decide a promotion "worked"? What was the null hypothesis?
3. Why a generator for the sales file — what did it buy you and what did it cost?
4. Which cleaning decision would you reverse with more information?
5. The owner's single most valuable finding, in one sentence?

## Run
```bash
pip install numpy pandas matplotlib seaborn
python -m freshmart report --store 4          # from this folder
jupyter notebook freshmart_analysis_student.ipynb
```
