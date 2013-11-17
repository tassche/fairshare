Fairshare
=========

A small command line utility to keep track of shared expenses.

Buy stuff together, pay each other back later. Fairshare lets you easily keep 
track of who has payed what and when, and who should repay who and how much.

Fairshare's written in Python 3 and uses a local SQLite database to store its 
data.


Setup
-----

Save the files `fairshare.py` and ` fairshare.sh` to the same directory, e.g. 
`$HOME/bin`. Use `./fairshare.sh` to run the application.

    $ cd ~/bin
    $ ./fairshare.sh --help

Note that you must `cd` to the directory where you saved the fairshare files 
for the program to run correctly. 

You can work around this limitation by adding the `cd` command to the shell 
script. For example, let's say you've saved the files in the directory 
`$HOME/bin/fairshare-bin`, then edit `fairshare.sh` as follows:

    #! /bin/bash
    cd $HOME/bin/fairshare-bin
    python3 fairshare.py "$@"

For more convenience you should add `$HOME/bin` to your PATH and create a 
symlink to `fairshare.sh`.

    $ ln -s $HOME/bin/fairshare-bin/fairshare.sh $HOME/bin/fairshare

Now you can run the program by executing the command `fairshare` from any
directory.

    $ fairshare --help


Usage
-----

    fairshare.sh [COMMAND] [-h]

**Commands**

    add (a)             add an expense
    edit (e)            edit an expense
    history (h)         list settled expenses
    list (l)            list all expenses
    settle (se)         settle debts
    status (s)          show the status
    users (u)           user management

**Optional Arguments**

    -h, --help          show this help message and exit


Additional help for every command is available with the `-h` flag, e.g. for 
the `users` command:

    $ ./fairshare.sh users -h
    usage: fairshare.py users [-h] {add,a,rename,r,list,l} ...
    
    user management
    
    positional arguments:
      {add,a,rename,r,list,l}
        add (a)             create a new user
        rename (r)          change a username
        list (l)            list all users
    
    optional arguments:
      -h, --help            show this help message and exit


Examples
--------

**Add some users**

We add Alice and Bob to the database.

    $ ./fairshare.sh users add alice bob

**List the users**

    $ ./fairshare.sh users list
    alice
    bob

**Add a new expense**

Alice went grocery shopping for Bob and herself. She adds the expense as 
follows:

    $ ./fairshare.sh add
    title: groceries
    cost: 42
    date: 20131117
    payer: alice
    debtors: alice, bob

**List the expenses**

The `list` command shows the current expenses in the database ordered by date.

    $ ./fairshare.sh list
    ID  Date     Expense         Payer      Cost   Debtors
      1 20131117 groceries       alice        42.0 bob            21.0 >> alice

**Show the status**

A quick overview of who has to pay who and how much is generated using the 
`status` command:

    $ ./fairshare.sh status
    bob >> alice 21.0

**Payback time**

Bob has just repayed Alice the 21.0 EUR he owed her. Use the `settle` command 
to reflect this in the database:

    $ ./fairshare.sh settle
    user2 >> user1 21.0
    Settle? [y/N]: y
    $ ./fairshare.sh status
    $ ./fairshare.sh list
    ID  Date     Expense         Payer      Cost   Debtors

