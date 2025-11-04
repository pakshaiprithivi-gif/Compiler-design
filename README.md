
# 🧠 Consensus Algorithm Demonstrator (Paxos / Raft Model)

## 📘 Overview

The **Consensus Algorithm Demonstrator** is a Python-based simulation of two fundamental distributed consensus algorithms — **Paxos** and **Raft**.
These algorithms ensure that multiple distributed nodes can **agree on a single value**, even if some nodes fail or messages are delayed.

This project helps visualize and understand **how leader election, log replication, and fault tolerance** are achieved in distributed systems.

---

## ⚙️ Features

* ✅ Implements **Paxos Algorithm** (Proposer, Acceptor, Learner)
* ✅ Implements **Raft Algorithm** (Leader Election, Log Replication)
* ⚙️ Simulates network latency and node communication
* 📡 Uses Python’s `asyncio` to simulate concurrent node behavior
* 🧩 Single file, easy to run — no external dependencies

---

## 🖥️ Technologies Used

* **Language:** Python 3.x
* **Libraries:** `asyncio`, `time`, `random`, `collections`
* **Algorithms:** Paxos, Raft

---

## 📂 Project Structure

```
Consensus-Algorithm-Demonstrator/
│
├── paxos_raft_demo.py     # Main simulation file
└── README.md              # Documentation file
```

---

## 🚀 How to Run

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/<your-username>/Consensus-Algorithm-Demonstrator.git
cd Consensus-Algorithm-Demonstrator
```

### 2️⃣ Run Paxos Simulation

```bash
python paxos_raft_demo.py paxos
```

### 3️⃣ Run Raft Simulation

```bash
python paxos_raft_demo.py raft
```

---

## 🧩 Paxos Algorithm Flow

1. **Proposer** sends a prepare request to acceptors.
2. **Acceptors** promise to respond only to higher proposal numbers.
3. **Proposer** sends an accept request with a value.
4. **Learners** learn the chosen value once a majority of acceptors accept it.

📈 **Sample Output:**

```
[P1] Value chosen: ReleaseWater
[Learner L1] Learned: ReleaseWater
```

---

## ⚙️ Raft Algorithm Flow

1. **Nodes** start as followers.
2. **Candidates** start an election after timeout.
3. **Leader** is elected after receiving majority votes.
4. **Leader** replicates log entries to followers.

📈 **Sample Output:**

```
--- Raft Demo ---
[N2] wins election, becomes leader (term 3)
Leader is N2, sending client commands
[N2] Command committed: SetMode=ALERT
[N2] Command committed: ReleaseResources
```

---

## 🔍 Key Concepts

| Algorithm | Component | Description                          |
| --------- | --------- | ------------------------------------ |
| Paxos     | Proposer  | Suggests values for consensus        |
| Paxos     | Acceptor  | Votes on proposed values             |
| Paxos     | Learner   | Learns the final agreed value        |
| Raft      | Leader    | Manages replication and coordination |
| Raft      | Follower  | Responds to leader heartbeats        |
| Raft      | Candidate | Competes to become the next leader   |

---

## 🧠 Learning Outcomes

* Understand **how distributed systems achieve consensus**
* Visualize **leader election and fault tolerance**
* Learn the difference between **Paxos** and **Raft** algorithms

---

## 🔮 Future Enhancements

* Simulate **node failures** and **network partitions**
* Add a **graphical dashboard** to visualize leader elections
* Extend to support **persistent logs and recovery**

---

## 👩‍💻 Author

Akshaya P
Akalya S
Akash S

