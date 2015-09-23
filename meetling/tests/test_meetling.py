# Meetling
# Copyright (C) 2015 Meetling contributors
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <http://www.gnu.org/licenses/>.

# pylint: disable=missing-docstring

from redis import RedisError
from tornado.testing import AsyncTestCase
from meetling import Meetling, InputError

class MeetlingTestCase(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.app = Meetling(redis_url='15')
        self.app.r.flushdb()

class MeetlingTest(MeetlingTestCase):
    def test_init_redis_url_invalid(self):
        with self.assertRaises(InputError):
            Meetling(redis_url='//localhost:foo')

    def test_create_meeting(self):
        meeting = self.app.create_meeting('Cat Hangout', '  ')
        self.assertIn(meeting.id, self.app.meetings)
        # Whitespace-only strings should be converted to None
        self.assertIsNone(meeting.description)

    def test_create_meeting_title_empty(self):
        with self.assertRaises(InputError):
            self.app.create_meeting('  ')

    def test_create_meeting_no_redis(self):
        app = Meetling(redis_url='//localhoax')
        with self.assertRaises(RedisError):
            app.create_meeting('Cat Hangout')

    def test_create_example_meeting(self):
        meeting = self.app.create_example_meeting()
        self.assertTrue(len(meeting.items))

class MeetingTest(MeetlingTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.app.create_meeting('Cat Hangout')

    def test_edit(self):
        self.meeting.edit(description='Bring food!')
        self.assertEqual(self.meeting.description, 'Bring food!')

    def test_create_agenda_item(self):
        item = self.meeting.create_agenda_item('Purring')
        self.assertIn(item.id, self.meeting.items)

class AgendaItemTest(MeetlingTestCase):
    def test_edit(self):
        meeting = self.app.create_meeting('Cat Hangout')
        item = meeting.create_agenda_item('Purring')
        item.edit(description='Good mood!')
        self.assertEqual(item.description, 'Good mood!')
