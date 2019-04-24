#------------------------------------------------------------------------------
#
#  Copyright (c) 2012, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in enthought/LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Author: Pietro Berkes
#  Date:   Dec 2012
#
#------------------------------------------------------------------------------

from __future__ import absolute_import
import unittest

from traits.api import Bool, HasTraits, Instance, Int, List
from traitsui.api import Item, TreeEditor, TreeNode, View

from traitsui.tests._tools import *


class Bogus(HasTraits):
    """ A bogus class representing a bogus tree. """

    bogus_list = List


class BogusTreeView(HasTraits):
    """ A traitsui view visualizing Bogus objects as trees. """

    bogus = Instance(Bogus)

    hide_root = Bool

    word_wrap = Bool

    def default_traits_view(self):
        nodes = [
            TreeNode(
                node_for=[Bogus],
                children='bogus_list',
                label='=Bogus'
            ),
        ]

        tree_editor = TreeEditor(
            nodes=nodes,
            hide_root=self.hide_root,
            editable=False,
            word_wrap=self.word_wrap,
        )

        traits_view = View(
            Item(name='bogus', id='engine', editor=tree_editor),
            buttons=['OK'],
        )

        return traits_view


class TestTreeView(unittest.TestCase):

    def _test_tree_editor_releases_listeners(self, hide_root):
        """ The TreeEditor should release the listener to the root node's children
        when it's disposed of.
        """

        with store_exceptions_on_all_threads():
            bogus = Bogus(bogus_list=[Bogus()])
            tree_editor_view = BogusTreeView(bogus=bogus, hide_root=hide_root)
            ui = tree_editor_view.edit_traits()

            # The TreeEditor sets a listener on the bogus object's children list
            notifiers_list = bogus.trait('bogus_list')._notifiers(False)
            self.assertEqual(1, len(notifiers_list))

            # Manually close the UI
            press_ok_button(ui)

            # The listener should be removed after the UI has been closed
            notifiers_list = bogus.trait('bogus_list')._notifiers(False)
            self.assertEqual(0, len(notifiers_list))

    @skip_if_null
    def test_tree_editor_listeners_with_shown_root(self):
        self._test_tree_editor_releases_listeners(hide_root=False)

    @skip_if_null
    def test_tree_editor_listeners_with_hidden_root(self):
        self._test_tree_editor_releases_listeners(hide_root=True)

    @skip_if_null
    def test_smoke_save_restore_prefs(self):
            bogus = Bogus(bogus_list=[Bogus()])
            tree_editor_view = BogusTreeView(bogus=bogus)
            ui = tree_editor_view.edit_traits()
            prefs = ui.get_prefs()
            ui.set_prefs(prefs)

    @skip_if_not_qt4
    def test_smoke_word_wrap(self):
            bogus = Bogus(bogus_list=[Bogus()])
            tree_editor_view = BogusTreeView(bogus=bogus, word_wrap=True)
            ui = tree_editor_view.edit_traits()
            ui.dispose()