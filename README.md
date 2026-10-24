# Zeo++

A Python-based tool for analyzing Metal–Organic Framework (MOF) CIF structures using [Zeo++](https://github.com/richardjgowers/zeoplusplus).

The script calculates the **Largest Cavity Diameter (LCD)**, **Pore Limiting Diameter (PLD)**, and **Largest Free Sphere Path Diameter (LFPD)** for each MOF. It applies configurable LCD and PLD thresholds, generates CSV reports, and copies qualifying CIF files into the output directory.

## Features

- Calculates LCD, PLD, and LFPD using Zeo++.
- Processes multiple CIF files in parallel using `ProcessPoolExecutor`.
- Filters MOFs according to configurable LCD and PLD ranges.
- Generates CSV reports containing pore properties.

## Requirements

- Python 3.10.
- Conda or Miniconda.
- Zeo++ source code, already included in this repository.
- MOF CIF input files.
- A compatible C/C++ compiler and `make`.

## 1. Clone the Repository

```bash
git clone https://github.com/grp27-kmof/Zeo.git
cd Zeo
```

## 2. Create a Conda Environment

```bash
conda create -n zeo python=3.10 -y
```

## 3. Activate the Environment

```bash
conda activate zeo
```

## 4. Install Dependencies

Install the required Python packages:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 5. Extract and Compile Zeo++

The Zeo++ source archive is included in this repository. If it is provided as `zeo++-0.3.tar`, extract it in the repository root.

```bash
tar -xf zeo++-0.3.tar
```

Compile Voro++:

```bash
cd zeo++-0.3/voro++/src
make
```

Compile Zeo++:

```bash
cd ../..
make
```

Return to the repository root:

```bash
cd ..
```

Verify that the Zeo++ executable exists:

```bash
ls zeo++-0.3/network
```

The script automatically checks whether the `network` executable exists and attempts to compile Zeo++ if it does not.

## 6. Add Input CIF Files

Place the MOF CIF files you want to analyze in the `input/` directory.

The script processes `.cif` files directly inside this directory.

## 7. Configure the Analysis

Open `main.py` and review the following settings:

```python
PLD_MIN = 2.66
PLD_MAX = 10.0

LCD_MIN = 2.66
LCD_MAX = 20.0

N_WORKERS = 25
```

### LCD and PLD filtering

A MOF passes the filter when both conditions are satisfied:

- LCD is between 2.66 Å and 20.0 Å, inclusive.
- PLD is between 2.66 Å and 10.0 Å, inclusive.

These are the configured screening ranges used by this script. Modify the values in `main.py` if you need different thresholds.

### Parallel execution

The script uses `ProcessPoolExecutor` to process multiple CIF files concurrently.

This configuration was used on a **32-core workstation with 25 workers**. Adjust `N_WORKERS` according to your system's CPU resources and available RAM. Using too many workers can increase memory consumption without improving performance.

## 8. Run the Script

From the repository root, execute:

```bash
python main.py
```

The script checks whether Zeo++ needs to be compiled, finds the input CIF files, and launches the parallel analysis.

Example terminal output (illustrative; actual filenames, values, and timings will differ):

```text
ZEO++ already compiled.

Found 1000 CIF files.
Launching pool of 25 worker processes...

All 1000 jobs submitted to the pool (up to 25 run at once). Waiting for results...

[1/1000] MOF_001.cif: LCD=8.42 Å | PLD=3.12 Å | LFPD=2.85 Å | Pass=True | (0.14s)
[2/1000] MOF_002.cif: LCD=12.65 Å | PLD=2.40 Å | LFPD=2.18 Å | Pass=False | (0.11s)

Wall-clock time for all 1000 CIFs: 15.2s

Total MOFs       : 1000
Filtered MOFs    : 420

All Results CSV  : /path/to/repository/all_mof_properties.csv
Filtered CSV     : /path/to/repository/filtered_mofs.csv
Filtered CIFs    : /path/to/repository/output
```

The example values and counts above are illustrative, not measured results.

## 9. Output Files

After execution, the script generates two CSV reports in the repository root.

### `all_mof_properties.csv`

Contains the successful analyses, including:

- `MOF` — input CIF filename.
- `LCD_Angstrom` — Largest Cavity Diameter in Å.
- `PLD_Angstrom` — Pore Limiting Diameter in Å.
- `LFPD_Angstrom` — Largest Free Sphere Path Diameter in Å.
- `Filtered` — whether the MOF satisfies both configured thresholds.
- `seconds` — processing time for that CIF, in seconds.

### `filtered_mofs.csv`

Contains only MOFs that pass the LCD and PLD filters. The `Filtered` and `seconds` columns are omitted from this report.

### `output/`

Contains copies of the original CIF files that pass both configured filters.

**Note:** CIF files that fail processing are printed as errors and are not included in the current CSV results. The final completion message does not guarantee that every input CIF was analyzed successfully.

## Acknowledgements

This project uses:

- [Zeo++](https://github.com/richardjgowers/zeoplusplus) for pore geometry analysis.
- [Pandas](https://pandas.pydata.org/) for CSV generation and data handling.

