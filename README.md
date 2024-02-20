# compute_real_interest

Reads a transaction history CSV file from Percent.com and for each investment in the file, reports the effective (real) interest rate.

Read a CSV file from Percent.com containing the transaction history for an
account, and for each investment listed in the file, calculate the effective
(real) interest rate from the first investment to the earlier of (1) the date
the principal was paid off or (2) today = the date this program is run.

**Key insight**

$\text{total interest paid} = \text{rate} \cdot \int_t balance(t)$, where
    $balance(t)$ is the outstanding principal at time $t$. 
    
Therefore, $\text{effective rate} = (\text{total interest paid} - \text{fees}) / \int_t balance(t)$ .

**Assumptions**

1. The file goes all the way back, i.e. each investment's initial deposit
        is listed in the file.
2. The file is current, i.e. no transactions have occurred since the last
        item listed in the file.
3. This version does not account for sale or purchase of an existing
        investment to/from another investor, a feature Percent.com says
        they're planning to implement.
4. The user wants to interpret any fee associated with an investment as
        a reduction in the effective interest rate paid.
5. The file has transactions listed in reverse chronological order, i.e.
        with the newest entries at the top of the file after a header row.
6. Principal is only added to a given investment once (which is how
        Percent.com investments have worked so far).
7. A year = 365 days (not, *e.g.*, 360 days).
