import lxml.html
import lxml
from urllib.request import urlopen
from os.path import join as pjoin
import logging
from multiprocessing import Pool
import pandas as pd
import re

YEARS = (1900, 2023)
N_PROC = 4
SAVE_DIR = "CHANGE_TO_OUT_DIR"
FORMATTER = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
COLS = [
    "Autor",
    "Autor/Asesor",
    "Datos Publicación",
    "Desc. Física",
    "Entidad particip.",
    "Fuente de catalog.",
    "No. de sistema",
    "Nota de tesis",
    "Recurso electr.",
    "Restricciones",
    "Tipo de contenido",
    "Tipo de portador",
    "Tipo de soporte",
    "Título",
]


def setup_logger(name, log_file, level=logging.WARNING, formatter=FORMATTER):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def get_initial_url(year=2022):
    """
    We have to scrape annually because of the 20k result limit.
    """
    year = int(year)
    url = f"http://tesiunam.dgb.unam.mx/F/?func=find-b&local_base=TES01&request=&find_code=WRD&adjacent=N&filter_code_2=WYR&filter_request_2={year}&filter_code_3=WYR&filter_request_3={year}"
    return url


def get_full_url(url):
    """
    From original search url we get one that we can use to 'jump' to the subsequent
    pages and iteratively scrape all the results.

    """
    html = lxml.html.parse(urlopen(url)).getroot()
    n_tesis = int(html.xpath(".//strong")[2].text_content().split()[-1][:-1])
    if n_tesis > 10:
        url = html.xpath(".//a")[30].get("href")
    return url, n_tesis


def get_theses_links(url):
    """
    Get all links to specific data pages from search page.

    """
    html = lxml.html.parse(urlopen(url)).getroot()
    url_list = html.xpath(".//a")  # [34:54][::2]
    url_list = [x.get("href").replace("999", "002") for x in url_list]
    url_list = [x for x in url_list if "format=002" in x]
    return url_list


def jump_url(url, jump_len=10):
    """
    Go to the next page containing ten thesis.
    """
    return url[:-6] + f"{int(url[-6:]) + jump_len:06d}"


def parse_thesis_page(url):
    """
    Returns all relevant data from specific thesis page.

    """
    table = pd.read_html(url)[0].transpose()
    table = table.rename(columns=table.iloc[0]).drop(table.index[0])
    try:
        table[["Autor/Asesor"]] = table[["Autor/Asesor"]] + "||"
    except Exception:
        pass
        # print(f"Error {url}")
    return table.groupby(level=0, axis=1).sum()


def get_year_df(year, save_dir, cols=COLS):
    """
    Scrapes an entire year and outputs a DataFrame in .csv format for later use.
    Also creates a log file for possible errors.
    """
    logger = setup_logger(f"{year}", pjoin(save_dir, f"log_{year}.txt"))
    url = get_initial_url(year)
    url, n_theses = get_full_url(url)
    n_pages = -(n_theses // -10)
    df = pd.DataFrame(columns=cols)

    for i in range(n_pages):
        try:
            thesis_list = get_theses_links(url)
            for j in range(len(thesis_list)):
                tmp_df = parse_thesis_page(thesis_list[j])
                df = pd.concat([df, tmp_df], axis=0)[cols]
        except Exception:
            logger.exception(f"Got exception on {url}")
        url = jump_url(url)
    df.to_csv(pjoin(save_dir, f"{year}.csv"), index=False)

    return None


def get_pdf_link(link):
    """
    Get direct pdf link; skip intermediate html page that UNAM provides.

    """
    # get link and remove index.html to replace with direct pdf link
    link = re.match("http(.*)html", link).group()[:-11]
    code = link.split("/")[-1]
    link = link + "/" + code + ".pdf"


def pool_wrapper(year):
    get_year_df(year, SAVE_DIR)
    return None


if __name__ == "__main__":
    year_stack = list(range(*YEARS))

    with Pool(N_PROC) as p:
        p.map(pool_wrapper, year_stack)

