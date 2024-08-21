# compute_real_interest

Reads a CSV file from Percent.com containing the transaction history for an
account. For each investment listed in the file, calculates the effective
(real) interest rate from the first investment to the earlier of (1) the date
the principal was paid off or (2) an "as-of" date supplied by the user, 
or if not supplied, the date the program is run. Also reports the mean interest rate for all investments, weighted by principal invested.

**Before downloading your transaction history, make sure you select all fields.** Go to the Percent.com / Portfolio / Transaction History page, click the two-white, one-purple icon to the right of the download icon, click on the checkbox to the left of "All Columns", and then click on the download icon).

## Key insight

$\text{total interest paid} = \text{rate} \cdot \int_t balance(t)$, where
    $balance(t)$ is the outstanding principal at time $t$. 
    
Therefore, $\text{effective rate} = (\text{total interest paid} - \text{fees}) / \int_t balance(t)$ .

## Assumptions

1. The file goes all the way back, *i.e.* each investment's initial deposit
        is listed in the file.
2. The file is current, *i.e.* no transactions have occurred since the last
        item listed in the file.
3. This version does not account for sale or purchase of an existing
        investment to/from another investor, a feature Percent.com says
        they're planning to implement.
4. The user wants to interpret any fee associated with an investment as
        a reduction in the effective interest rate paid.
5. Principal is only added to a given investment once (which is how
        Percent.com investments have worked so far).
6. A year = 365 days (not, *e.g.*, 360 days).
7. Unless interest was paid on the date the effective interest rate was computed, the program adds a note that tbe effective rate will increase when another interest payment is received. I could remove that flag by reporting effective rate as of the most recent interest payment, and that may be the rate you expect to see. That is, for a loan with a promised 10% rate, if all previous payments were at 10% and the next payment is not yet due, then the payor is paying 10% as promised. But you haven't yet received the interest accrued since that last payment (and in real life, maybe you never will), so you haven't received all 10% yet. Similarly, before the first interest payment, any investment will show an effective rate of 0%. But that's accurate _until you receive that first payment_.

## Sample output

**Input:** 

`python compute_real_interest.py Percent_History_2024_02_16.csv` # run on Feb. 19, 2024

**Output:**
```
Unhandled CSV file row(s):
{'Date': '2022-06-17', 'Transaction Type': 'Credit - Promotion', 'Description': 'Promotion', 'Amount': '150.00'}
{'Date': '2023-04-24', 'Transaction Type': 'Credit - Adjustment', 'Description': 'Other adjustment (credit)', 'Amount': '20.00'}

Summary of effective interest rate for each investment in this account:
=======================================================================
    Code      Initial P  Interest     Fees    Balance  Effective rate
=======================================================================
 CFI1 2023-2   $  2,550  $    160  $      0  $  1,973       15.3% *
 ESP1 2022-1   $    653  $     19  $      0  $      0       11.8%
 FTL1 2023-1   $    603  $     16  $      0  $      0       12.0%
 IDG1 2022-8   $    775  $     53  $      0  $     -0       11.0%
 PBN1 2023-1   $  5,000  $    645  $     71  $  5,000       10.9% *
 PBN6 2023-1   $  5,097  $    467  $     58  $  5,097       10.5% *
 PCT1 2022-1   $  2,000  $    225  $      0  $      0       14.9%
 RAP1 2022-6   $    500  $     12  $      0  $      0       13.8%
 TAP1 2022-5   $    500  $      5  $      0  $      0        9.0%
 TOR1 2022-5   $    500  $     14  $      0  $      0       11.3%
 TSM1 2023-1   $  1,000  $     40  $      0  $      0       16.0%
 TSM1 2023-3   $  1,000  $     53  $      0  $      0       15.8%
 WSF1 2022-2   $    500  $     50  $      0  $      0       15.0%
 WSF1 2022-3   $    535  $     59  $      0  $      0       15.0%
 WSF1 2023-4   $    764  $     93  $      0  $     -0       17.4%
 WSF1 2023-7   $  5,098  $    468  $      0  $  5,098       17.3% *
 WSF1 2023-9   $  2,666  $    152  $     15  $  2,666       14.1% *
=======================================================================
               $ 29,741  $  2,531  $    144  $ 19,834       13.6%

Mean effective rate 13.6% is weighted by initial principal.

* = effective rate will increase if interest is paid after 2024-02-19.
```
