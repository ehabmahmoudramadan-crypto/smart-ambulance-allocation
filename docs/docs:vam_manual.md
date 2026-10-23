# Constrained Manual VAM Solution (Vogel's Approximation Method)

**Project:** Smart Ambulance Allocation System | **Role:** VAM Manual Solution (Step 3)

---

## 1. Model Data & Operational Constraints

Each cost $c_{ij}$ represents the **estimated travel time in minutes** from station $i$ to area $j$. Total system objective $Z$ is measured in **minutes × allocated ambulances**.

### Operational Constraints Applied:
1. **Prohibited Route:** $S_1 \to A_4$ is blocked due to emergency roadworks ($x_{14} = 0, c_{14} = M = \infty$).
2. **Maximum Capacity Cap:** $S_3 \to A_5 \le 4$ ambulances max to avoid traffic bottlenecks.

| Station / Area | A1 | A2 | A3 | A4 | A5 | Supply ($s_i$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | 24 | 45 | 37 | **M** | 19 | **8** |
| **S2** | 28 | 36 | 37 | 13 | 23 | **6** |
| **S3** | 45 | 39 | 31 | 42 | 15 *(Cap ≤ 4)* | **7** |
| **S4** | 26 | 42 | 19 | 19 | 18 | **9** |
| **Demand ($d_j$)** | **5** | **7** | **6** | **6** | **6** | **30** |

Total supply = total demand = 30 ambulances (Balanced Problem).

---

## 2. Constrained VAM Methodology

- **Penalty Calculation:** Difference between the two lowest costs in each active line. Blocked routes ($M$) are excluded from penalty calculations.
- **Capacity Constraint Rule:** Allocation to $(S_3, A_5)$ cannot exceed 4 units regardless of remaining supply/demand.
- **Iteration Execution:** Pick the line with the maximum penalty, allocate $\min(\text{Supply}, \text{Demand}, \text{Capacity Cap})$, update remaining values, and cross out satisfied lines.

---

## 3. Detailed VAM Iterations

### Iteration Step Breakdown:

| Iter | Max Penalty Line | Selected Cell (Cost) | Allocation ($x_{ij}$) | Constraint Consideration & System Effect |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Row S3** (Penalty = 16) | $S_3 \to A_5$ (15) | $\min(7, 6, \mathbf{4}) = \mathbf{4}$ | **Capacity Cap Hit ($x_{35} \le 4$)**; $S_3$ supply left = 3; $A_5$ demand left = 2. |
| **2** | **Row S2** (Penalty = 15) | $S_2 \to A_4$ (13) | $\min(6, 6) = \mathbf{6}$ | $S_2$ & $A_4$ exhausted simultaneously (Degeneracy introduced). |
| **3** | **Row S4** (Penalty = 23) | $S_4 \to A_3$ (19) | $\min(9, 6) = \mathbf{6}$ | $A_3$ satisfied; $S_4$ supply left = 3. |
| **4** | **Row S1** (Penalty = 5) | $S_1 \to A_5$ (19) | $\min(8, 2) = \mathbf{2}$ | $A_5$ demand fully satisfied; $S_1$ supply left = 6. |
| **5** | **Row S1** (Penalty = 21) | $S_1 \to A_1$ (24) | $\min(6, 5) = \mathbf{5}$ | $A_1$ satisfied; $S_1$ supply left = 1. |

**Remaining Allocation (Column $A_2$ only):**
- $S_1 \to A_2 = 1$ unit (Cost = 45)
- $S_3 \to A_2 = 3$ units (Cost = 39)
- $S_4 \to A_2 = 3$ units (Cost = 42)
- *Check:* $1 + 3 + 3 = 7$ units = Demand of $A_2$.

---

## 4. Final Initial Allocation Table (Constrained VAM)

Bold numbers = allocated ambulances, $(\cdot)$ = unit travel cost in minutes.

| Station | A1 | A2 | A3 | A4 | A5 | Supply |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | **5** (24) | **1** (45) | - | **0** ($M$) | **2** (19) | 8 / 8 |
| **S2** | - | - | - | **6** (13) | - | 6 / 6 |
| **S3** | - | **3** (39) | - | - | **4** (15) | 7 / 7 |
| **S4** | - | **3** (42) | **6** (19) | - | - | 9 / 9 |
| **Demand** | 5 / 5 | 7 / 7 | 6 / 6 | 6 / 6 | 6 / 6 | **30 / 30** |

---

## 5. Total Initial Cost Calculation
$$\large Z_{VAM} = \sum (x_{ij} \times c_{ij})$$

| Station | Allocated Routes Calculation | Cost Contribution |
| :--- | :--- | :---: |
| **S1** | $5 \times 24 + 1 \times 45 + 2 \times 19 = 120 + 45 + 38$ | **203** |
| **S2** | $6 \times 13$ | **78** |
| **S3** | $3 \times 39 + 4 \times 15 = 117 + 60$ | **177** |
| **S4** | $3 \times 42 + 6 \times 19 = 126 + 114$ | **262** |
| **Total** | $\mathbf{Z_{VAM} = 203 + 78 + 177 + 262}$ | **720 minutes × ambulances** |

---

## 6. Verification & Handover Checklist

| Verification Metric | Result | Status |
| :--- | :---: | :---: |
| Total Supply = Total Demand (30 = 30) | Verified | ✓ |
| Prohibited Route $S_1 \to A_4 = 0$ | Verified ($x_{14} = 0$) | ✓ |
| Route Capacity $S_3 \to A_5 \le 4$ | Verified ($x_{35} = 4$) | ✓ |
| Non-degeneracy Check ($m + n - 1 = 8$) | 8 Basic Variables | ✓ |