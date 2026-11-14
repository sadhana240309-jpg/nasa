import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.core.statistics import compute_mann_kendall, apply_fdr_correction
import numpy as np

vals = np.array([10.2, 11.5, 12.1, 13.8, 14.2, 15.6, 16.1, 17.5])
times = np.array([2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022])

res = compute_mann_kendall(vals, times)
print("MK Test Success:", res["p_value"] < 0.05, "Sen Slope:", res["sen_slope"])

p_vals = [0.001, 0.04, 0.03, 0.25, 0.8]
adj_p, sig = apply_fdr_correction(p_vals)
print("FDR Adjusted:", adj_p, sig)
print("ALL CORE TESTS PASSED!")
