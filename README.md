# Load Cell Force Plotter

This project includes a simple Python tool to view and save force data from the load cell over USB serial.

## Setup

Install the Python packages once:

```powershell
python -m pip install -r tools\requirements-force-plot.txt
```

## Run

Connect the device by USB, then run:

```powershell
python tools\force_plot.py
```

By default it reads from `COM4`, shows a live force plot, and saves data to:

```text
data\force_run.csv
```

## Common Options

Use a different serial port:

```powershell
python tools\force_plot.py --port COM5
```

Save to a different CSV file:

```powershell
python tools\force_plot.py --csv data\my_test.csv
```

Plot without saving:

```powershell
python tools\force_plot.py --no-csv
```
