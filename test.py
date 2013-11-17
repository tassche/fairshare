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

import fairshare as fs
import os
import sqlite3
import unittest

class TestDatabase(unittest.TestCase):
    '''Base class for database related unit tests.
    
    Provides setUp and tearDown methods that create and destroy a database 
    for testing purposes.
    '''
    def setUp(self):
        self.db = 'fairsharetest.db'
        fs.create_database(self.db)
        self.connection = sqlite3.connect(self.db)
        self.cursor = self.connection.cursor()

    def tearDown(self):
        self.connection.close()
        os.remove(self.db)


class TestDatabaseUsers(TestDatabase):
    def test_get_users_dict(self):
        self.assertEqual(fs.get_users_dict(self.cursor), {})
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        users_expected = {1: 'user1', 2: 'user2'}
        self.assertEqual(fs.get_users_dict(self.cursor), users_expected)

    def test_get_users_list(self):
        self.assertEqual(fs.get_users_list(self.cursor), [])
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        users_expected = [(1, 'user1'), (2, 'user2')]
        self.assertEqual(fs.get_users_list(self.cursor), users_expected)

    def test_insert_user(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        users_expected = [(1, 'user1'), (2, 'user2')]
        self.assertEqual(fs.get_users_list(self.cursor), users_expected)

    def test_insert_user_twice(self):
        '''insert_user should raise an exception if u_name already exists'''
        fs.insert_user(self.cursor, 'user1')
        self.assertRaises(sqlite3.IntegrityError, fs.insert_user, 
                          self.cursor, 'user1')

    def test_update_user(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        users_expected = [(1, 'user1'), (2, 'user2')]
        self.assertEqual(fs.get_users_list(self.cursor), users_expected)
        fs.update_user(self.cursor, 'user2', 'user3')
        users_expected = [(1, 'user1'), (2, 'user3')]
        self.assertEqual(fs.get_users_list(self.cursor), users_expected)

    def test_update_user_that_does_not_exist(self):
        self.assertRaises(fs.UserNotFoundError, fs.update_user, self.cursor, 
                          'unknown user', 'new name')

    def test_get_u_id(self):
        fs.insert_user(self.cursor, 'user1')
        self.connection.commit()
        self.assertEqual(fs.get_u_id(self.cursor, 'user1'), 1)

    def test_get_u_id_for_u_name_that_does_not_exist(self):
        values = ('user1', '', ' ', 1)
        for x in values:
            self.assertRaises(fs.UserNotFoundError, fs.get_u_id,
                              self.cursor, x)

    def test_get_u_name(self):
        fs.insert_user(self.cursor, 'user1')
        self.connection.commit()
        self.assertEqual(fs.get_u_name(self.cursor, 1), 'user1')

    def test_get_u_name_for_u_id_that_does_not_exist(self):
        values = (1, '', ' ', 'user1')
        for x in values:
            self.assertRaises(fs.UserNotFoundError, fs.get_u_name,
                              self.cursor, x)


class TestDatabaseExpenses(TestDatabase):
    def test_get_expense(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test2', 30, '20130102', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test3', 40, '20130103', 2, (1, 2))
        self.connection.commit()
        expected_exp = (
            {'id': 1, 'date': '20130101', 'title': 'test1', 'payer': 1, 
             'cost': 20},
            {'id': 2, 'date': '20130102', 'title': 'test2', 'payer': 1, 
             'cost': 30},
            {'id': 3, 'date': '20130103', 'title': 'test3', 'payer': 2, 
             'cost': 40},
        )
        for i in range(len(expected_exp)):
            self.assertEqual(fs.get_expense(self.cursor, i+1), expected_exp[i])

    def test_get_expense_that_does_not_exist(self):
        values = (1, 'a', '')
        for x in values:
            self.assertRaises(fs.ExpenseNotFoundError, fs.get_expense,
                              self.cursor, 1)

    def test_get_expenses(self):
        self.assertEqual(fs.get_expenses(self.cursor), [])
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test2', 30, '20130102', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test3', 40, '20130103', 2, (1, 2))
        self.connection.commit()
        expected_result = [
            {'id': 1, 'date': '20130101', 'title': 'test1', 'payer': 1, 
             'cost': 20},
            {'id': 2, 'date': '20130102', 'title': 'test2', 'payer': 1, 
             'cost': 30},
            {'id': 3, 'date': '20130103', 'title': 'test3', 'payer': 2, 
             'cost': 40},
        ]
        self.assertEqual(fs.get_expenses(self.cursor), expected_result)

    def test_get_debtors(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test2', 30, '20130102', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test3', 40, '20130103', 2, (1, 2))
        self.connection.commit()
        expected_deb = ([1, 2], [1, 2], [1, 2])
        for i in range(len(expected_deb)):
            self.assertEqual(fs.get_debtors(self.cursor, i+1), expected_deb[i])

    def test_get_debtors_for_expense_that_does_not_exist(self):
        '''get_debtors should return an empty list if e_id doesn't exist'''
        values = (1, 'a', '')
        for x in values:
            self.assertEqual(fs.get_debtors(self.cursor, x), [])

    def test_get_status_list(self):
        self.assertEqual(fs.get_status_list(self.cursor), [])
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        fs.insert_expense(self.cursor, 'test', 20, '20130101', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test', 30, '20130101', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test', 40, '20130101', 2, (1, 2))
        self.connection.commit()
        expected_status =  [('user2', 'user1', 5)]
        self.assertEqual(fs.get_status_list(self.cursor), expected_status)
        fs.insert_expense(self.cursor, 'test', 40, '20130101', 2, (1, 2))
        fs.insert_expense(self.cursor, 'test', 40, '20130101', 2, (1, 2))
        fs.insert_expense(self.cursor, 'test', 5, '20130101', 1, (1, 2))
        self.connection.commit()
        expected_status =  [('user1', 'user2', 32.5)]
        self.assertEqual(fs.get_status_list(self.cursor), expected_status)
        fs.insert_user(self.cursor, 'user3')
        fs.insert_expense(self.cursor, 'test', 105, '20130101', 3, (1, 2))
        fs.insert_expense(self.cursor, 'test', 210, '20130101', 3, (1, 2, 3))
        self.connection.commit()
        expected_status =  [
            ('user1', 'user2', 32.5),
            ('user1', 'user3', 122.5),
            ('user2', 'user3', 122.5),
        ]
        self.assertEqual(fs.get_status_list(self.cursor), expected_status)

    def test_get_status_dict(self):
        users = fs.get_users_dict(self.cursor)
        self.assertEqual(fs.get_status_dict(self.cursor, users), {})
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        fs.insert_user(self.cursor, 'user3')
        fs.insert_expense(self.cursor, 'test', 20, '20130101', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test', 30, '20130101', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test', 40, '20130101', 2, (1, 2))
        fs.insert_expense(self.cursor, 'test', 40, '20130101', 2, (1, 2))
        fs.insert_expense(self.cursor, 'test', 40, '20130101', 2, (1, 2))
        fs.insert_expense(self.cursor, 'test', 5, '20130101', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test', 105, '20130101', 3, (1, 2))
        fs.insert_expense(self.cursor, 'test', 210, '20130101', 3, (1, 2, 3))
        self.connection.commit()
        expected_status = {
            'user1': {'user1': 0, 'user2': 0, 'user3': 0},
            'user2': {'user1': 32.5, 'user2': 0, 'user3': 0},
            'user3': {'user1': 122.5, 'user2': 122.5, 'user3': 0},
        }
        users = fs.get_users_dict(self.cursor)
        self.assertEqual(fs.get_status_dict(self.cursor, users), 
                         expected_status)

    def test_insert_expense(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test2', 30, '20130102', 1, (1, 2))
        fs.insert_expense(self.cursor, 'test3', 40, '20130103', 2, (1, 2))
        self.connection.commit()
        expected_exp = (
            {'id': 1, 'date': '20130101', 'title': 'test1', 'payer': 1, 
             'cost': 20},
            {'id': 2, 'date': '20130102', 'title': 'test2', 'payer': 1, 
             'cost': 30},
            {'id': 3, 'date': '20130103', 'title': 'test3', 'payer': 2, 
             'cost': 40},
        )
        expected_deb = ([1, 2], [1, 2], [1, 2])
        for i in range(len(expected_exp)):
            self.assertEqual(fs.get_expense(self.cursor, i+1), expected_exp[i])
            self.assertEqual(fs.get_debtors(self.cursor, i+1), expected_deb[i])
                         
    def test_insert_expense_with_invalid_title(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        values = (' title ', ' title', '', ' ')
        for x in values:
            self.assertRaises(fs.IllegalExpenseTitleError, fs.insert_expense, 
                              self.cursor, x, 20, '20130101', 1, (1, 2))
        self.connection.commit()

    def test_insert_expense_with_invalid_cost(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        values = (-30, '-30', 0, '0', '', ' ', '-.2')
        for x in values:
            self.assertRaises(fs.IllegalExpenseCostError, fs.insert_expense, 
                              self.cursor, 'test', x, '20130101', 1, (1, 2))
        self.connection.commit()

    def test_insert_expense_with_invalid_date(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        values = ('20130229', 'jfjfjf', '130101', '', ' ')
        for x in values:
            self.assertRaises(fs.IllegalExpenseDateError, fs.insert_expense, 
                              self.cursor, 'test', 20, x, 1, (1, 2))
        self.connection.commit()

    def test_insert_expense_with_unknown_payer(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        values = (3, 4, 9000, 'a', '')
        for x in values:
            self.assertRaises(fs.UserNotFoundError, fs.insert_expense, 
                              self.cursor, 'test', 20, '20130101', x, (1, 2))
        self.connection.commit()

    def test_insert_expense_with_unknown_debtor(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        values = (3, 4, 9000, 'a', '')
        for x in values:
            self.assertRaises(fs.UserNotFoundError, fs.insert_expense, 
                              self.cursor, 'test', 20, '20130101', 1, (1, x))
        self.connection.commit()

    def test_update_expense(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        self.connection.commit()
        fs.update_expense(self.cursor, 1, 'edit1', 30, '20130102', 2, (1,))
        expected_expense = {'id': 1, 'title': 'edit1', 'cost': 30, 
                            'date': '20130102', 'payer': 2}
        expected_debtors = [1,]
        self.assertEqual(fs.get_expense(self.cursor, 1), expected_expense)
        self.assertEqual(fs.get_debtors(self.cursor, 1), expected_debtors)

    def test_update_expense_that_does_not_exist(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        self.connection.commit()
        values = (1, 2, '', ' ', 'a')
        for x in values:
            self.assertRaises(fs.ExpenseNotFoundError, fs.update_expense, 
                              self.cursor, x, 'edit', 30, '20130102', 2, (1,))

    def test_update_expense_with_invalid_title(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        self.connection.commit()
        values = (' title ', ' title', '', ' ')
        for x in values:
            self.assertRaises(fs.IllegalExpenseTitleError, fs.update_expense, 
                              self.cursor, 1, x, 20, '20130101', 2, (1, 2))
        self.connection.commit()

    def test_update_expense_with_invalid_cost(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        self.connection.commit()
        values = (-30, '-30', 0, '0', '', ' ', '-.2')
        for x in values:
            self.assertRaises(fs.IllegalExpenseCostError, fs.update_expense, 
                              self.cursor, 1, 'edit', x, '20130102', 2, (1, 2))
        self.connection.commit()

    def test_update_expense_with_invalid_date(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        self.connection.commit()
        values = ('20130229', 'jfjfjf', '130101', '', ' ')
        for x in values:
            self.assertRaises(fs.IllegalExpenseDateError, fs.update_expense, 
                              self.cursor, 1, 'edit', 20, x, 2, (1, 2))
        self.connection.commit()

    def test_update_expense_with_unknown_payer(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        self.connection.commit()
        values = (3, 4, 9000, 'a', '')
        for x in values:
            self.assertRaises(fs.UserNotFoundError, fs.update_expense, 
                              self.cursor, 1, 'edit', 20, '20130101', x, (2,))
        self.connection.commit()

    def test_update_expense_with_unknown_debtor(self):
        fs.insert_user(self.cursor, 'user1')
        fs.insert_user(self.cursor, 'user2')
        fs.insert_expense(self.cursor, 'test1', 20, '20130101', 1, (1, 2))
        self.connection.commit()
        values = (3, 4, 9000, 'a', '')
        for x in values:
            self.assertRaises(fs.UserNotFoundError, fs.update_expense, 
                              self.cursor, 1, 'edit', 20, '20130101', 1, (x,))
        self.connection.commit()

    def test_settle_expenses(self):
        '''not yet implemented'''
        pass


class TestValidateUsername(unittest.TestCase):
    def test_username_known_values(self):
        values = ('abcde', 'a49763', 'Aaa', 'a a', 'aa bbb', 'a b cc')
        for username in values:
            fs.validate_username(username)

    def test_username_is_a_number(self):
        values = ('0', '12', '-5')
        for username in values:
            self.assertRaises(fs.IllegalUsernameError,
                              fs.validate_username, username)

    def test_username_is_empty_or_whitespace(self):
        values = ('', ' ', '  ', '   ')
        for username in values:
            self.assertRaises(fs.IllegalUsernameError,
                              fs.validate_username, username)

    def test_username_contains_a_comma(self):
        values = (',', 'aa,bb', 'a, b')
        for username in values:
            self.assertRaises(fs.IllegalUsernameError,
                              fs.validate_username, username)

    def test_username_has_leading_or_trailing_whitespace(self):
        values = (' a', 'a ', ' a ', ' a a ')
        for username in values:
            self.assertRaises(fs.IllegalUsernameError,
                              fs.validate_username, username)


class TestValidateExpenseCost(unittest.TestCase):
    def test_cost_known_values(self):
        values = ('10', '10.22', '108', '186.34', '71.33', '0.24', '0.25')
        for cost in values:
            fs.validate_expense_cost(cost)

    def test_cost_is_negative_or_zero(self):
        values = ('0', '0.0', '-10', '-2.0')
        for cost in values:
            self.assertRaises(fs.IllegalExpenseCostError,
                              fs.validate_expense_cost, cost)

    def test_cost_is_not_a_number(self):
        values = ('', ' ', 'a', 'a-10', '2.0b', 'sin(x)', '2*2')
        for cost in values:
            self.assertRaises(fs.IllegalExpenseCostError,
                              fs.validate_expense_cost, cost)


class TestValidateExpenseDate(unittest.TestCase):
    def test_date_known_values(self):
        values = ('20131114', '20021231', '19740331', '20130228', '20120229')
        for date in values:
            fs.validate_expense_date(date)

    def test_date_is_in_the_future(self):
        values = ('21130101', '21131106')
        for date in values:
            self.assertRaises(fs.IllegalExpenseDateError, 
                              fs.validate_expense_date, date)

    def test_date_is_not_a_valid_date(self):
        values = ('20130229', '20130431', '20130230', '', ' ', 'jkl', '0101')
        for date in values:
            self.assertRaises(fs.IllegalExpenseDateError, 
                              fs.validate_expense_date, date)


class TestValidateExpenseTitle(unittest.TestCase):
    def test_title_known_values(self):
        values = ('aaa', 'a b', 'Aa Bb', 'abcde')
        for title in values:
            fs.validate_expense_title(title)

    def test_title_is_empty_or_whitespace(self):
        values = ('', ' ', '  ', '   ')
        for title in values:
            self.assertRaises(fs.IllegalExpenseTitleError, 
                              fs.validate_expense_title, title)

    def test_title_has_leading_or_trailing_whitespace(self):
        values = (' a', 'a ', ' a ', ' a a ')
        for title in values:
            self.assertRaises(fs.IllegalExpenseTitleError, 
                              fs.validate_expense_title, title)


if __name__ == '__main__':
    unittest.main()
