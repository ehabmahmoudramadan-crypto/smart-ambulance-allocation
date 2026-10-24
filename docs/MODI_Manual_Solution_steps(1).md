# Manual MODI Solution Sheet (Modified Distribution Method)

**Project:** Smart Ambulance Allocation System | **Role:** MODI Manual Solution

---

## 1. Model Data Matrix (Costs in minutes)

Each cost $c_{ij}$ is the **estimated travel time in minutes**, so $Z$ is measured in **minutes × allocated ambulances**.

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

Total supply = total demand = 78, so the problem is balanced. ✗ = closed route ($S_2 \to A_7$, maintenance)[cite: 16], (≤5) = route capacity limit ($S_5 \to A_9$)[cite: 16].

---

## 2. MODI Optimization Principles & Dual Potentials

1. **Starting Point:** Initial feasible allocation from VAM ($Z_{VAM} = 1257$)[cite: 16].
2. **Dual Variable System:** For all basic cells $(i, j)$, evaluate row potentials $u_i$ and column potentials $v_j$ satisfying $u_i + v_j = c_{ij}$[cite: 16].
3. **Reduced Cost Evaluation:** For non-basic cells, compute opportunity cost $\Delta_{ij} = c_{ij} - (u_i + v_j)$[cite: 16].
4. **Bounded Route Condition:** $S_5 \to A_9$ is at its maximum upper bound of 5 ambulances ($x_{5,9} = 5$)[cite: 16]. Its reduced cost satisfies upper-bound optimality conditions ($\Delta_{5,9} \le 0$)[cite: 16].
5. **Prohibited Route Condition:** Closed route $S_2 \to A_7$ has $c_{2,7} = M = 999999$, ensuring $\Delta_{2,7} \gg 0$ and no flow allocation[cite: 16].

### Final Dual Potentials ($u_i, v_j$)
- **Row Potentials ($u_i$):** $u_1=0$, $u_2=0$, $u_3=-5$, $u_4=-6$, $u_5=-7$, $u_6=1$, $u_7=-8$, $u_8=1$
- **Column Potentials ($v_j$):** $v_1=14$, $v_2=6$, $v_3=16$, $v_4=13$, $v_5=28$, $v_6=16$, $v_7=31$, $v_8=8$, $v_9=11$, $v_{10}=7$, $v_{11}=33$, $v_{12}=19$

---

## 3. Final Optimal MODI Allocation Matrix

| | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | Supply |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | - | - | - | - | - | - | - | - | **7** | - | **3** | - | 10 / 10 |
| **S2** | - | **6** | - | - | - | **4** | - | - | - | - | - | - | 10 / 10 |
| **S3** | - | - | - | **4** | - | - | **1** | - | - | - | **5** | - | 10 / 10 |
| **S4** | - | - | **1** | - | - | - | **5** | - | - | - | - | **4** | 10 / 10 |
| **S5** | - | - | **4** | - | - | - | - | - | **5** | - | - | - | 9 / 9 |
| **S6** | - | - | - | - | - | **4** | - | - | - | **6** | - | - | 10 / 10 |
| **S7** | - | - | **2** | - | **7** | - | - | - | - | - | - | - | 9 / 9 |
| **S8** | **4** | - | - | - | - | - | **1** | **5** | - | - | - | - | 10 / 10 |
| **Demand** | 4 / 4 | 6 / 6 | 7 / 7 | 4 / 4 | 7 / 7 | 8 / 8 | 7 / 7 | 5 / 5 | 12 / 12 | 6 / 6 | 8 / 8 | 4 / 4 | 78 / 78 |

---

## 4. Total Optimal Cost Breakdown

| Station | Calculation | Cost |
| :--- | :--- | :---: |
| S1 | 7×11 + 3×33 | 176 |
| S2 | 6×6 + 4×16 | 100 |
| S3 | 4×8 + 1×26 + 5×28 | 198 |
| S4 | 1×10 + 5×25 + 4×13 | 187 |
| S5 | 4×9 + 5×1 | 41 |
| S6 | 4×17 + 6×8 | 116 |
| S7 | 2×8 + 7×20 | 156 |
| S8 | 4×15 + 1×32 + 5×9 | 137 |

**Z (MODI Optimal) = 176 + 100 + 198 + 187 + 41 + 116 + 156 + 137 = 1111 (minutes × ambulances)**

---

## 5. Optimization Comparison & Executive Impact

| Optimization Stage | Total Cost (Minutes × Ambulances) | Cost Savings vs Baseline | Operational Status |
| :--- | :---: | :---: | :--- |
| **Current Baseline Allocation** | **2097** | - | Basic Supply & Demand met[cite: 16] |
| **VAM Initial Solution** | **1257** | **840 mins saved (-40.1%)** | Feasible Constrained Solution[cite: 16] |
| **MODI Optimal Solution** | **1111** | **986 mins saved (-47.0%)** | Fully Optimized ($Z = 1111$) |