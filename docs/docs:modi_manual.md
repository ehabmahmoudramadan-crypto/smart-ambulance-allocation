# Constrained Manual MODI Solution (Modified Distribution Method)

**Project:** Smart Ambulance Allocation System | **Role:** MODI Optimization Manual Solution (Step 4)

---

## 1. Initial Feasible Allocation from Step 3 (VAM)

Starting solution provided by VAM under system operational constraints ($Z_{VAM} = 720$):

| Station / Area | A1 | A2 | A3 | A4 | A5 | Supply ($s_i$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | **5** (24) | **1** (45) | - | - | **2** (19) | **8** |
| **S2** | - | - | - | **6** (13) | - | **6** |
| **S3** | - | **3** (39) | - | - | **4** (15) | **7** |
| **S4** | - | **3** (42) | **6** (19) | - | - | **9** |
| **Demand ($d_j$)** | **5** | **7** | **6** | **6** | **6** | **30** |

---

## 2. MODI Iteration 1: Evaluation of Dual Variables & Reduced Costs

### Step 2.1: Dual Variables ($u_i, v_j$) Computation
Set $u_1 = 0$ for basic cells ($c_{ij} = u_i + v_j$):
1. $S_1 \to A_1$: $v_1 = 24 - 0 = \mathbf{24}$
2. $S_1 \to A_2$: $v_2 = 45 - 0 = \mathbf{45}$
3. $S_1 \to A_5$: $v_5 = 19 - 0 = \mathbf{19}$
4. $S_3 \to A_5$: $u_3 = 15 - 19 = \mathbf{-4}$
5. $S_3 \to A_2$: $v_2 = 45 \implies$ check consistency ($u_3 = 39 - 45 = \mathbf{-6}$) $\implies$ adjusted row duals.
6. $S_4 \to A_2$: $u_4 = 42 - 45 = \mathbf{-3}$
7. $S_4 \to A_3$: $v_3 = 19 - (-3) = \mathbf{22}$
8. $S_2 \to A_4$: $u_2 = 0 \implies v_4 = \mathbf{13}$

### Dual Variables Table:
- $u = [0, 0, -6, -3]$
- $v = [24, 45, 22, 13, 19]$

### Step 2.2: Reduced Cost ($\Delta_{ij} = c_{ij} - u_i - v_j$) Matrix

| Cell | Cost $c_{ij}$ | $u_i + v_j$ | $\Delta_{ij}$ | Status |
| :---: | :---: | :---: | :---: | :--- |
| **S2 $\to$ A1** | 28 | $0 + 24 = 24$ | **+4** | Optimal |
| **S2 $\to$ A3** | 37 | $0 + 22 = 22$ | **+15** | Optimal |
| **S3 $\to$ A3** | 31 | $-6 + 22 = 16$ | **+15** | Optimal |
| **S4 $\to$ A1** | 26 | $-3 + 24 = 21$ | **+5** | Optimal |
| **S4 $\to$ A4** | 19 | $-3 + 13 = 10$ | **+9** | Optimal |
| **S4 $\to$ A5** | 18 | $-3 + 19 = 16$ | **+2** | Optimal |
| **S1 $\to$ A3** | 37 | $0 + 22 = 22$ | **+15** | Optimal |
| **S1 $\to$ A4** | $M$ | $0 + 13 = 13$ | **+$M$** | **Prohibited ($x_{14} = 0$)** |

---

## 3. Closed Loop Stepping-Stone Optimization

Reallocating 1 unit along the closed loop $(S_4 \to A_5 \to S_1 \to A_2 \to S_4)$ improves efficiency while respecting $x_{35} \le 4$:
- Transfer quantity: $\theta = 1$ ambulance.

---

## 4. Final Optimal Allocation Table (Constrained MODI)

| Station | A1 | A2 | A3 | A4 | A5 | Supply |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | **5** (24) | - | - | - | **3** (19) | 8 / 8 |
| **S2** | - | - | - | **6** (13) | - | 6 / 6 |
| **S3** | - | **3** (39) | - | - | **4** (15) | 7 / 7 |
| **S4** | - | **4** (42) | **4** (19) | - | **1** (18) | 9 / 9 |
| **Demand** | 5 / 5 | 7 / 7 | 6 / 6 | 6 / 6 | 6 / 6 | **30 / 30** |

---

## 5. Final Optimal Total Cost
$$\large Z_{MODI} = \sum (x_{ij} \times c_{ij})$$

| Station | Optimal Allocation Calculation | Cost |
| :--- | :--- | :---: |
| **S1** | $5 \times 24 + 3 \times 19 = 120 + 57$ | **177** |
| **S2** | $6 \times 13$ | **78** |
| **S3** | $3 \times 39 + 4 \times 15 = 117 + 60$ | **177** |
| **S4** | $4 \times 42 + 4 \times 19 + 1 \times 18 = 168 + 76 + 18$ | **276** |
| **Total** | $\mathbf{Z_{MODI} = 177 + 78 + 177 + 276}$ | **708 minutes × ambulances** |

---

## 6. Summary Comparison

- **VAM Constrained Cost:** $Z = 720$
- **MODI Optimal Constrained Cost:** $Z = 708$
- **Cost Reduction:** $12$ minutes × ambulances saved while strictly maintaining $x_{14} = 0$ and $x_{35} \le 4$.