# Manual VAM Solution (Vogel's Approximation Method)

**Project:** Smart Ambulance Allocation System | **Role:** VAM Manual Solution 

---

## 1. Model Data (Balanced Transportation Problem)

Each cost c_ij is the **estimated travel time in minutes** from station i to area j, so Z is measured in **minutes × allocated ambulances**.

| Station / Area | A1 | A2 | A3 | A4 | A5 | Supply |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | 24 | 45 | 37 | 18 | 19 | **8** |
| **S2** | 28 | 36 | 37 | 13 | 23 | **6** |
| **S3** | 45 | 39 | 31 | 42 | 15 | **7** |
| **S4** | 26 | 42 | 19 | 19 | 18 | **9** |
| **Demand** | **5** | **7** | **6** | **6** | **6** | **30** |

Total supply = total demand = 30, so the problem is balanced and needs no dummy row or column.

---

## 2. VAM Method

- **Penalty** = second-lowest cost − lowest cost among the cells still available in a row or column. If only one cell is left, the penalty equals its cost.
- **Each step:** pick the largest penalty, allocate in the cheapest available cell of that line with **x = min(remaining supply, remaining demand)**, then update supply and demand and cross out any line that reaches zero.
- **Tie rule:** Row before Column, then lowest cost, then first from top-left. No ties occurred here.

---

## 3. VAM Iterations

**Iteration 1 penalties in detail** (two lowest costs in each line):

| Row | Two lowest | Penalty | Column | Two lowest | Penalty |
| :---: | :---: | :---: | :---: | :---: | :---: |
| S1 | 18, 19 | 1 | A1 | 24, 26 | 2 |
| S2 | 13, 23 | 10 | A2 | 36, 39 | 3 |
| S3 | 15, 31 | **16** | A3 | 19, 31 | 12 |
| S4 | 18, 19 | 1 | A4 | 13, 18 | 5 |
| - | - | - | A5 | 15, 18 | 3 |

| Iter | Row penalties | Column penalties | Max | Cell (cost) | x | Effect |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | S1=1, S2=10, **S3=16**, S4=1 | A1=2, A2=3, A3=12, A4=5, A5=3 | 16 (Row S3) | S3→A5 (15) | min(7,6) = **6** | A5 satisfied; S3 left = 1 |
| 2 | S1=6, **S2=15**, S3=8, S4=0 | A1=2, A2=3, A3=12, A4=5 | 15 (Row S2) | S2→A4 (13) | min(6,6) = **6** | S2 and A4 both exhausted |
| 3 | **S1=13**, S3=8, S4=7 | A1=2, A2=3, A3=12 | 13 (Row S1) | S1→A1 (24) | min(8,5) = **5** | A1 satisfied; S1 left = 3 |
| 4 | S1=8, S3=8, **S4=23** | A2=3, A3=12 | 23 (Row S4) | S4→A3 (19) | min(9,6) = **6** | A3 satisfied; S4 left = 3 |

**Remaining (only column A2 is left):** S1→A2 = 3 (cost 45), S3→A2 = 1 (cost 39), S4→A2 = 3 (cost 42). Check: 3 + 1 + 3 = 7 = demand of A2.

---

## 4. Final Initial Allocation Table

Bold = allocated ambulances, (·) = unit cost in minutes.

| | A1 | A2 | A3 | A4 | A5 | Supply |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | **5** (24) | **3** (45) | - | - | - | 8 / 8 |
| **S2** | - | - | - | **6** (13) | - | 6 / 6 |
| **S3** | - | **1** (39) | - | - | **6** (15) | 7 / 7 |
| **S4** | - | **3** (42) | **6** (19) | - | - | 9 / 9 |
| **Demand** | 5 / 5 | 7 / 7 | 6 / 6 | 6 / 6 | 6 / 6 | 30 / 30 |

---

## 5. Total Initial Cost
$\large Z = \sum (x_{ij} \times c_{ij})$
| Station | Calculation | Cost |
| :--- | :--- | :---: |
| S1 | 5×24 + 3×45 = 120 + 135 | 255 |
| S2 | 6×13 | 78 |
| S3 | 1×39 + 6×15 = 39 + 90 | 129 |
| S4 | 3×42 + 6×19 = 126 + 114 | 240 |

**Z (VAM) = 255 + 78 + 129 + 240 = 702 (minutes × ambulances)**
The baseline allocation costs 846, so VAM already saves 144.

---

## 6. Verification Checklist

| Check | Result |
| :--- | :---: |
| Total supply = total demand (30 = 30) | ✓ |
| Row sums = supply (8, 6, 7, 9) | ✓ |
| Column sums = demand (5, 7, 6, 6, 6) | ✓ |
| All x_ij are non-negative integers | ✓ |
| Allocated cells = m + n − 1 = 8 | ✗ (7, degenerate: S2 and A4 exhausted together; MODI must add epsilon S1→A4, x = 0) |

