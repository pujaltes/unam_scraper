"""
WIP script to download all pdf text data. Current pipeline is very slow and would take
several days to complete. Furthermore, doesn't work very well for old scanned thesis;
although that might just be unsolvable. It might be a good idea to just stick to modern
digital thesis for now.

Current plan is to convert every pdf into a vector using TfidVectorizer and find KNN
using cosine similarity.
"""

from os.path import join as pjoin
import logging
from multiprocessing import Pool
import pandas as pd
import re
from urllib.request import Request, urlopen
import io
import pikepdf
from pdfminer.high_level import extract_text
import os
from pathlib import Path


N_PROC = 4
SAVE_DIR = "CHANGE_TO_DIR"
YEARS = (1975, 2023)
FORMATTER = logging.Formatter("%(asctime)s %(levelname)s %(message)s")


def setup_logger(name, log_file, level=logging.WARNING, formatter=FORMATTER):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def get_pdf_link(link):
    # get link and remove index.html to replace with direct pdf link
    link = re.match("http(.*)html", link).group()[:-11]
    code = link.split("/")[-1]
    link = link + "/" + code + ".pdf"
    return link


def scrape_pdf(url, tmp_name="tmp.pdf", page_nums=list(range(2, 200, 1))):
    """
    Extract all text info form the pdf's.
    TODO: Figure out how to avoid downloading a tmp file
    TODO: Deal with werid text in old thesis
    """
    stream = io.BytesIO(urlopen(Request(url)).read())
    pdf = pikepdf.open(stream)
    pdf.save(tmp_name)
    text = extract_text(tmp_name, page_numbers=page_nums)
    return text


def scrape_year(year, df, save_path):
    logger = setup_logger(f"{year}", pjoin(save_path, f"log_{year}.txt"))
    tmp_df = df[df["Datos Publicacion"] == year]
    for index, row in tmp_df.iterrows():
        try:
            url = get_pdf_link(row["Recurso electr."])
            tmp_path = pjoin(save_path, f"tmp_{year}.pdf")
            text = scrape_pdf(url, tmp_name=tmp_path)
            os.remove(tmp_path)
        except Exception:
            logger.exception(f"Got exception on yr:{year} and indx:{index}")
            text = ""
        with open(pjoin(save_path, f"{year}.txt"), "a+") as f:
            f.write(f"{index}\n")
            f.write(text.replace('\n', '') + "\n")
    return None


if __name__ == "__main__":

    path = Path(__file__).parent.absolute()
    table_path = pjoin(os.path.dirname(path), "data", "combined_sin_ac.out")

    table = pd.read_csv(table_path, low_memory=False)
    # filter out thess that dont have a pdf
    missing_bool = pd.isnull(table[["Recurso electr.", "Datos Publicacion"]]).any(
        axis=1
    )
    table = table[~missing_bool]
    link_bool = table["Recurso electr."].str.contains("Portada") | table[
        "Datos Publicacion"
    ].str.contains("\?")
    table = table[~link_bool]
    table["Datos Publicacion"] = (
        table["Datos Publicacion"].str.extract("(\d+)", expand=False).astype(int)
    )
    table.to_csv(pjoin(SAVE_DIR, "pdf_links.csv"))
    table = table[["Recurso electr.", "Datos Publicacion"]]

    def pool_wrapper(year):
        scrape_year(year, table, SAVE_DIR)
        return None

    year_stack = list(range(*YEARS))

    with Pool(N_PROC) as p:
        p.map(pool_wrapper, year_stack)
