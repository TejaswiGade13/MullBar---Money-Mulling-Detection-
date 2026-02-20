# 🕵️ MullBar — Money Muling & Fraud Ring Detection

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![NetworkX](https://img.shields.io/badge/Graph-NetworkX-orange)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-green)
![Built By Students](https://img.shields.io/badge/Built%20By-Students-purple)

> **A graph-based fraud detection system built to uncover suspicious transaction patterns — the student way.**

Ever wondered how banks detect money muling networks?  
Or how complex transaction webs can reveal hidden fraud rings?

**MullBar** is a graph-driven fraud detection platform that analyzes transaction datasets to uncover suspicious accounts, detect coordinated fraud rings, and compute interpretable risk scores — all through a clean web interface.

Built with a focus on **explainability, clarity, and real-world patterns**, this project demonstrates how graph theory can power intelligent financial monitoring systems.

---

## 🌐 Live Demo

**Deployment:**  
👉 https://mulbarr.onrender.com

*(Replace with your Render URL when deployed)*

---

## 🧰 Tech Stack

### 🧠 Backend
- Python 3
- Flask
- NetworkX
- Pandas
- NumPy

### 🎨 Frontend
- HTML
- CSS
- JavaScript

### 📊 Data Processing
- CSV transaction datasets
- Graph analytics
- Rule-based scoring engine

---

## 🏗 System Architecture

```markdown
## 🏗 System Architecture Flow

```mermaid
flowchart TD
    T([MullBar System Architecture])

    T --> A[Transaction Dataset (CSV)]
    A --> B[Data Ingestion Module]
    B --> C[Graph Builder (Directed Graph)]
    C --> D[Pattern Detection Engine]
    D --> E[Fraud Ring Identification]
    E --> F[Suspicion Scoring Engine]
    F --> G[Flask Web Interface]

    classDef main fill:#84934A,color:#fff,stroke:#492828,stroke-width:2px;
    classDef process fill:#ECECEC,stroke:#656D3F,stroke-width:2px,color:#000;

    class T main;
    class A,B,C,D,E,F,G process;

The system converts raw transactions into a graph structure and runs multiple detection algorithms to uncover suspicious behaviors.
```
---

## ⚙ Algorithm Approach

MullBar uses **graph theory + behavioral heuristics** to detect fraud patterns.

### 1️⃣ Graph Construction
- Directed graph using NetworkX
- Nodes → Accounts
- Edges → Transactions  

**Complexity:** `O(V + E)`

---

### 2️⃣ Cycle Detection (Circular Transfers)
Uses **Depth First Search (DFS)** to detect loops like:

A → B → C → A  

**Complexity:** `O(V + E)`

---

### 3️⃣ Multi-Hop Layering Detection
Uses **Breadth First Search (BFS)** to detect long transaction chains.  

**Complexity:** `O(V + E)`

---

### 4️⃣ Smurfing Detection
Degree-based analysis to detect:
- High fan-in
- High fan-out  

**Complexity:** `O(V)`

---

### 5️⃣ Fraud Ring Detection
Strongly Connected Components (SCC) analysis identifies tightly connected clusters.  

**Complexity:** `O(V + E)`

---

### 6️⃣ Suspicion Score Computation
Rule-based weighted scoring model aggregates detected behaviors.  

**Complexity:** `O(V)`

---

Transaction Dataset (CSV)
↓
Data Ingestion Module
↓
Graph Builder (Directed Graph)
↓
Pattern Detection Engine
↓
Fraud Ring Identification
↓
Suspicion Scoring Engine
↓
Flask Web Interface


## 📊 Suspicion Score Methodology

Each account receives a **0–100 risk score** based on behavioral indicators.

### 🎯 Scoring Factors

| Factor | Weight |
|--------|--------|
| Cycle Participation | +30 |
| Multi-Hop Layering | +20 |
| Star Centrality | +15 |
| High Transaction Frequency | +15 |
| Large Transaction Amount | +20 |

---

### 🧮 Final Score Formula

Suspicion Score =
CycleScore +
LayeringScore +
CentralityScore +
FrequencyScore +
AmountScore


---

### 🚨 Risk Levels

| Score | Risk |
|------|------|
| 0–30 | Low |
| 31–60 | Medium |
| 61–80 | High |
| 81–100 | Critical |

---

## 🧪 Installation & Setup

### 1️⃣ Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/mullbar.git
cd mullbar

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt 

👉 http://127.0.0.1:5000
```


## 🚀 Usage Instructions

1️⃣ Launch the web app  
2️⃣ Upload a transaction CSV dataset  
3️⃣ Click **Run Analysis**  

The system will:

✅ Build transaction graph  
✅ Detect suspicious patterns  
✅ Identify fraud rings  
✅ Compute risk scores  

You’ll see:

- Suspicious accounts list  
- Fraud ring summaries  
- Risk classifications  
- Behavioral insights  

---

## ⚠ Known Limitations

- Batch processing only (no real-time streaming)  
- Rule-based scoring (not ML-driven)  
- Performance may degrade for very large datasets  
- Possible false positives for high-volume legitimate accounts  
- Requires correctly formatted CSV input  

---

## 👩‍💻 Team Members

- **Gade Tejaswi**  
- **Medamreddy Sivani**  
- **Chintanippula Vidya Sravani**  

