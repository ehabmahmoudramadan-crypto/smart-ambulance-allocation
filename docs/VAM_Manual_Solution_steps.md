# Manual VAM Solution Sheet (Vogel's Approximation Method)

**Project:** Smart Ambulance Allocation System | **Role:** VAM Manual Solution 

---

## 1. Model Data

Each cost c_ij is the **estimated travel time in minutes**, so Z is measured in **minutes × allocated ambulances**.

| | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | Supply |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | 17 | 24 | 31 | 15 | 47 | 43 | 32 | 14 | 11 | 42 | 33 | 31 | **10** |
| **S2** | 24 | 6 | 15 | 33 | 24 | 16 | ~~5~~ ✗ | 20 | 26 | 20 | 43 | 28 | **10** |
| **S3** | 31 | 34 | 40 | 8 | 56 | 53 | 26 | 25 | 17 | 47 | 28 | 31 | **10** |
| **S4** | 31 | 17 | 10 | 28 | 28 | 25 | 25 | 13 | 19 | 18 | 28 | 13 | **10** |
| **S5** | 37 | 25 | 9 | 33 | 23 | 26 | 30 | 24 | 1 (≤5) | 13 | 29 | 14 | **9** |
| **S6** | 30 | 17 | 9 | 38 | 17 | 17 | 40 | 25 | 28 | 8 | 38 | 22 | **10** |
| **S7** | 33 | 22 | 8 | 33 | 20 | 20 | 30 | 24 | 23 | 12 | 29 | 14 | **9** |
| **S8** | 15 | 19 | 25 | 21 | 39 | 34 | 32 | 9 | 13 | 33 | 36 | 26 | **10** |
| **Demand** | **4** | **6** | **7** | **4** | **7** | **8** | **7** | **5** | **12** | **6** | **8** | **4** | **78** |

Total supply = total demand = 78, so the problem is balanced. ✗ = closed route (S2→A7, maintenance), (≤5) = route capacity limit (S5→A9).

---

## 2. VAM Rules & Strict Tie-Breaking Protocol

1. **Penalty Calculation:** P = second lowest cost − lowest cost among eligible cells in each active row/column.
2. **Closed Route Exclusion:** S2 → A7 is prohibited (x(S2,A7) = 0).
3. **Capacity Enforcement:** S5 → A9 ≤ 5. Once 5 ambulances are allocated, the cell becomes ineligible.
4. **Step Allocation:** Select the line with the maximum penalty, allocate x = min(remaining supply, remaining demand, remaining route capacity) to the lowest-cost cell.
5. **Strict Tie-Breaking Priority:**
   - **Priority 1:** Row over Column.
   - **Priority 2:** Lowest unit cell cost c_ij in candidate lines.
   - **Priority 3:** Top-leftmost cell (smallest row index, then smallest column index).

---

## 3. Sequential VAM Iterations Log (18 Steps)

Bold = largest penalty. † = tie for the largest penalty, resolved by the tie-breaking priorities above.

| Iter | Row Penalties | Column Penalties | Max Penalty | Selected Cell (c_ij) | Allocated (x) | Remaining Supply | Remaining Demand |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | S1=3, S2=9, S3=9, S4=3, S5=8, S6=1, S7=4, S8=4 | A1=2, **A2=11**, A3=1, A4=7, A5=3, A6=1, A7=1, A8=4, A9=10, A10=4, A11=0, A12=1 | **11 (Col A2)** | **S2 → A2 (6)** | **6** | S2 left 4 | A2 satisfied (0) |
| **2** | S1=3, S2=1, S3=9, S4=3, S5=8, S6=1, S7=4, S8=4 | A1=2, A3=1, A4=7, A5=3, A6=1, A7=1, A8=4, **A9=10**, A10=4, A11=0, A12=1 | **10 (Col A9)** | **S5 → A9 (1)** | **5** | S5 left 4 | A9 left 7 (cap 0) |
| **3** | S1=3, S2=1, **S3=9**, S4=3, S5=4, S6=1, S7=4, S8=4 | A1=2, A3=1, A4=7, A5=3, A6=1, A7=1, A8=4, A9=2, A10=4, A11=0, A12=1 | **9 (Row S3)** | **S3 → A4 (8)** | **4** | S3 left 6 | A4 satisfied (0) |
| **4** | S1=3, S2=1, **S3=8**, S4=3, S5=4, S6=1, S7=4, S8=4 | A1=2, A3=1, A5=3, A6=1, A7=1, A8=4, A9=2, A10=4, A11=0, A12=1 | **8 (Row S3)** | **S3 → A9 (17)** | **6** | S3 exhausted (0) | A9 left 1 |
| **5** | S1=3, S2=1, S4=3, S5=4, S6=1, S7=4, S8=4 | A1=2, A3=1, A5=3, A6=1, **A7=5**, A8=4, A9=2, A10=4, A11=1, A12=1 | **5 (Col A7)** | **S4 → A7 (25)** | **7** | S4 left 3 | A7 satisfied (0) |
| **6** | S1=3, S2=1, S4=3, S5=4, S6=1, **S7=4**, S8=4 | A1=2, A3=1, A5=3, A6=1, A8=4, A9=2, A10=4, A11=1, A12=1 | **4 † (Row S7)** | **S7 → A3 (8)** | **7** | **S7 left 2** | A3 satisfied (0) |
| **7** | S1=3, S2=4, S4=0, S5=1, **S6=9**, S7=2, S8=4 | A1=2, A5=3, A6=1, A8=4, A9=2, A10=4, A11=1, A12=1 | **9 (Row S6)** | **S6 → A10 (8)** | **6** | S6 left 4 | A10 satisfied (0) |
| **8** | S1=3, S2=4, S4=0, **S5=9**, S6=0, S7=6, S8=4 | A1=2, A5=3, A6=1, A8=4, A9=2, A11=1, A12=1 | **9 (Row S5)** | **S5 → A12 (14)** | **4** | S5 exhausted (0) | A12 satisfied (0) |
| **9** | S1=3, S2=4, **S4=6**, S6=0, S7=0, S8=4 | A1=2, A5=3, A6=1, A8=4, A9=2, A11=1 | **6 (Row S4)** | **S4 → A8 (13)** | **3** | S4 exhausted (0) | A8 left 2 |
| **10** | S1=3, S2=4, S6=0, S7=0, S8=4 | A1=2, A5=3, A6=1, **A8=5**, A9=2, A11=4 | **5 (Col A8)** | **S8 → A8 (9)** | **2** | S8 left 8 | A8 satisfied (0) |
| **11** | S1=6, **S2=8**, S6=0, S7=0, S8=2 | A1=2, A5=3, A6=1, A9=2, A11=4 | **8 (Row S2)** | **S2 → A6 (16)** | **4** | S2 exhausted (0) | A6 left 4 |
| **12** | **S1=6**, S6=0, S7=0, S8=2 | A1=2, A5=3, A6=3, A9=2, A11=4 | **6 (Row S1)** | **S1 → A9 (11)** | **1** | S1 left 9 | A9 satisfied (0) |
| **13** | S1=16, S6=0, S7=0, **S8=19** | A1=2, A5=3, A6=3, A11=4 | **19 (Row S8)** | **S8 → A1 (15)** | **4** | S8 left 4 | A1 satisfied (0) |
| **14** | **S1=10**, S6=0, S7=0, S8=2 | A5=3, A6=3, A11=4 | **10 (Row S1)** | **S1 → A11 (33)** | **8** | S1 left 1 | A11 satisfied (0) |
| **15** | S1=4, S6=0, S7=0, **S8=5** | A5=3, A6=3 | **5 (Row S8)** | **S8 → A6 (34)** | **4** | S8 exhausted (0) | A6 satisfied (0) |
| **16** | **S1=47**, S6=17, S7=20 | A5=3 | **47 (Row S1)** | **S1 → A5 (47)** | **1** | S1 exhausted (0) | A5 left 6 |
| **17** | S6=17, **S7=20** | A5=3 | **20 (Row S7)** | **S7 → A5 (20)** | **2** | S7 exhausted (0) | A5 left 4 |
| **18** | **S6=17** | **A5=17** | **17 † (Row S6)** | **S6 → A5 (17)** | **4** | S6 exhausted (0) | A5 satisfied (0) |

---

## 4. Final Initial Allocation Table

| | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | Supply |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | - | - | - | - | **1** | - | - | - | **1** | - | **8** | - | 10 / 10 |
| **S2** | - | **6** | - | - | - | **4** | - | - | - | - | - | - | 10 / 10 |
| **S3** | - | - | - | **4** | - | - | - | - | **6** | - | - | - | 10 / 10 |
| **S4** | - | - | - | - | - | - | **7** | **3** | - | - | - | - | 10 / 10 |
| **S5** | - | - | - | - | - | - | - | - | **5** | - | - | **4** | 9 / 9 |
| **S6** | - | - | - | - | **4** | - | - | - | - | **6** | - | - | 10 / 10 |
| **S7** | - | - | **7** | - | **2** | - | - | - | - | - | - | - | 9 / 9 |
| **S8** | **4** | - | - | - | - | **4** | - | **2** | - | - | - | - | 10 / 10 |
| **Demand** | 4 / 4 | 6 / 6 | 7 / 7 | 4 / 4 | 7 / 7 | 8 / 8 | 7 / 7 | 5 / 5 | 12 / 12 | 6 / 6 | 8 / 8 | 4 / 4 | 78 / 78 |

---

## 5. Total Initial Cost

| Station | Calculation | Cost |
| :--- | :--- | :---: |
| S1 | 1×47 + 1×11 + 8×33 | 322 |
| S2 | 6×6 + 4×16 | 100 |
| S3 | 4×8 + 6×17 | 134 |
| S4 | 7×25 + 3×13 | 214 |
| S5 | 5×1 + 4×14 | 61 |
| S6 | 4×17 + 6×8 | 116 |
| S7 | 7×8 + 2×20 | 96 |
| S8 | 4×15 + 4×34 + 2×9 | 214 |

**Z (VAM) = 322 + 100 + 134 + 214 + 61 + 116 + 96 + 214 = 1257 (minutes × ambulances)**

---

## 6. Verification Checklist & Basis Evaluation

| Check Parameter | Result | Status |
| :--- | :---: | :---: |
| Total Supply = Total Demand | 78 = 78 | Verified (✓) |
| Closed Route Restriction (S2 → A7) | x(S2,A7) = 0 | Compliant (✓) |
| Upper Bound Capacity Limit (S5 → A9) | x(S5,A9) = 5 ≤ 5 | Compliant (✓) |
| Number of Positive Allocated Cells | **18 Cells** | Non-negative Integers (✓) |
| Standard Transportation Basis Formula (m + n − 1) | 8 + 12 − 1 = 19 | **18 Positive Cells (Degenerate Basis)** |



**Handling for MODI:** the 18 positive allocations are fewer than m + n − 1 = 19, so add one symbolic zero allocation ε (0*) at S8 → A9 (cost 13). It is not a real assignment, adds 0 to Z, and connects the two disconnected parts of the basis without forming a closed loop. Note that S5 → A9 is at its upper bound (5), so MODI must use a bounded-variable method, and Z = 1257 is an initial feasible solution, not a proven optimum.
