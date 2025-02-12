# Forensic Event Reconstruction App

This application is designed to generate visualizations in the form of Petri Nets, display metric evaluations, and produce event sequences in the form of alignment traces. It utilizes process mining and episode mining techniques to reconstruct events from forensic timeline.


## How to install

### 1. Create Anaconda Virtual Environment

```bash
conda create --name forensic-event-reconstruction-app
```

### 2. Activate the Virtual Environment

```bash
conda activate forensic-event-reconstruction-app
```

### 3. Clone the repository

```bash
git clone https://github.com/ridaadila/forensic-event-reconstruction-app.git
```

### 4. Install requirements.txt in the root directory of the project

```bash
pip install -r requirements.txt
```

## How to run

### 1. Run the following command inside the virtualenv in the root directory of the project:
```bash
python main.py
```

### 2. Open the application in your browser
Once the application is running, open your browser and navigate to: http://127.0.0.1:5000/

### 3. View the Homepage
The application will display the following homepage:

![Alt text](./docs/homepage.png)

## References
1) https://github.com/logpai/Drain3
2) https://www.philippe-fournier-viger.com/spmf/index.php?link=documentation.php
3) https://github.com/process-intelligence-solutions/pm4py

