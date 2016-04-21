Web API
=======

Introduction
------------

Meetling provides a JSON REST API.

Arguments are passed to an endpoint simply as JSON object and the result is returned as JSON value.
*Objects* contain a ``__type__`` attribute that holds the name of the object type.

If a requested endpoint doesn't exist, a :ref:`NotFoundError` is returned. For any endpoint, an
:ref:`InputError` is returned if the input contains invalid arguments.

Authentication and Permissions
------------------------------

To make an API request authenticated as some user, include a cookie named ``auth_secret`` with the
:ref:`User` 's *auth_secret*.

If user authentication with the given secret fails, an :ref:`AuthenticationError` is returned. For
any endpoint, a :ref:`PermissionError` is returned if the current user is not allowed to perform the
action.

.. _Meetling:

Meetling
--------

Meetling application.

.. http:post:: /api/login

   ``{"code": null}``

   Log in an :ref:`User` (device) and return them.

   If *code* is given, log in an existing user with the login *code*. If the login fails, a
   :exc:`ValueError` (``code_invalid``) is returned.

   If *code* is ``null``, create and log in a new user. The very first user who logs in is
   registered as staff member.

.. http:post:: /api/meetings

   ``{"title", "time": null, "location": null, "description": null}``

   Create a :ref:`Meeting` and return it.

   Permission: Authenticated users.

.. http:post:: /api/create-example-meeting

   Create a :ref:`Meeting` with an example agenda and return it.

   Useful to illustrate how meetings work.

   Permission: Authenticated users.

.. _Object:

Object
------

Object in the Meetling universe.

.. attribute:: id

   Unique ID of the object.

.. attribute:: trashed

   Indicates if the object has been trashed (deleted).

.. _Editable:

Editable
--------

:ref:`Object` that can be edited.

The URL that uniquely identifies an object is referred to as *object-url*, e.g. ``meetings/abc`` for
a :ref:`Meeting` with the *id* ``abc``.

.. describe:: authors

   :ref:`User` s who edited the object.

.. http:post:: /api/(object-url)

   ``{attrs...}``

   Edit the attributes given by *attrs* and return the updated object.

   A *trashed* (deleted) object cannot be edited. In this case a :ref:`ValueError`
   (`object_trashed`) is returned.

   Permission: Authenticated users.

.. _User:

User
----

Meetling user.

User is an :ref:`Object` and :ref:`Editable` by the user oneself.

.. describe:: name

   Name or nick name.

.. describe:: auth_secret

   Secret for authentication. Visible only to the user oneself.

.. http:get:: /api/users/(id)

   Get the user given by *id*.

.. _Settings:

Settings
--------

App settings.

Settings is an :ref:`Object` and :ref:`Editable` by staff members.

.. describe:: title

   Site title.

.. describe:: icon

   URL of the site icon. May be ``null``.

.. describe:: favicon

   URL of the site icon optimized for a small size. May be ``null``.

.. describe:: staff

   Staff users.

.. http:get:: /api/settings

   Get the settings.

.. _Meeting:

Meeting
-------

Meeting.

Meeting is an :ref:`Object` and :ref:`Editable`.

.. describe:: title

   Title of the meeting.

.. describe:: time

   Date and time the meeting begins. May be ``null``.

.. describe:: location

   Location where the meeting takes place. May be ``null``.

.. describe:: description

   Description of the meeting. May be ``null``.

.. http:get:: /api/meetings/(id)

   Get the meeting given by *id*.

.. http:get:: /api/meetings/(id)/items

   Get the list of :ref:`AgendaItem` s on the meeting's agenda.

   If ``/trashed`` is appended to the URL, only trashed (deleted) items are returned.

.. http:post:: /api/meetings/(id)/items

   ``{"title", "duration": null, "description": null}``

   Create an :ref:`AgendaItem` and return it.

   Permission: Authenticated users.

.. http:post:: /api/meetings/(id)/trash-agenda-item

   ``{"item_id"}``

   Trash (delete) the :ref:`AgendaItem` with *item_id*.

   If there is no item with *item_id* for the meeting, a :ref:`ValueError` (``item_not_found``) is
   returned.

   Permission: Authenticated users.

.. http:post:: /api/meetings/(id)/restore-agenda-item

   ``{"item_id"}``

   Restore the previously trashed (deleted) :ref:`AgendaItem` with *item_id*.

   If there is no trashed item with *item_id* for the meeting, a :ref:`ValueError`
   (``item_not_found``) is returned.

   Permission: Authenticated users.

.. http:post:: /api/meetings/(id)/move-agenda-item

   ``{"item_id", "to_id"}``

   Move the :ref:`AgendaItem` with *item_id* to the position directly after the item with *to_id*.

   If *to_id* is ``null``, move the item to the top of the agenda.

   If there is no item with *item_id* or *to_id* for the meeting, a :ref:`ValueError`
   (``item_not_found`` or ``to_not_found``) is returned.

   Permission: Authenticated users.

.. _AgendaItem:

AgendaItem
----------

Item on a :ref:`Meeting` 's agenda.

AgendaItem is an :ref:`Object` and :ref:`Editable`.

.. describe:: title

   Title of the item.

.. describe:: duration

   Time the agenda item takes in minutes. May be ``null``.

.. describe:: description

   Description of the item. May be ``null``.

.. http:get:: /api/meetings/(meeting-id)/items/(item-id)

   Get the item given by *item-id*.

.. _ValueError:

ValueError
----------

Returned for value-related errors.

.. attribute:: code

   Error string providing more information about the problem.

.. _InputError:

InputError
----------

Returned if the input to an endpoint contains one or more arguments with an invalid value.

InputError is a :ref:`ValueError` with *code* set to ``input_invalid``.

.. attribute:: errors

   Map of argument names / error strings for every problematic argument of the input.

.. _NotFoundError:

NotFoundError
-------------

Returned if a requested endpoint does not exist.

.. _AuthenticationError:

AuthenticationError
-------------------

Returned if user authentication fails.

.. _PermissionError:

PermissionError
---------------

Returned if the current user is not allowed to perform an action.