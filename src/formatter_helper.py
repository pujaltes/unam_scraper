#!/usr/bin/env python3
"""
Quick script to format combined UNAM thesis output
"""
import pandas as pd
from os.path import join as pjoin
from pathlib import Path

path = Path(__file__).parent.absolute()

table = pd.read_csv(pjoin(path, "combined.out"), low_memory=False)
table[['Título']].to_csv(pjoin(path, "titles.csv"), index=False)
table[['Autor/Asesor']].to_csv(pjoin(path, "autor_asesor.csv"), index=False)
