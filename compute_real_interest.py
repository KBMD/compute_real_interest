# -*- coding: utf-8 -*-
"""
Read a CSV file from Percent.com containing the transaction history for an
account, and for each investment listed in the file, calculate the effective
(real) interest rate from the first investment to the earlier of (1) the date
the principal was paid off or (2) today = the date this program is run.

**Key insight**
    total interest paid = rate × INTEGRAL OVER t { balance(t) }, where
    balance(t) is the outstanding principal at time t. Therefore,
    effective rate =
        {total interest paid less fees) / INTEGRAL OVER t {balance(t)} .

**ASSUMPTIONS**
    (1) the file goes all the way back, i.e. each investment's initial deposit
        is listed in the file
    (2) the file is current, i.e. no transactions have occurred since the last
        item listed in the file
    (3) this version does not account for sale or purchase of an existing
        investment to/from another investor, a feature Percent.com says
        they're planning to implement
    (4) the user wants to interpret any fee associated with an investment as
        a reduction in the effective interest rate paid.
    (5) the file has transactions listed in reverse chronological order, i.e.
        with the newest entries at the top of the file after a header row
    (6) principal is only added to a given investment once (which is how
        Percent.com investments have worked so far)
    (7) a year = 365 days
#TODO: check these assumptions in the program, or spit out a disclaimer

Created on Fri Feb  9 21:15:09 2024
Current version 16 Feb 2024

@author: kevin@theBlacks.us
Thanks to gpt.wustl.edu for help on Python classes
"""

import datetime
import csv, sys, os, re

# Global variables
DEBUG  = True
DEBUG2 = False

transactions = [] # an array into which all transactions in the CSV file ...
    # ... are read, one row per array entry
date_format = "%Y-%m-%d" # i.e., in CSV file, dates are written e.g. 2024-02-09
today = datetime.date.today()
as_of_date = today # show returns as of today, unless a different date is given
epsilon = 1E-6
show_depwd = False # List all deposits and withdrawals?
depwds = ('Withdrawal - ACH',  'Deposit - ACH', \
          'Withdrawal - Wire', 'Deposit - Wire')

ERROR_REINITIALIZE = 101
ERROR_REINITIALIZE_STRING = "ERROR: attempt to initialize a second "+\
      "investment with the same code."
ERROR_PARSE_ARGS = 102
ERROR_PARSE_ARGS = 1  # Note: don't need a code printed for this error
ERROR_PARSE_ARGS_STRING = \
    f"SYNTAX: {sys.argv[0]} path_and_filename.csv [2024-02-16]\n"+\
     "  e.g.: compute_real_interest.py .\Percent_History_2024-02-15.csv\n"+\
     "  NOTE: Optional 2nd argument = date as of which the return "+\
         "is calculated.\n"
ERROR_DATE_FORMAT = 103
ERROR_DATE_FORMAT_STRING = f"Expected date format is {date_format}"
ERROR_NO_FILE = 104
ERROR_NO_FILE_STRING = "File not found"

def close_enough(a, b, epsilon=1E-6):
    "Return true if a and b differ (absolutely) by less than epsilon."
    return (abs(a-b) < epsilon)  # type bool

class Investment:
    instances = {} # Class-level dictionary to store instances
        # Here, an instance is an object containing information about a
        # specific investment, e.g. with code "PBN6 2023-1".

    def __init__(self, code, p0, date, pt=0, interest=0, fees=0):
        """
        Data attributes:
            code = short string identifying investment, e.g. "PCT1 2022-1"
            p0 = initial principal invested (read in as a negative number,
                stored as positive number) (units: $)
            ptouched = date when principal was last changed
            itouched = date of last interest payment (or first deposit)
                Note: ?touched are of type <class 'datetime.date'>
            pt = principal × time on which interest has accrued"
                actually, it's the discrete equivalent of
                INTEGRAL OVER t { balance(t)}, where t = time
                NOTE: pt is in units $*years
            balance (units: $)
            interest = total interest paid to date (units: 1/year)
            fees = total fees paid to date (units: $)
        """

        # Check if object instance with matching code already exists
        if code in Investment.instances:
            # this investment was previously invested in
            print(f"Attempting to initialize investment with code {code}")
            error_exit(ERROR_REINITIALIZE_STRING, ERROR_REINITIALIZE)
        else:
            # Initialize the new instance ...
            p0 = float(p0)
            assert p0 < 0, "amount invested must be negative in the CSV file"
            assert close_enough(100*p0, int(100*p0)), \
                "amounts must be given as whole cents e.g. zyxw.vu or zyxw"
            self.code = code
            self.p0 = -p0  #WARNING: note additive inverse (see docstring)
            self.ptouched = date
            # Not sure if the next line is the right choice, but it seems
            # better than not initializing the "last interest payment" 
            # variable at all ...
            self.itouched = date
            self.pt = pt
            self.interest = interest
            self.fees = fees
            self.balance = self.p0
            # ... and (since we got here without triggering assertions above)
            # add the new instance to the instances dictionary:
            Investment.instances[code] = self
        if DEBUG2:
            print("This investment is: ")
            print(self)
            print("=========")

    @classmethod
    def get_instance(cls, code):
        """Checks to see if an investment exists (i.e. has already been seen
            while reading the .csv file). Returns the investment object if it
            exists; otherwise returns None.
        """
        if code in cls.instances:
            return cls.instances[code]
        else:
            return None

    def update_from_return_of_principal(self, date, returned):
        """
        Updates the investment (object) when some of the principal is repaid.

        Parameters
        ----------
        date : TYPE: date.date
            the date of the (possibly partial) return of principal.
        returned : TYPE: float (should be a 0- to 2-digit decimal)
            amount returned from this investment (object) in dollars.cents.

        Returns
        -------
        None.

        """
        assert returned >= 0, \
            "Principal returned must be given as a nonnegative number"
        assert date >= self.ptouched, \
            "Error, transactions must be ordered from oldest to newest"
        self.pt += ((date - self.ptouched).days/365)*self.balance
            # NOTE ptouched and balance in above line are the _old_ values
        self.ptouched = date
        self.balance -= returned

    def update_from_fee(self, fee):
        assert fee < 0, "Fees must be given as a negative number"
        self.fees -= fee

    def update_from_interest(self, interest_paid_here):
        self.interest += interest_paid_here

    def eff_rate(self, date):
        """
        Calculates the effective interest rate returned by the investment
        through the date supplied, taking into account fees and the timing
        of (partial) principal repayment(s).

        Parameters
        ----------
        date : TYPE datetime.date
            DESCRIPTION: The date at which the investment's
            effective return is evaluated

        Returns
        -------
        eff_rate : TYPE float
            DESCRIPTION: the effective rate computed for this
            investment through the date specified.

        """
        assert date >= self.ptouched, \
            "ERROR: date given is before a previously recorded balance change"
        current_pt = self.pt + ((date - self.ptouched).days/365)*self.balance
        return (self.interest - self.fees) / current_pt

    def __str__(self):
        return "Investment: "+\
            f"{self.code}, outstanding principal {self.balance:,.2f}, "+\
            f"balance changed {self.ptouched.strftime('%Y-%m-%d')}, "+\
            f"total interest and fees: {self.interest:,.2f}, {self.fees:,.2f}, "+\
            "\N{GREEK CAPITAL LETTER SIGMA} principal \N{MIDDLE DOT} "+\
                f"time = {self.pt:,.2f} ($\N{MIDDLE DOT}years)"

def read_transactions_csv_file(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        # Read each row as a dictionary
        for row in reader:
            transactions.append(row)  # for now, uses a global "transactions"
                #ASSUMES the whole CSV can be read into memory--probably fine
            # Access field names and values
            # for field, value in row.items():
            #    print(f"{field}: {value}")
    transactions.reverse()  # now transactions are in ascending order

def get_code_from_description(description):
    """
    defines code from the Description field of a row in the CSV file
    ASSUMES that the only thing in parentheses is the code.
    :param description: Description field from a row in the CSV file (string)
    :return: The code extracted from the description, string a la "WSF1 2023-9"
    """
    code = re.search(r'\((.*?)\)', description)
    if code:
        assert len(code.groups()) == 1, f"ERROR: >1 code in {description}"
        return code.group(1)
    else:
        return None

def process_transactions(transactions_array):
    other_rows = False # Have there been any unhandled CSV file rows?
    for i in range(len(transactions_array)):
        global as_of_date
        row = transactions_array[i]
        row_code = get_code_from_description(row['Description'])
        row_date = datetime.datetime.strptime(row['Date'], date_format).date()
        # Note row_date is of type <class 'datetime.datetime'>
        row_amt  = float(row['Amount'])
        row_type = row['Transaction Type']
        if row_date > as_of_date:
            if DEBUG:
                if row_code == None:
                    msg = f"DEBUG: Skip row {row_type}: {row_date} is "+ \
                          "after as-of date."
                else:
                    msg = f"DEBUG: Skip row {row_code}: {row_date} is "+ \
                          "after as-of date."
                print(msg)
            continue
        if   row_type == 'Investment':
            Investment(row_code, row_amt, row_date)
        elif row_type == 'Principal':
            this_investment = Investment.get_instance(row_code)
            this_investment.update_from_return_of_principal(row_date, row_amt)
        elif row_type == 'Interest':
            this_investment = Investment.get_instance(row_code)
            this_investment.update_from_interest(row_amt)
            this_investment.itouched = row_date
        elif row_type == 'Fee':
            this_investment = Investment.get_instance(row_code)
            this_investment.update_from_fee(row_amt)
        else:
            if show_depwd or row_type not in depwds: #  we want to print it
                if not other_rows:  # this is our first, so print a header
                    print("Unhandled CSV file row(s):")
                    other_rows = True
                print(row)

def error_exit(status_string, error_code=1):
    print(status_string)
    if error_code > 1:
        print("ERROR CODE =", error_code)
    sys.exit(error_code)

def print_header():
    print()
    print("Summary of effective interest rate for each investment in this account:")
    print("=======================================================================")
    print("    Code      Initial P  Interest     Fees    Balance  Effective rate")
    print("=======================================================================")

def print_footer(pr,inte,fee,bal,rate,anyflags):
    print("=======================================================================")
    print("            "+"   "+\
          f"${pr:>7,.0f}  ${inte:>7,.0f}  " +\
          f"${fee:>7,.0f}  ${bal:>7,.0f}"+\
          f"{rate:>12,.1%}")
    print()
    print(f"Mean effective rate {rate:.1%} is weighted by initial principal.")
    if anyflags:
        print()
        print(f"* = effective rate will increase if interest is paid after {as_of_date}.")
        # NOTE: I could remove that flag issue by reporting effective rate
        # as of the most recent interest payment, and usually that is what
        # is expected. That is, for a loan with a promised 10% rate, if 
        # all previous payments were at 10% and the next payment is not yet 
        # due, then the payor is paying 10% as promised. But you haven't yet 
        # received the interest accrued since that last payment (and in real
        # life, maybe you never will), so you haven't received all 10% yet.
        # E.g. before the first interest payment, any investment will show
        # an effective rate of 0%. But that's accurate _as of today_.

def main():
    global as_of_date
    if len(sys.argv) == 2 or len(sys.argv) == 3:
        transactions_csv_file_path = sys.argv[1]
        if not os.path.exists(transactions_csv_file_path):
            error_exit(ERROR_NO_FILE_STRING+f"; supplied: {sys.argv[1]}", \
                       ERROR_NO_FILE)
    if len(sys.argv) == 3:
        datestring = sys.argv[2]
        try:
            as_of_date = datetime.datetime.strptime(datestring, date_format).date()
        except ValueError:
            error_exit(ERROR_DATE_FORMAT_STRING+f"; supplied: {datestring}", \
                       ERROR_DATE_FORMAT)
    if not (len(sys.argv) == 2 or len(sys.argv) == 3):
        error_exit(ERROR_PARSE_ARGS_STRING, ERROR_PARSE_ARGS)
    read_transactions_csv_file(transactions_csv_file_path)
    process_transactions(transactions)
    #TODO: doesn't deal with a file with 0 investments, but who cares?
    totpr  = 0 # total principal invested across all investments
    totint = 0 # total interest over investments
    totfee = 0 # total fees over investments
    totbal = 0 # total outstanding principal over investments
    wt_rate_sum = 0 # sums (balance*effective_rate) over investments
    print_header()
    anyflags = False
    for instance in sorted(Investment.instances.keys()):
        inv =  Investment.instances[instance]
        # print a summary line for this investment "inv", and add its
        # information to the "total" variables
        totpr += inv.p0
        totbal += inv.balance
        totint += inv.interest
        totfee += inv.fees
        inv_rate = inv.eff_rate(as_of_date)
        wt_rate_sum += inv.p0 * inv_rate
        if inv.balance > 0.99 and inv.itouched < as_of_date:
            # Note, the line above justifies initializing itouched
            # to the date of the initial investment.
            rateflag = " *"; anyflags = True
        else:
            rateflag = ""
        print(f"{inv.code:>12}   " +\
              f"${inv.p0:>7,.0f}  ${inv.interest:>7,.0f}  " +\
              f"${inv.fees:>7,.0f}  ${inv.balance:>7,.0f}"+\
              f"{inv_rate:>12,.1%}" + rateflag)
    weighted_rate = wt_rate_sum/totpr
    print_footer(totpr, totint, totfee, totbal, weighted_rate, anyflags)

if __name__ == "__main__":
    main()
