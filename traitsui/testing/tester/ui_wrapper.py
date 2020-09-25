#  Copyright (c) 2005-2020, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
""" Define the top-level object which is responsible for dispatching testing
functionality for a given GUI object. The functionality is exposed via
``UITester``, which is a TraitsUI specific tester.
"""

from contextlib import contextmanager
import textwrap

from traitsui.testing._exception_handling import (
    reraise_exceptions as _reraise_exceptions,
)
from traitsui.testing._gui import (
    process_cascade_events as _process_cascade_events,
)
from traitsui.testing.tester import locator
from traitsui.testing.tester.exceptions import (
    InteractionNotSupported,
    LocationNotSupported,
)


class UIWrapper:
    """
    An ``UIWrapper`` has the following responsibilities:

    (1) Wraps a UI target.
    (2) Search for a nested UI target within the wrapped UI target.
    (3) Perform user interaction on the UI target, e.g. mouse click.

    A UI target is an object which can be searched for nested UI targets,
    either as intermediate things (like editors or a table widget), or as a
    leaf widget which can be operated upon (e.g. a mouse click).

    For example, a ``UIWrapper`` may wrap an instance of traitsui.ui.UI in
    which more UI targets can be located. A ``UIWrapper`` may also wrap a
    leaf widget on which user interactions can be performed.

    For locating a nested UI target, the ``locate`` method is provided.
    For simulating user interactions such as a mouse click or visual
    inspection, the ``perform`` and ``inspect`` methods are provided.

    Parameters
    ----------
    target : any
        An object on which further UI target can be searched for, or can be
        a leaf target that can be operated on.
    registries : list of TargetRegistry
        Registries of interaction for different target, in the order
        of decreasing priority.
    delay : int, optional
        Time delay (in ms) in which actions by the wrapper are performed. Note
        it is propagated through to created child wrappers. The delay allows
        visual confirmation test code is working as desired. Defaults to 0.

    Attributes
    ----------
    delay : int
        Time delay (in ms) in which actions by the wrapper are performed. Note
        it is propagated through to created child wrappers. The delay allows
        visual confirmation test code is working as desired.
    """

    def __init__(self, target, registries, delay=0):
        self._target = target
        self._registries = registries
        self.delay = delay

    def help(self):
        """ Print help messages.
        (This function is intended for interactive use.)
        """
        # mapping from interaction types to their documentation
        interaction_to_doc = dict()

        # mapping from location types to their documentation
        location_to_doc = dict()

        # Order registries by their priority (low to high)
        for registry in self._registries[::-1]:
            for type_ in registry.get_interactions(self._target.__class__):
                interaction_to_doc[type_] = registry.get_interaction_doc(
                    self._target.__class__, type_)

            for type_ in registry.get_locations(self._target.__class__):
                location_to_doc[type_] = registry.get_location_doc(
                    self._target.__class__, type_)

        print("Interactions")
        print("------------")
        for interaction_type in sorted(interaction_to_doc, key=repr):
            print(repr(interaction_type))
            print(
                textwrap.indent(
                    interaction_to_doc[interaction_type], prefix="    "
                )
            )
            print()

        if not interaction_to_doc:
            print("No interactions are supported.")
            print()

        print("Locations")
        print("---------")
        for locator_type in sorted(location_to_doc, key=repr):
            print(repr(locator_type))
            print(
                textwrap.indent(
                    location_to_doc[locator_type], prefix="    "
                )
            )
            print()

        if not location_to_doc:
            print("No locations are supported.")
            print()

    def locate(self, location):
        """ Attempt to resolve the given location and return a new
        UIWrapper.

        Parameters
        ----------
        location : any
            Any location type supported by the current target.

        Raises
        ------
        LocationNotSupported
            If the given location is not supported.

        See also
        --------
        UIWrapper.help
        """
        return UIWrapper(
            target=self._get_next_target(location),
            registries=self._registries,
            delay=self.delay,
        )

    def find_by_name(self, name):
        """ Find a target inside the current target using a name.

        This is equivalent to calling ``locate(TargetByName(name=name))``.

        Parameters
        ----------
        name : str
            A single name for retreiving a target on a UI.

        Returns
        -------
        wrapper : UIWrapper

        Raises
        ------
        LocationNotSupported
            If the current target does not support locating another target
            by a name.

        See also
        --------
        traitsui.testing.tester.locator.TargetByName
        """
        return self.locate(locator.TargetByName(name=name))

    def find_by_id(self, id):
        """ Find a target inside the current target using an id.

        This is equivalent to calling ``locate(TargetById(id=id))``.

        Parameters
        ----------
        id : str
            Id for finding an item in the UI.

        Returns
        -------
        wrapper : UIWrapper

        Raises
        ------
        LocationNotSupported
            If the current target does not support locating another target
            by a unique identifier.

        See also
        --------
        traitsui.testing.tester.locator.TargetById
        """
        return self.locate(locator.TargetById(id=id))

    def perform(self, interaction):
        """ Perform a user interaction that causes side effects.

        Parameters
        ----------
        interaction : object
            An interaction instance that defines the user interaction.
            See ``traitsui.testing.tester.command`` module for builtin
            query objects.
            e.g. ``traitsui.testing.tester.command.MouseClick``

        Raises
        ------
        InteractionNotSupported
            If the interaction given is not supported for the current UI
            target.

        See also
        --------
        UIWrapper.help
        """
        self._perform_or_inspect(interaction)

    def inspect(self, interaction):
        """ Return a value or values for inspection.

        Parameters
        ----------
        interaction : object
            An interaction instance that defines the inspection.
            See ``traitsui.testing.tester.query`` module for builtin
            query objects.
            e.g. ``traitsui.testing.tester.query.DisplayedText``

        Raises
        ------
        InteractionNotSupported
            If the interaction given is not supported for the current UI
            target.

        See also
        --------
        UIWrapper.help
        """
        return self._perform_or_inspect(interaction)

    def _perform_or_inspect(self, interaction):
        """ Perform a user interaction or a user inspection.

        Parameters
        ----------
        interaction : instance of interaction type
            An object defining the interaction.

        Returns
        -------
        value : any

        Raises
        ------
        InteractionNotSupported
            If the given interaction does not have a corresponding
            implementation for the wrapped UI target.
        """
        interaction_class = interaction.__class__
        supported = []
        for registry in self._registries:
            try:
                handler = registry.get_handler(
                    target_class=self._target.__class__,
                    interaction_class=interaction_class,
                )
            except InteractionNotSupported as e:
                supported.extend(e.supported)
                continue
            else:
                with _event_processed():
                    return handler(self, interaction)

        raise InteractionNotSupported(
            target_class=self._target.__class__,
            interaction_class=interaction.__class__,
            supported=supported,
        )

    def _get_next_target(self, location):
        """ Return the next UI target from the given location.

        Parameters
        ----------
        location : instance of locator type
            A location for resolving the next target.

        Returns
        -------
        new_target : any

        Raises
        ------
        LocationNotSupport
            If no solver are provided for resolving the given location in the
            wrapped UI target.
        """
        supported = set()
        for registry in self._registries:
            try:
                handler = registry.get_solver(
                    self._target.__class__,
                    location.__class__,
                )
            except LocationNotSupported as e:
                supported |= set(e.supported)
            else:
                return handler(self, location)

        raise LocationNotSupported(
            target_class=self._target.__class__,
            locator_class=location.__class__,
            supported=list(supported),
        )


@contextmanager
def _event_processed():
    """ Context manager to ensure GUI events are processed upon entering
    and exiting the context.
    """
    with _reraise_exceptions():
        _process_cascade_events()
        try:
            yield
        finally:
            _process_cascade_events()
