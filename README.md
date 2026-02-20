Project Title

MullBar: Graph-Based Money Muling & Fraud Ring Detection System

Live Demo URL

Local Deployment:

http://127.0.0.1:5000


(Replace with production URL if deployed on Render / AWS / etc.)

Tech Stack
Backend

Python 3.x

Flask

NetworkX

Pandas

NumPy

Frontend

HTML

CSS

JavaScript

🏗 System Architecture:

Transaction Dataset (CSV)
            ↓
Data Ingestion Module
            ↓
Graph Builder (NetworkX Directed Graph)
            ↓
Pattern Detection Engine
            ↓
Fraud Ring Identification
            ↓
Suspicion Scoring Engine
            ↓
Flask Web Interface (Visualization & Results)

🔍 Algorithms Used in MullBar

The system uses Graph Theory–based algorithms to detect structured financial fraud patterns.

1️⃣ Graph Construction

Library Used: NetworkX
Type: Directed Graph (DiGraph)

Algorithm:

Add nodes for each unique account

Add directed edges for each transaction

Complexity:

O(V + E)

Where:

V = Number of accounts

E = Number of transactions

2️⃣ Cycle Detection Algorithm

Technique Used: Depth First Search (DFS)

Purpose:

Detect circular transaction flows such as:

A → B → C → A

Why DFS?

DFS efficiently detects back edges in directed graphs, which indicate cycles.

Complexity:

O(V + E)

3️⃣ Multi-Hop (Layered Transfer) Detection

Technique Used: Breadth First Search (BFS)

Purpose:

Detect long transaction chains such as:

Victim → Mule1 → Mule2 → Mule3 → Hacker

Why BFS?

BFS explores graph level-by-level, making it suitable for detecting transaction depth and layering.

Complexity:

O(V + E)

4️⃣ Smurfing Detection (Fan-In & Fan-Out)

Technique Used: Degree-Based Analysis

Fan-Out Detection:

Compute Out-Degree of each node

Flag nodes with unusually high outgoing connections

Fan-In Detection:

Compute In-Degree of each node

Flag nodes receiving funds from many accounts

Why Degree Analysis?

Smurfing patterns are structural behaviors reflected in node connectivity.

Complexity:

O(V)

(Degree computation is linear in number of nodes)

5️⃣ Fraud Ring Detection

Technique Used: Connected Components Analysis

Purpose:

Identify clusters of tightly connected accounts operating together.

Method:

Find strongly connected components (SCC) in directed graph
OR

Identify connected subgraphs

Why This Method?

Fraud rings often form dense internal transaction groups.

Complexity:

O(V + E)

6️⃣ Suspicion Score Computation

Technique Used: Rule-Based Weighted Scoring Model

Approach:

Aggregate pattern detections into weighted risk score:

Cycle involvement

Multi-hop depth

Smurfing behavior

Transaction frequency

Transaction volume

Complexity:

O(V)

(Score computed once per account)

📊 Suspicion Score Methodology

Each account receives a Suspicion Score (0–100) based on detected behaviors.

Scoring Components
Factor	Weight
Cycle Participation	+30
Multi-Hop Involvement	+20
Star Centrality	+15
High Transaction Frequency	+15
Large Transaction Amount	+20
Final Formula
Suspicion Score =
CycleScore +
LayeringScore +
CentralityScore +
FrequencyScore +
AmountScore

Risk Classification
Score Range	Risk Level
0 – 30	Low Risk
31 – 60	Medium Risk
61 – 80	High Risk
81 – 100	Critical Risk
Good Model Characteristics

High scores for structured fraud rings

Low scores for normal users

Clear separation between suspicious and legitimate accounts

Reduced false positives

⚙ Installation & Setup
1️⃣ Extract ZIP

Unzip the project folder.

2️⃣ Navigate to Project Directory
cd MullBar---Money-Mulling-Detection-

3️⃣ Create Virtual Environment
python -m venv venv


Activate:

Windows:

venv\Scripts\activate


Mac/Linux:

source venv/bin/activate

4️⃣ Install Dependencies
pip install -r requirements.txt

5️⃣ Run Application
python app.py


Open in browser:

http://127.0.0.1:5000

🚀 Usage Instructions

Launch the application.

Upload transaction dataset (CSV format).

Click Run Analysis.

System will:

Build transaction graph

Detect suspicious patterns

Identify fraud rings

Calculate suspicion scores

View:

Fraud Ring Summary

Suspicious Accounts List

Risk Levels

⚠ Known Limitations

Batch processing only (not real-time streaming)

Rule-based scoring (not ML-based)

Scalability limited for very large datasets (>1M transactions)

Possible false positives in high-volume legitimate accounts

Requires properly formatted CSV input

👩‍💻 Team Members

Gade Tejaswi

Medamreddy Sivani 

Chintanippula Vidya Sravani 
 

