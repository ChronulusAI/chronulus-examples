

### Install requirements for this example

```bash
pip install -r requirements.txt --upgrade
```

### Run the example

This example assumes a `CHRONULUS_API_KEY` will be entered into the UI at runtime. However, you can still export your key in the `CHRONULUS_API_KEY` environment variable if you prefer.


### Sports Prediction Demos

```bash 
ENTRY=sports streamlit run sports_main.py --server.port=8501 --server.address=0.0.0.0 --server.headless 1
```


### Finance & Markets Demos

```bash 
ENTRY=fin streamlit run fin_main.py --server.port=8502 --server.address=0.0.0.0 --server.headless 1
```