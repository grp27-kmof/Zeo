#!/usr/bin/env python3
 
import os
import shutil
import subprocess
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
 
import pandas as pd
 
BASE_DIR = Path(__file__).resolve().parent
 
ZEO_DIR = BASE_DIR / "zeo++-0.3"
MOF_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
 
NETWORK = ZEO_DIR / "network"
 
ALL_RESULTS_CSV = BASE_DIR / "all_mof_properties.csv"
FILTERED_RESULTS_CSV = BASE_DIR / "filtered_mofs.csv"
 
 
PLD_MIN = 2.66
PLD_MAX = 10.0
 
LCD_MIN = 2.66
LCD_MAX = 20.0
 
# Number of CIFs to process concurrently
N_WORKERS = 25

SINGLE_THREAD_ENV = {
    **os.environ,
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}
 
 
def compile_zeopp():
    """Compile ZEO++ if needed."""
 
    if NETWORK.exists():
        print("ZEO++ already compiled.\n")
        return
 
    print("Compiling Voro++...")
 
    subprocess.run(
        ["make"],
        cwd=ZEO_DIR / "voro++" / "src",
        check=True,
    )
 
    print("Compiling ZEO++...")
 
    subprocess.run(
        ["make"],
        cwd=ZEO_DIR,
        check=True,
    )
 
    print("Compilation completed.\n")
 
 
def process_one(cif_path_str):
 
    cif_path = Path(cif_path_str)
    res_path = cif_path.with_suffix(".res")
 
    start = time.time()
 
    try:
        subprocess.run(
            [
                str(NETWORK),
                "-ha",
                "-res",
                str(res_path),
                str(cif_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            env=SINGLE_THREAD_ENV,
        )
 
        with open(res_path) as f:
            line = f.readline().strip()
 
        parts = line.split()
 
        if len(parts) < 4:
            return {"MOF": cif_path.name, "error": "Invalid .res file."}
 
        lcd = float(parts[1])
        pld = float(parts[2])
        lfpd = float(parts[3])
 
        passed = (
            LCD_MIN <= lcd <= LCD_MAX
            and
            PLD_MIN <= pld <= PLD_MAX
        )
 
        if passed:
            shutil.copy2(
                cif_path,
                OUTPUT_DIR / cif_path.name,
            )
 
        return {
            "MOF": cif_path.name,
            "LCD_Angstrom": lcd,
            "PLD_Angstrom": pld,
            "LFPD_Angstrom": lfpd,
            "Filtered": passed,
            "seconds": round(time.time() - start, 2),
        }
 
    except Exception as e:
        return {"MOF": cif_path.name, "error": str(e)}
 
    finally:
        if res_path.exists():
            res_path.unlink()
 
 
def analyze_mofs():
 
    OUTPUT_DIR.mkdir(exist_ok=True)
 
    cif_files = sorted(MOF_DIR.glob("*.cif"))
    total = len(cif_files)
 
    print(f"Found {total} CIF files.")
    print(f"Launching pool of {N_WORKERS} worker processes...\n")
 
    results = []
    done = 0
    batch_start = time.time()
 
    with ProcessPoolExecutor(max_workers=N_WORKERS) as executor:
        futures = {
            executor.submit(process_one, str(cif_path)): cif_path
            for cif_path in cif_files
        }
 
        print(f"All {total} jobs submitted to the pool "
              f"(up to {N_WORKERS} run at once). Waiting for results...\n")
 
        for future in as_completed(futures):
            cif_path = futures[future]
            done += 1
 
            try:
                res = future.result()
            except Exception as e:
                print(f"[{done}/{total}] {cif_path.name}: Error: {e}")
                continue
 
            if "error" in res:
                print(f"[{done}/{total}] {cif_path.name}: Error: {res['error']}")
                continue
 
            results.append(res)
 
            print(
                f"[{done}/{total}] {res['MOF']}: "
                f"LCD={res['LCD_Angstrom']:.2f} Å | "
                f"PLD={res['PLD_Angstrom']:.2f} Å | "
                f"LFPD={res['LFPD_Angstrom']:.2f} Å | "
                f"Pass={res['Filtered']} | "
                f"({res['seconds']}s)"
            )
 
    elapsed = time.time() - batch_start
    print(f"\nWall-clock time for all {total} CIFs: {elapsed:.1f}s")
 
    df = pd.DataFrame(results)
 
    # CSV containing all MOFs
    df.to_csv(ALL_RESULTS_CSV, index=False)
 
    # CSV containing only filtered MOFs
    filtered_df = (
        df[df["Filtered"]]
        .drop(columns=["Filtered", "seconds"])
        .reset_index(drop=True)
    )
 
    filtered_df.to_csv(FILTERED_RESULTS_CSV, index=False)
 
    print(f"\nTotal MOFs       : {len(df)}")
    print(f"Filtered MOFs    : {len(filtered_df)}")
 
    print(f"\nAll Results CSV  : {ALL_RESULTS_CSV}")
    print(f"Filtered CSV     : {FILTERED_RESULTS_CSV}")
    print(f"Filtered CIFs    : {OUTPUT_DIR}")
 
 
def main():
 
    compile_zeopp()
    analyze_mofs()
 
 
if __name__ == "__main__":
    main()