# Meetling
# Copyright (C) 2017 Meetling contributors
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

"""Core parts of Meetling."""

from datetime import datetime, timedelta

from micro import (Application, Object, Editable, Settings, Event, ValueError, InputError,
                   PermissionError)
from micro.jsonredis import JSONRedis, JSONRedisMapping
from micro.util import parse_isotime, randstr, str_or_none

class Meetling(Application):
    """See :ref:`Meetling`.

    .. attribute:: meetings

       Map of all :class:`Meeting` s.
    """

    def __init__(self, redis_url='', email='bot@localhost', smtp_url='',
                 render_email_auth_message=None):
        super().__init__(redis_url=redis_url, email=email, smtp_url=smtp_url,
                         render_email_auth_message=render_email_auth_message)
        self.types.update({'Meeting': Meeting, 'AgendaItem': AgendaItem})
        self.meetings = JSONRedisMapping(self.r, 'meetings')

    def do_update(self):
        db_version = self.r.get('version')

        # If fresh, initialize database
        if not db_version:
            self.r.set('version', 5)
            return

        db_version = int(db_version)
        r = JSONRedis(self.r.r)
        r.caching = False

        # Deprecated since 0.12.0
        if db_version < 5:
            users = r.omget(r.lrange('users', 0, -1))
            for user in users:
                user['email'] = None
            r.omset({u['id']: u for u in users})
            r.set('version', 5)

    def create_settings(self):
        return Settings(
            id='Settings', trashed=False, app=self, authors=[], title='My Meetling', icon=None,
            favicon=None, provider_name=None, provider_url=None, provider_description={},
            feedback_url=None, staff=[])

    def create_meeting(self, title, time=None, location=None, description=None):
        """See :http:post:`/api/meetings`."""
        if not self.user:
            raise PermissionError()

        e = InputError()
        if not str_or_none(title):
            e.errors['title'] = 'empty'
        e.trigger()

        meeting = Meeting(
            id='Meeting:' + randstr(), trashed=False, app=self, authors=[self.user.id], title=title,
            time=time.isoformat() + 'Z' if time else None, location=str_or_none(location),
            description=str_or_none(description))
        self.r.oset(meeting.id, meeting)
        self.r.rpush('meetings', meeting.id)

        self.activity.publish(Event.create('create-meeting', None, {'meeting': meeting}, app=self))
        return meeting

    def create_example_meeting(self):
        """See :http:post:`/api/create-example-meeting`."""
        if not self.user:
            raise PermissionError()

        time = (datetime.utcnow() + timedelta(days=7)).replace(hour=12, minute=0, second=0,
                                                               microsecond=0)
        meeting = self.create_meeting('Working group meeting', time, 'At the office',
                                      'We meet and discuss important issues.')
        meeting.create_agenda_item('Round of introductions')
        meeting.create_agenda_item('Lunch poll', duration=30,
                                   description='What will we have for lunch today?')
        meeting.create_agenda_item('Next meeting', duration=5,
                                   description='When and where will our next meeting be?')
        return meeting

class Meeting(Object, Editable):
    """See :ref:`Meeting`.

    .. attribute:: items

       Ordered map of :class:`AgendaItem` s on the meeting's agenda.

    .. attribute:: trashed_items

       Ordered map of trashed (deleted) :class:`AgendaItem` s.
    """

    def __init__(self, id, trashed, app, authors, title, time, location, description):
        super().__init__(id=id, trashed=trashed, app=app)
        Editable.__init__(self, authors=authors)
        self.title = title
        self.time = parse_isotime(time) if time else None
        self.location = location
        self.description = description

        self._items_key = self.id + '.items'
        self._trashed_items_key = self.id + '.trashed_items'
        self.items = JSONRedisMapping(self.app.r, self._items_key)
        self.trashed_items = JSONRedisMapping(self.app.r, self._trashed_items_key)

    def do_edit(self, **attrs):
        e = InputError()
        if 'title' in attrs and not str_or_none(attrs['title']):
            e.errors['title'] = 'empty'
        e.trigger()

        if 'title' in attrs:
            self.title = attrs['title']
        if 'time' in attrs:
            self.time = attrs['time']
        if 'location' in attrs:
            self.location = str_or_none(attrs['location'])
        if 'description' in attrs:
            self.description = str_or_none(attrs['description'])

    def create_agenda_item(self, title, duration=None, description=None):
        """See :http:post:`/api/meetings/(id)/items`."""
        if not self.app.user:
            raise PermissionError()

        e = InputError()
        if str_or_none(title) is None:
            e.errors['title'] = 'empty'
        if duration is not None and duration <= 0:
            e.errors['duration'] = 'not_positive'
        description = str_or_none(description)
        e.trigger()

        item = AgendaItem(
            id='AgendaItem:' + randstr(), trashed=False, app=self.app, authors=[self.app.user.id],
            title=title, duration=duration, description=description)
        self.app.r.oset(item.id, item)
        self.app.r.rpush(self._items_key, item.id)
        return item

    def trash_agenda_item(self, item):
        """See :http:post:`/api/meetings/(id)/trash-agenda-item`."""
        if not self.app.r.lrem(self._items_key, 1, item.id):
            raise ValueError('item_not_found')
        self.app.r.rpush(self._trashed_items_key, item.id)
        item.trashed = True
        self.app.r.oset(item.id, item)

    def restore_agenda_item(self, item):
        """See :http:post:`/api/meetings/(id)/restore-agenda-item`."""
        if not self.app.r.lrem(self._trashed_items_key, 1, item.id):
            raise ValueError('item_not_found')
        self.app.r.rpush(self._items_key, item.id)
        item.trashed = False
        self.app.r.oset(item.id, item)

    def move_agenda_item(self, item, to):
        """See :http:post:`/api/meetings/(id)/move-agenda-item`."""
        if to:
            if to.id not in self.items:
                raise ValueError('to_not_found')
            if to == item:
                # No op
                return
        if not self.app.r.lrem(self._items_key, 1, item.id):
            raise ValueError('item_not_found')
        if to:
            self.app.r.linsert(self._items_key, 'after', to.id, item.id)
        else:
            self.app.r.lpush(self._items_key, item.id)

    def json(self, restricted=False, include=False):
        """See :meth:`Object.json`.

        If *include_items* is ``True``, *items* and *trashed_items* are included.
        """
        json = super().json(restricted=restricted, include=include)
        json.update(Editable.json(self, restricted=restricted, include=include))
        json.update({
            'title': self.title,
            'time': self.time.isoformat() + 'Z' if self.time else None,
            'location': self.location,
            'description': self.description
        })
        if include:
            json['items'] = [i.json(restricted=restricted, include=include)
                             for i in self.items.values()]
            json['trashed_items'] = [i.json(restricted=restricted, include=include)
                                     for i in self.trashed_items.values()]
        return json

class AgendaItem(Object, Editable):
    """See :ref:`AgendaItem`."""

    def __init__(self, id, trashed, app, authors, title, duration, description):
        super().__init__(id=id, trashed=trashed, app=app)
        Editable.__init__(self, authors=authors)
        self.title = title
        self.duration = duration
        self.description = description

    def do_edit(self, **attrs):
        e = InputError()
        if 'title' in attrs and str_or_none(attrs['title']) is None:
            e.errors['title'] = 'empty'
        if attrs.get('duration') is not None and attrs['duration'] <= 0:
            e.errors['duration'] = 'not_positive'
        e.trigger()

        if 'title' in attrs:
            self.title = attrs['title']
        if 'duration' in attrs:
            self.duration = attrs['duration']
        if 'description' in attrs:
            self.description = str_or_none(attrs['description'])

    def json(self, restricted=False, include=False):
        json = super().json(restricted=restricted, include=include)
        json.update(Editable.json(self, restricted=restricted, include=include))
        json.update({
            'title': self.title,
            'duration': self.duration,
            'description': self.description
        })
        return json
