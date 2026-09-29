
## Interactive dashboard (CSV + dynamic rules)

Activate the project virtual environment and install dependencies:

```powershell
pip install -r requirements.txt
python -m streamlit run dashboard.py
```

Open `http://localhost:8501`. Upload a CSV and optionally a YAML (`.yaml`/`.yml`) or JSON (`.json`) rules file. If no rules file is uploaded, `config/rules.yaml` is used. Uploaded rules must follow the same supported rule schema/operators as the engine. Each audit writes uniquely named reports under `reports/<run_id>/` to avoid overwriting another run.

The dashboard validates fields referenced by the selected rules, so users can use different CSV schemas when their rules reference the corresponding columns. Performance should be benchmarked on the target machine and actual rule set; no runtime guarantee is implied without measurement.
