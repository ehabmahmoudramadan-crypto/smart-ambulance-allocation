# Step 4: MODI Method — Optimal Solution and Optimality Verification

## 1. Purpose and transportation data

The Modified Distribution method (MODI), also called the **u-v method**, checks whether the initial feasible solution from Vogel's Approximation Method (VAM) can be improved. The objective is to minimize the total transportation cost.

- Total supply: \(8+6+7+9=30\)
- Total demand: \(5+7+6+6+6=30\)
- The problem is balanced.
- Number of rows: \(m=4\); number of columns: \(n=5\).
- A non-degenerate basis requires \(m+n-1=8\) basic cells.

### Cost matrix

| Station / Area | A1 | A2 | A3 | A4 | A5 | Supply |
|:--|--:|--:|--:|--:|--:|--:|
| S1 | 24 | 45 | 37 | 18 | 19 | 8 |
| S2 | 28 | 36 | 37 | 13 | 23 | 6 |
| S3 | 45 | 39 | 31 | 42 | 15 | 7 |
| S4 | 26 | 42 | 19 | 19 | 18 | 9 |
| **Demand** | **5** | **7** | **6** | **6** | **6** | **30** |

## 2. Initial solution from VAM

The VAM allocation for this data is:

| Station / Area | A1 | A2 | A3 | A4 | A5 | Row total |
|:--|--:|--:|--:|--:|--:|--:|
| **S1** | 5 | 3 | 0 | 0 | 0 | **8** |
| **S2** | 0 | 0 | 0 | 6 | 0 | **6** |
| **S3** | 0 | 1 | 0 | 0 | 6 | **7** |
| **S4** | 0 | 3 | 6 | 0 | 0 | **9** |
| **Column total** | **5** | **7** | **6** | **6** | **6** | **30** |

Its cost is:

\[
Z_0=(5\times24)+(3\times45)+(6\times13)+(1\times39)+(6\times15)+(3\times42)+(6\times19)=702.
\]

There are **7 positive allocations**, fewer than the 8 basic cells required. Therefore, this is a **degenerate** transportation solution. For MODI, include one zero-valued \(\varepsilon\) basic cell that does not create a closed loop. The zero basic cell is part of the basis only; it does not change supply, demand, or cost.

> Important correction: do not use the alternative initial matrix with S1 = (2, 0, 0, 6, 0), S2 = (0, 6, 0, 0, 0), S3 = (1, 0, 0, 0, 6), and S4 = (2, 1, 6, 0, 0) while labelling its cost as 702. That matrix has a cost of 715 and is not the VAM result for the supplied data.

## 3. MODI method

For each basic cell, calculate row and column potentials using:

\[
c_{ij}=u_i+v_j.
\]

Set one potential, conventionally \(u_1=0\), and solve the equations for the remaining potentials. Then calculate each non-basic cell's reduced cost:

\[
\Delta_{ij}=c_{ij}-(u_i+v_j).
\]

For a minimization problem:

- If all non-basic reduced costs are \(\Delta_{ij}\geq0\), the current solution is optimal.
- If any reduced cost is negative, choose a negative reduced-cost cell to enter the basis and form a closed loop through basic cells. Put alternating plus and minus signs around the loop.
- Set \(\theta\) to the smallest allocation at a minus position. Add \(\theta\) to plus cells and subtract it from minus cells. If a basic allocation becomes zero, remove the appropriate zero cell from the basis while retaining a valid basis of 8 cells.

Because the starting VAM solution is degenerate, the selected zero-valued basic cell can affect the sequence of intermediate MODI calculations. The essential requirements are to use a valid basis throughout, preserve all row and column totals, and verify optimality using the final reduced costs.

## 4. Final optimal allocation

A MODI optimal allocation for the supplied data is:

| Station / Area | A1 | A2 | A3 | A4 | A5 | Row total |
|:--|--:|--:|--:|--:|--:|--:|
| **S1** | 5 | 0 | 0 | 3 | 0 | **8** |
| **S2** | 0 | 3 | 0 | 3 | 0 | **6** |
| **S3** | 0 | 1 | 0 | 0 | 6 | **7** |
| **S4** | 0 | 3 | 6 | 0 | 0 | **9** |
| **Column total** | **5** | **7** | **6** | **6** | **6** | **30** |

The row totals equal the supplies and the column totals equal the demands, so the allocation is feasible.

### Total cost

\[
\begin{aligned}
Z={}&(5\times24)+(3\times18)+(3\times36)+(3\times13)\\
&+(1\times39)+(6\times15)+(3\times42)+(6\times19)\\
={}&120+54+108+39+39+90+126+114\\
={}&\mathbf{690\text{ cost units}}.
\end{aligned}
\]

The improvement over the VAM starting solution is:

\[
702-690=12\text{ cost units},\qquad \frac{12}{702}\times100\approx1.71\%.
\]

## 5. Final potentials and optimality test

For the final basis, one valid set of potentials is:

\[
u=[0,-5,-2,1],\qquad v=[24,41,18,18,17].
\]

Check that each occupied cell satisfies \(c_{ij}=u_i+v_j\). For non-basic cells, the reduced costs are:

| Cell | Calculation | Reduced cost |
|:--|:--|--:|
| S1–A2 | \(45-(0+41)\) | +4 |
| S1–A3 | \(37-(0+18)\) | +19 |
| S1–A5 | \(19-(0+17)\) | +2 |
| S2–A1 | \(28-(-5+24)\) | +9 |
| S2–A3 | \(37-(-5+18)\) | +24 |
| S2–A5 | \(23-(-5+17)\) | +11 |
| S3–A1 | \(45-(-2+24)\) | +23 |
| S3–A3 | \(31-(-2+18)\) | +15 |
| S3–A4 | \(42-(-2+18)\) | +26 |
| S4–A1 | \(26-(1+24)\) | +1 |
| S4–A4 | \(19-(1+18)\) | **0** |
| S4–A5 | \(18-(1+17)\) | **0** |

All listed non-basic reduced costs are non-negative. Therefore, the MODI optimality condition is satisfied and the minimum cost is **690 cost units**.

A zero reduced cost at a non-basic cell indicates that an alternative optimum **may** exist; it does not by itself prove that a distinct feasible alternative allocation exists. To claim alternate optima, construct the corresponding valid loop and verify that the resulting allocation is distinct and has the same cost.

## 6. Summary

| Metric | Initial VAM solution | Final MODI solution |
|:--|--:|--:|
| Total cost | 702 | **690** |
| Feasible | Yes | Yes |
| Row supply totals satisfied | Yes | Yes |
| Column demand totals satisfied | Yes | Yes |
| Basic cells required | 8 (including one \(\varepsilon\) cell due to degeneracy) | 8 (including any required zero basic cell) |
| Optimality | Not yet proven | Verified by non-negative reduced costs |

**Conclusion:** For the given cost matrix, supply, and demand, VAM provides a feasible starting cost of 702. MODI verifies an optimal transportation cost of **690**, an improvement of approximately **1.71%**.
