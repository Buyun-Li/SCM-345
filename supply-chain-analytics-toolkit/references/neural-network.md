# A simple feed-forward neural network in Excel

## Contents
1. The idea: every hop is a regression
2. Parts and names
3. Activation functions you can picture
4. The class network shape (and counting the numbers to fit)
5. The build, column by column
6. Solver set-up
7. Judging it, and what goes wrong
8. Worked example numbers

---

## 1. The idea

Last week's regression is one straight line from the factors to the outcome. A neural network uses the same factors, feeds them through **several small models**, bends some of their outputs into curves, and blends them. **Every hop from one layer to the next is a regression**: what changes is which inputs go in, what shape comes out, and what the weights are. More shapes on offer means more chance of catching the true relationship, whether it is one of the shapes or a blend of them.

Properties worth knowing:
- Inputs may be correlated with each other; the network does not need them to be separate.
- Inputs need not cause the outcome; a factor that merely moves with a real driver can still help prediction (and the fit may simply use it very little).
- Flexibility is the strength and the danger: more layers and neurons can memorize history. Judge on held-out data.

## 2. Parts and names

- **Neuron:** a small model: add up its inputs times weights, plus a constant (starting point), then apply an activation (shape).
- **Link / weight:** each arrow between neurons carries a weight (like a regression rate).
- **Constant:** each neuron's own starting point, exactly like the constant in a regression.
- **Layers:** input layer (the factors), hidden layers (the small models), output layer (the prediction).

One formula, for reference: `neuron output = activation( constant + SUM of weight x input )`

## 3. Activation functions

| Name | Shape in words | Excel (total in S6) |
|---|---|---|
| Linear | no bending: output = total | `=S6` |
| Softplus | flat near zero for negative totals, then climbs roughly straight (something that stays small until it starts, then grows) | `=LN(1+EXP(S6))` |
| Logistic | S curve between 0 and 1 (the curve from logistic regression) | `=1/(1+EXP(-S6))` |

A layer of only linear neurons cannot bend anything; it just re-mixes the inputs. Bending comes from softplus and logistic neurons.

## 4. The class network shape

```
input layer      4 factors, each rescaled (divided by a round number near its maximum)
hidden layer 1   2 neurons, linear                         4 x 2 = 8 weights + 2 constants
hidden layer 2   3 neurons: softplus, softplus, logistic   2 x 3 = 6 weights + 3 constants
output layer     1 neuron, linear                          3 x 1 = 3 weights + 1 constant
```
17 weights + 6 constants = **23 numbers** for Solver to find. Adjust counts for a different number of factors (inputs x neurons in the next layer, plus one constant per neuron).

Rescale inputs first (e.g., diesel / 6, tonnage / 140, rate / 7, hires / 120) so every input is roughly between 0 and 1; otherwise EXP() overflows and Solver struggles.

## 5. The build, column by column

Data: factors in B:E, rescaled copies in M:P, actual outcome in Z. Weights and constants in named yellow blocks: `W1_S1` (4 weights into signal 1), `C1_S1` (its constant), `W1_S2`, `C1_S2`, `W2_N1`..`W2_N3` (2 weights each), `C2_N1`..`C2_N3`, `W3` (3 output weights), `C3` (output constant). Group them as `L1_Block`, `L2_Block`, `L3_Block` for Solver.

Row 6 (first data row), then fill down:
```
Q  =SUMPRODUCT(M6:P6,W1_S1)+C1_S1        hidden layer 1, signal 1 (linear)
R  =SUMPRODUCT(M6:P6,W1_S2)+C1_S2        hidden layer 1, signal 2 (linear)
S  =SUMPRODUCT(Q6:R6,W2_N1)+C2_N1        total into neuron 1
T  =SUMPRODUCT(Q6:R6,W2_N2)+C2_N2        total into neuron 2
U  =SUMPRODUCT(Q6:R6,W2_N3)+C2_N3        total into neuron 3
V  =LN(1+EXP(S6))                        softplus 1
W  =LN(1+EXP(T6))                        softplus 2
X  =1/(1+EXP(-U6))                       logistic
Y  =SUMPRODUCT(V6:X6,W3)+C3              predicted outcome
AA =(Z6-Y6)^2                            squared miss
```
`Total_Squares =SUM(AA6:AA55)`. Also build the straight-line regression on the same data for comparison.

## 6. Solver set-up

- Set Objective `Total_Squares`, **Min**.
- By Changing `L1_Block, L2_Block, L3_Block` (all weights and constants).
- Constraints: `L1_Block >= -5`, `L1_Block <= 5`, `L2_Block >= -5`, `L2_Block <= 5`. Leave `L3_Block` free (the output weights carry the outcome's units and need room). The bounds keep every total inside EXP() small enough to evaluate.
- Options: tick **Use Automatic Scaling**; clear **Make Unconstrained Variables Non-Negative**.
- **GRG Nonlinear.** Expect 20-30 seconds.
- **Starting values: a spread of small numbers (e.g., between -1 and 1), never all zeros.** All-zero weights make every neuron identical and Solver stalls. Keep a copy of the starting block so you can paste it back and re-solve; try two or three different starts and keep the best total.

## 7. Judging it, and what goes wrong

- Compare `Total_Squares`, typical miss `=SQRT(Total_Squares/COUNT(...))` and R-squared `=1-Total_Squares/DEVSQ(actual)` with the straight line on the same data.
- Then judge on held-out rows: fit on most rows, compute the squared misses on rows the fit never saw. A network that beats the line in-sample but not out-of-sample has memorized.
- Two fits can reach the same total with completely different weights (the hidden signals can be rescaled and remixed). Compare totals, not weights.

| Symptom | Cause | Fix |
|---|---|---|
| Total stops far above expected | weights started at zero, or Solver stalled | paste the starting block back, solve again, try another start |
| `#NUM!` in softplus columns | a total inside EXP() grew huge (bounds deleted, inputs not rescaled) | restore bounds; rescale inputs |
| Logistic column wrong | sign typo: must be `EXP(-U6)` | fix the sign |
| Solver changes nothing | objective pointed at the wrong cell | check Set Objective |
| Great in-sample, bad held-out | overfitting | fewer neurons, more data, or stick with the line |

## 8. Worked example numbers

Lehigh Valley Fulfillment (50 orders; pick minutes vs order lines, weight, aisles crossed, pickers in the zone): straight line total squared miss 416.7 (typical miss 2.89 min, R-squared 0.915); the network 49.6 (typical miss 1.00 min, R-squared 0.990). Order size behaves like softplus (little effect until the order outgrows a hand basket) and congestion like an S curve (the second picker in an aisle costs real time, the seventh almost none), which is why the bending helps.
