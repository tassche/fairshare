# Fairshare - A small command line application to manage shared expenses.
# Copyright (C) 2013  Tijl Van Assche <tijlvanassche@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import datetime
import os.path
import sqlite3


database = 'fairshare.db'


class Error(Exception):
    '''Base class for exceptions in this module.'''
    pass


class ItemNotFoundError(Error):
    '''Exception raised if an item cannot be found in the database.'''
    pass


class ExpenseNotFoundError(ItemNotFoundError):
    '''Exception raised if an expense cannot be found in the database.'''
    pass


class UserNotFoundError(ItemNotFoundError):
    '''Exception raised if a user cannot be found in the database.'''
    pass


class IllegalInputError(Error):
    '''Exception raised for invalid input.'''
    def __init__(self, message):
        self.message = message


class IllegalUsernameError(IllegalInputError):
    '''Exception raised for an invalid username.'''
    pass


class IllegalExpenseCostError(IllegalInputError):
    '''Exception raised for an invalid expense cost.'''
    pass


class IllegalExpenseDateError(IllegalInputError):
    '''Exception raised for an invalid expense date.'''
    pass


class IllegalExpenseTitleError(IllegalInputError):
    '''Exception raised for an invalid expense title.'''
    pass


def create_database(database):
    '''Create the SQLite3 database.'''
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute(
        '''
        CREATE TABLE users (
            "u_id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "u_name" TEXT NOT NULL UNIQUE
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE expenses (
            "e_id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "e_cost" REAL NOT NULL,
            "e_title" TEXT,
            "e_date" TEXT,
            "e_payer" INTEGER NOT NULL,
            FOREIGN KEY(e_payer) REFERENCES users(u_id)
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE debts (
            "d_expense" INTEGER NOT NULL,
            "d_debtor" INTEGER NOT NULL,
            FOREIGN KEY(d_expense) REFERENCES expenses(e_id),
            FOREIGN KEY(d_debtor) REFERENCES users(u_id)
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE settles (
            "s_id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "s_date" TEXT NOT NULL
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE expenses_settled (
            "e_id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "e_cost" REAL NOT NULL,
            "e_title" TEXT,
            "e_date" TEXT,
            "e_payer" INTEGER NOT NULL,
            "e_settle" INTEGER NOT NULL,
            FOREIGN KEY(e_payer) REFERENCES users(u_id),
            FOREIGN KEY(e_settle) REFERENCES settles(s_id)
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE debts_settled (
            "d_expense" INTEGER NOT NULL,
            "d_debtor" INTEGER NOT NULL,
            FOREIGN KEY(d_expense) REFERENCES expenses_settled(e_id),
            FOREIGN KEY(d_debtor) REFERENCES users(u_id)
        )
        '''
    )
    connection.commit()
    connection.close()


def get_users_dict(cursor):
    '''Return a dictionary of u_id keys and u_name values.
    
    Arguments:
    cursor -- the SQLite3 cursor to use
    '''
    cursor.execute('SELECT u_id, u_name FROM users')
    users = dict()
    for u_id, u_name in cursor:
        users[u_id] = u_name
    return users


def get_users_list(cursor):
    '''Return a list of (u_id, u_name) tuples ordered by u_name.
    
    Arguments:
    cursor -- the SQLite3 cursor to use
    '''
    cursor.execute('SELECT u_id, u_name FROM users ORDER BY u_name')
    return [x for x in cursor]


def get_u_id(cursor, u_name):
    '''Return the u_id for a given u_name.

    Arguments:
    cursor -- the SQLite3 cursor to use
    u_name -- the user's u_name
    
    Raises:
    UserNotFoundError -- if no u_id was found in the database
    '''
    cursor.execute('SELECT u_id FROM users WHERE u_name=?', (u_name,))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        raise UserNotFoundError()


def get_u_name(cursor, u_id):
    '''Return the u_name for a given u_id.

    Arguments:
    cursor -- the SQLite3 cursor to use
    u_id -- the user's u_id

    Raises:
    UserNotFoundError -- if no u_name was found in the database
    '''
    cursor.execute('SELECT u_name FROM users WHERE u_id=?', (u_id,))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        raise UserNotFoundError()


def get_expense(cursor, e_id, u_name=False):
    '''Return an expense (dictionary) for a given e_id.

    The expense has the following keys: 
        id, date, title, payer, cost

    Arguments:
    cursor -- the SQLite3 cursor to use
    e_id -- the e_id of the expense

    Keyword Arguments:
    u_name -- if True the value for payer is a 'u_name' instead of a 'u_id' 

    Raises:
    ExpenseNotFoundError -- if e_id doens't exist
    '''
    cursor.execute('SELECT e_title, e_cost, e_date, e_payer FROM expenses '
                   'WHERE e_id=?', (e_id,))
    result = cursor.fetchone()
    try:
        expense = {'id': e_id, 'date': result[2], 'title': result[0], 
                   'payer': result[3], 'cost': result[1]}
    except TypeError:
        raise ExpenseNotFoundError()
    if u_name:
        expense['payer'] = get_u_name(cursor, expense['payer'])
    return expense


def get_expenses(cursor, u_name=False):
    '''Return a list of expenses (dictionaries).

    Each expense has the following keys: 
        id, date, title, payer, cost

    Arguments:
    cursor -- the SQLite3 cursor to use

    Keyword arguments:
    u_name -- if True the value for payer is a 'u_name' instead of a 'u_id' 
    '''
    cursor.execute('SELECT e_id, e_date, e_title, e_payer, e_cost '
                   'FROM expenses ORDER BY e_date')
    expenses = list()
    for x in cursor:
        expense = {'id': x[0], 'date': x[1], 'title': x[2], 'payer': x[3], 
                   'cost': x[4]}
        expenses.append(expense)
    if u_name:
        users = get_users_dict(cursor)
        for expense in expenses:
            expense['payer'] = users[expense['payer']]
    return expenses


def get_debtors(cursor, e_id, u_name=False):
    '''Return a list of debtors for a given e_id.

    Arguments:
    cursor -- the SQLite3 cursor to use
    e_id -- the e_id of the expense

    Keyword arguments:
    u_name -- if True the value for debtor is a 'u_name' instead of a 'u_id' 
    '''
    cursor.execute('SELECT d_debtor FROM debts WHERE d_expense=?', (e_id,))
    debtors = [debtor[0] for debtor in cursor]
    if u_name:
        users = get_users_dict(cursor)
        debtors = [users[debtor] for debtor in debtors]
    return debtors


def get_status_list(cursor):
    '''Return the current total debt per user as a list of tuples.
    
    The list does not contain users that have no open debts.

    Arguments:
    cursor -- the SQLite3 cursor to use

    Return format:
    [(this user must pay, this user, this amount), ...]
    '''
    status = list()
    users = get_users_dict(cursor)
    cashers = get_status_dict(cursor, users)
    for casher in users.values():
        for payer in users.values():
            if cashers[casher][payer] != 0:
                status.append((payer, casher, cashers[casher][payer]))
    return status


def get_status_dict(cursor, users):
    '''Return the current total debt for each user as a dictionary.

    Arguments:
    cursor -- the SQLite3 cursor to use
    users -- a dictionary of users (get_user_dict)

    Return format:
    {{user1: {user1: 'user1 must pay this amount to user1',
              user2: 'user2 must pay this amount to user1',
              ...
              }
      },
     {user2: {user1: 'user1 must pay this amount to user2',
              user2: 'user2 must pay this amount to user2',
              ...
              }
      },
     ...
     }
    '''
    cashers = dict()
    for casher_u_name in users.values():
        payers = dict()
        for payer_u_name in users.values():
            payers[payer_u_name] = 0
        cashers[casher_u_name] = payers
    for expense in get_expenses(cursor, u_name=True):
        debtors = get_debtors(cursor, expense['id'], u_name=True)
        share = expense['cost'] / len(debtors)
        for debtor in debtors:
            cashers[expense['payer']][debtor] += share
    for casher in users.values():
        for payer in users.values():
            c = abs(cashers[casher][payer] - cashers[payer][casher])
            if cashers[casher][payer] > cashers[payer][casher]:
                cashers[casher][payer] = c
                cashers[payer][casher] = 0
            elif cashers[casher][payer] == cashers[payer][casher]:
                cashers[casher][payer] = cashers[payer][casher] = 0
    return cashers


def validate_username(u_name):
    '''Validate a username and return it.
    
    Does not check if u_name already exists in the database.
    
    Arguments:
    u_name -- the username to validate

    Raises:
    IllegalUsernameError -- if u_name is not a valid username
    '''
    if u_name != u_name.strip():
        raise IllegalUsernameError('no leading or trailing whitespace allowed')
    if u_name == '' or u_name.isspace():
        raise IllegalUsernameError('cannot be empty or whitespace only')
    if ',' in u_name:
        raise IllegalUsernameError("no ',' allowed")
    try:
        int(u_name)
        raise IllegalUsernameError('cannot be a number')
    except ValueError:
        pass
    return u_name


def validate_user_id(cursor, u_id):
    '''Check if u_id exists in the database and return it.

    Arguments:
    cursor -- the SQLite3 cursor to use
    u_id -- the u_id to check
    
    Raises:
    UserNotFoundError -- if no u_name can be found for the given u_id
    '''
    get_u_name(cursor, u_id)
    return u_id


def validate_expense_id(cursor, e_id):
    '''Check if e_id exists in the database and return it.

    Arguments:
    cursor -- the SQLite3 cursor to use
    e_id -- the e_id to check
    
    Raises:
    ExpenseNotFoundError -- if e_id was not found in the database
    '''
    cursor.execute('SELECT e_id FROM expenses WHERE e_id=?', (e_id,))
    try:
        cursor.fetchone()[0]
    except TypeError:
        raise ExpenseNotFoundError()        
    return e_id


def validate_expense_cost(cost):
    '''Validate cost and return it (float).

    Arguments:
    cost -- the cost to validate
    
    Raises:
    IllegalExpenseCostError -- if cost can not be casted to float
    IllegalExpenseCostError -- if cost is not greater than 0
    '''
    try:
        cost = float(cost)
        if not cost > 0:
            raise IllegalExpenseCostError('cost must be a positive number')
    except (TypeError, ValueError):
        raise IllegalExpenseCostError('cost must be a number')
    return cost


def validate_expense_date(date):
    '''Validate date and return it (str).

    Arguments:
    date -- the date to validate

    Raises:
    IllegalExpenseDateError -- if date is not today or before
    IllegalExpenseDateError -- if date is not in YYYYMMDD format
    '''
    try:
        date_ = datetime.datetime.strptime(date, '%Y%m%d').date()
        if date_ > datetime.date.today():
            raise IllegalExpenseDateError('date must be today or before')
    except (TypeError, ValueError):
        raise IllegalExpenseDateError("date format should be 'YYYYMMDD'")
    return date


def validate_expense_title(title):
    '''Validate title and return it.

    Arguments:
    title -- the title to validate

    Raises:
    IllegalExpenseTitle -- if title is an empty string or only whitespace
    '''
    if title != title.strip():
        raise IllegalExpenseTitleError('no leading or trailing whitespace '
                                       'allowed')
    if title == '' or title.isspace():
        raise IllegalExpenseTitleError('cannot be empty or whitespace only')
    return title


def insert_user(cursor, u_name):
    '''Insert a new user into the database.

    The u_name is validated before the query is executed.

    Arguments:
    cursor -- the SQLite3 cursor to use
    u_name -- the new user's username
    
    Raises:
    IllegalUsernameError -- if u_name is not a valid username
    sqlite3.IntegrityError -- if the username already exists in the database
    '''
    u_name = validate_username(u_name)
    cursor.execute('INSERT INTO users (u_name) VALUES (?)', (u_name,))


def insert_expense(cursor, title, cost, date, payer, debtors):
    '''Insert a new expense into the database.

    All arguments are validated before any query is executed.

    Arguments:
    cursor -- the SQLite3 cursor to use
    title -- the new title
    cost -- the new cost
    date -- the new date
    payer -- u_id of the payer
    debtors -- list of u_id's of the debtors

    Raises:
    IllegalExpenseTitleError -- if title is not valid
    IllegalExpenseCostError -- if cost is not valid
    IllegalExpenseDateError -- if date is not valid
    UserNotFoundError -- if payer or one of debtors doesn't exist
    '''
    title = validate_expense_title(title)
    cost = validate_expense_cost(cost)
    date = validate_expense_date(date)
    payer = validate_user_id(cursor, payer)
    debtors = [validate_user_id(cursor, debtor) for debtor in debtors]
    cursor.execute('INSERT INTO expenses (e_cost, e_title, e_date, e_payer) '
                   'VALUES (?, ?, ?, ?)', (cost, title, date, payer))
    rowid = cursor.lastrowid
    for debtor in debtors:
        cursor.execute('INSERT INTO debts (d_expense, d_debtor) VALUES (?, ?)',
                       (rowid, debtor))


def update_user(cursor, old_u_name, new_u_name):
    '''Update a u_name in the database.
    
    Arguments:
    cursor -- the SQLite3 cursor to use
    old_u_name -- the u_name to update
    new_u_name -- the new u_name

    Raises:
    IllegalUsernameError -- if new_u_name is not a valid username
    UserNotFoundError -- if old_u_name doesn't exist in the database
    sqlite3.IntegrityError -- if new_u_name already exists in the database
    '''
    new_u_name = validate_username(new_u_name)
    cursor.execute('UPDATE users SET u_name=? WHERE u_name=?', 
                   (new_u_name, old_u_name))
    if cursor.rowcount == 0:
        raise UserNotFoundError()


def update_expense(cursor, e_id, title, cost, date, payer, debtors):
    '''Update an expense in the database.

    All arguments are validated before any query is executed.

    Arguments:
    cursor -- the SQLite3 cursor to use
    e_id -- the e_id of the expense to update
    title -- the new title
    cost -- the new cost
    date -- the new date
    payer -- u_id of the payer
    debtors -- list of u_id's of the debtors

    Raises:
    ExpenseNotFoundError -- if e_id doesn't exist
    IllegalExpenseCostError -- if cost is not valid
    IllegalExpenseDateError -- if date is not valid
    UserNotFoundError -- if payer or one of debtors doesn't exist
    '''
    e_id = validate_expense_id(cursor, e_id)
    title = validate_expense_title(title)
    cost = validate_expense_cost(cost)
    date = validate_expense_date(date)
    payer = validate_user_id(cursor, payer)
    debtors = [validate_user_id(cursor, debtor) for debtor in debtors]
    cursor.execute('UPDATE expenses SET e_title=?, e_cost=?, e_date=?, '
                   'e_payer=? WHERE e_id=?', (title, cost, date, payer, e_id))
    cursor.execute('DELETE FROM debts WHERE d_expense=?', (e_id,))
    for debtor in debtors:
        cursor.execute('INSERT INTO debts (d_expense, d_debtor) VALUES (?, ?)',
                       (e_id, debtor))


def settle_expenses(cursor):
    '''Settle all expenses.
    
    Arguments:
    cursor -- the SQLite3 cursor to use
    '''
    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    cursor.execute('INSERT INTO settles (s_date) VALUES (?)', (now,))
    s_id = cursor.lastrowid
    cursor.execute('SELECT e_id, e_cost, e_title, e_date, e_payer '
                   'FROM expenses')
    for e_id, e_cost, e_title, e_date, e_payer in [row for row in cursor]:
        cursor.execute(
            '''
            INSERT INTO expenses_settled
                (e_cost, e_title, e_date, e_payer, e_settle)
            VALUES
                (?, ?, ?, ?, ?)
            ''',
            (e_cost, e_title, e_date, e_payer, s_id)
        )
        new_e_id = cursor.lastrowid
        cursor.execute('SELECT d_debtor FROM debts WHERE d_expense=?', 
                       (e_id,))
        for d_debtor in [row for row in cursor]:
            cursor.execute(
                'INSERT INTO debts_settled (d_expense, d_debtor) '
                'VALUES (?, ?)',
                (new_e_id, d_debtor[0])
            )
        cursor.execute('DELETE FROM expenses WHERE e_id=?', (e_id,))
        cursor.execute('DELETE FROM debts WHERE d_expense=?', (e_id,))


def add_users(args):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    for name in args.usernames:
        try:
            insert_user(cursor, name.strip())
        except IllegalUsernameError as e:
            print("Error: illegal username '{}': {}".format(name, e.message))
        except sqlite3.IntegrityError:
            print('Error: user already exists:', name)
    connection.commit()
    connection.close()


def edit_user(args):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    old, new = args.username[0], args.new_username[0]
    try:
        update_user(cursor, old, new)
    except UserNotFoundError:
        print("Error: user '{}' doesn't exist".format(old))
    except IllegalUsernameError as e:
        print("Error: illegal username '{}': {}".format(new, e.message))
    except sqlite3.IntegrityError:
        print('Error: user already exists:', new)
    connection.commit()
    connection.close()


def list_users():
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    for u_id, u_name in get_users_list(cursor):
        print(u_name)
    connection.close()


def read_username(cursor, prompt):
    '''Read a u_name from stdin and return the corresponding u_id.

    Read input from stdin. Print an error message if the input does not equal
    an existing u_name in the database. Repeat until the input equals an 
    existing u_name in the database. Return the u_id for the u_name read from 
    stdin.

    Arguments:
    cursor -- the SQLite3 cursor for the u_id lookup
    prompt -- the prompt text
    '''
    user = input(prompt)
    try:
        user = get_u_id(cursor, user)
    except UserNotFoundError:
        print("Error: user '{}' doesn't exist".format(user))
        return read_username(cursor, prompt)
    return user


def read_usernames(cursor, prompt):
    '''Read u_name's from stdin and return the corresponding u_id's.
    
    Read a comma-separated list of values (usernames) from stdin. Each value 
    must be an existing u_name in the database. Print an error message for each
    value that doesn't. Repeat until all values are existing u_name's. Return a
    list of u_id's where each u_id corresponds to a u_name read from stdin.

    Arguments:
    cursor -- the SQLite3 cursor for the u_id lookups
    prompt -- the prompt text
    '''
    users = list()
    valid = False
    while not valid:
        errors = 0
        for user in [u.strip() for u in input(prompt).split(',')]:
            try:
                users.append(get_u_id(cursor, user))
            except UserNotFoundError:
                errors += 1
                print("Error: User '{}' doesn't exist.".format(user))
        valid = errors == 0
    return users


def read_expense_cost(prompt):
    '''Read a cost from stdin and return it (float).
    
    Prompt the user for input. Print an error message if the input is not a 
    valid expense cost. Repeat until the cost is valid.

    Arguments:
    prompt -- the prompt text
    '''
    try:
        cost = validate_expense_cost(input(prompt))
    except IllegalExpenseCostError as e:
        print('Error: illegal cost: {}'.format(e.message))
        return read_expense_cost(prompt)
    return cost


def read_expense_date(prompt):
    '''Read a date from stdin and return it (str).
    
    Prompt the user for input. Print an error message if the input is not a 
    valid expense date. Repeat until the date is valid.

    Arguments:
    prompt -- the prompt text
    '''
    try:
        date = validate_expense_date(input(prompt))
    except IllegalExpenseDateError as e:
        print('Error: illegal date: {}'.format(e.message))
        return read_expense_date(prompt)
    return date


def read_expense_title(prompt):
    '''Read a title from stdin and return it (str).

    Prompt the user for input. Print an error message if the input is not a 
    valid expense title. Repeat until the title is valid.

    Arguments:
    prompt -- the prompt text
    '''
    try:
        title = validate_expense_title(input(prompt).strip())
    except IllegalExpenseTitleError as e:
        print('Error: illegal title: {}'.format(e.message))
        return read_expense_title(prompt)
    return title


def add_expense():
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    title = read_expense_title('title: ')
    cost = read_expense_cost('cost: ')
    date = read_expense_date('date: ')
    payer = read_username(cursor, 'payer: ')
    debtors = read_usernames(cursor, 'debtors: ')
    insert_expense(cursor, title, cost, date, payer, debtors)
    connection.commit()
    connection.close()


def edit_expenses(args):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    for e_id in args.expenses:
        # Retrieve the current expense data.
        try:
            expense = get_expense(cursor, e_id, u_name=True)
            debtors = get_debtors(cursor, e_id, u_name=True)
        except ExpenseNotFoundError:
            print("Error: expense '{}' doesn't exist".format(e_id))
            continue
        # Print the current and read the new data.
        print(">>> Editing expense: {}".format(e_id))
        print('old title:', expense['title'])
        title = read_expense_title('new title: ')
        print('old cost:', expense['cost'])
        cost = read_expense_cost('new cost: ')
        print('old date:', expense['date'])
        date = read_expense_date('new date: ')
        print('old payer:', expense['payer'])
        payer = read_username(cursor, 'new payer: ')
        d = ''
        for debtor in debtors:
            d += '{}, '.format(debtor)
        print('old debtors:', d[:-2])
        debtors = read_usernames(cursor, 'new debtors: ')
        # Update the database.
        update_expense(cursor, e_id, title, cost, date, payer, debtors)
        connection.commit()
    connection.close()


def list_expenses():
    headings = {'id': 'ID', 'date': 'Date', 'title': 'Expense', 'payer': 
                'Payer', 'cost': 'Cost', 'debtors': 'Debtors',}
    header = '{id:3} {date:8} {title:15} {payer:10} {cost:6} {debtors:32}'
    entry = ('{id:3} {date:8} {title:15} {payer:10} {cost:6} {debtors:14} '
             '{share:5} >> {payer:8}')
    print(header.format(**headings))
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    for expense in get_expenses(cursor, u_name=True):
        debtors = get_debtors(cursor, expense['id'], u_name=True)
        share = expense['cost'] / len(debtors)
        debtors_ = ''
        for debtor in sorted(debtors):
            if not debtor == expense['payer']:
                debtors_ += '{}, '.format(debtor)
        debtors = debtors_[:-2]
        data = {
            'date': expense['date'], 'title': expense['title'], 'payer': 
            expense['payer'], 'cost': expense['cost'], 'debtors': debtors,
            'share': share, 'id': expense['id']
        }
        print(entry.format(**data))
    connection.close()


def list_settled_expenses():
    print('list settled expenses -- not yet implemented')


def status():
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    status = get_status_list(cursor)
    for payer, receiver, amount in status:
        print(payer, '>>', receiver, amount)
    connection.close()


def settle():
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    status = get_status_list(cursor)
    for payer, receiver, amount in status:
        print(payer, '>>', receiver, amount)
    if confirm('Settle?', default_y=False):
        settle_expenses(cursor)
        connection.commit()
    connection.close()


def confirm(prompt, default_y=True):
    '''Prompt the user for confirmation.
    
    Return True if the user confirms else False.
    
    Arguments:
    prompt -- the prompt text

    Keyword arguments:
    default_y -- empty input confirms (default True)
    
    Example:
    >>> confirm('Save?')
    Save? [Y/n]: 
    '''
    ans_y, ans_n = ('y', 'yes'), ('n', 'no')
    yn = 'Y/n' if default_y else 'y/N'
    ans = input('{} [{}]: '.format(prompt, yn))
    while ans.strip().lower() not in ('',) + ans_y + ans_n:
        ans = input('{} [{}]: '.format(prompt, yn))
    return ans in (('',) + ans_y if default_y else ans_y)


def parse_args():
    '''Parse the CLI arguments and run the program.'''
    parser = argparse.ArgumentParser(
        description='''
        Additional help for every command (the first positional argument) is 
        available by using the -h option.
        ''',
        epilog='Written by Tijl Van Assche'
    )
    subparser = parser.add_subparsers()

    ### fs add
    args = ('add',)
    kwargs = {'description': 'add a new expense',
              'help': 'add an expense',
              'aliases': ('a',),
              }
    p_add = subparser.add_parser(*args, **kwargs)
    p_add.set_defaults(func=add_expense)

    ### fs edit expense [expense ...]
    args = ('edit',)
    kwargs = {'description': 'edit an existing expense',
              'help': 'edit an expense',
              'aliases': ('e',),
              }
    p_edit = subparser.add_parser(*args, **kwargs)
    args = ('expenses',)
    kwargs = {'help': 'ID of the expense to edit',
              'nargs': '+',
              'metavar': 'expense',
              'type': int,
              }
    p_edit.add_argument(*args, **kwargs)
    p_edit.set_defaults(func=edit_expenses)

    ### fs history
    args = ('history',)
    kwargs = {'description': 'list all settled debts',
              'help': 'list settled expenses',
              'aliases': ('h',),
              }
    p_history = subparser.add_parser(*args, **kwargs)
    p_history.set_defaults(func=list_settled_expenses)

    ### fs list
    args = ('list',)
    kwargs = {'description': 'list all expenses',
              'help': 'list all expenses', 
              'aliases': ('l',),
              }
    p_list = subparser.add_parser(*args, **kwargs)
    p_list.set_defaults(func=list_expenses)

    ### fs settle
    args = ('settle',)
    kwargs = {'description': 'settle all debts',
              'help': 'settle debts', 
              'aliases': ('se',),
              }
    p_settle = subparser.add_parser(*args, **kwargs)
    p_settle.set_defaults(func=settle)

    ### fs status
    args = ('status',)
    kwargs = {'description': 'show the current debts',
              'help': 'show the status', 
              'aliases': ('s',),
              }
    p_status = subparser.add_parser(*args, **kwargs)
    p_status.set_defaults(func=status)

    ### fs users
    args = ('users',)
    kwargs = {'description': 'user management',
              'help': 'user management',
              'aliases': ('u',),
              }
    p_users = subparser.add_parser(*args, **kwargs)
    u_subparser = p_users.add_subparsers()

    ### fs users add username [username ...]
    args = ('add',)
    kwargs = {'description': 'create a new user',
              'help': 'create a new user',
              'aliases': ('a',),
              }
    p_u_add = u_subparser.add_parser(*args, **kwargs)
    args = ('usernames',)
    kwargs = {'help': 'the usernames to create',
              'nargs': '+',
              'metavar': 'username',
              }
    p_u_add.add_argument(*args, **kwargs)
    p_u_add.set_defaults(func=add_users)

    ### fs users rename username new_username
    args = ('rename',)
    kwargs = {'description': 'change username',
              'help': 'change a username',
              'aliases': ('r',),
              }
    p_u_rename = u_subparser.add_parser(*args, **kwargs)
    args = ('username',)
    kwargs = {'help': 'the username to rename',
              'nargs': 1,
              'metavar': 'username',
              }
    p_u_rename.add_argument(*args, **kwargs)
    args = ('new_username',)
    kwargs = {'help': 'the new username',
              'nargs': 1,
              'metavar': 'new_username',
              }
    p_u_rename.add_argument(*args, **kwargs)
    p_u_rename.set_defaults(func=edit_user)

    ### fs users list
    args = ('list',)
    kwargs = {'description': 'list all users',
              'help': 'list all users',
              'aliases': ('l',),
              }
    p_u_list = u_subparser.add_parser(*args, **kwargs)
    p_u_list.set_defaults(func=list_users)

    ### run command
    args = parser.parse_args()
    try:
        args.func(args)
    except TypeError:
        # Command takes no argument(s).
        args.func()
    except AttributeError as e:
        # No command specified.
        parser.print_help()


if __name__ == '__main__':
    if not os.path.isfile(database):
        create_database(database)
    parse_args()
