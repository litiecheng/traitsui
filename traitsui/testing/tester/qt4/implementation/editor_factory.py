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
from traitsui.testing.tester import query
from traitsui.testing.tester.qt4.registry_helper import (
    register_editable_textbox_handlers,
)
from traitsui.qt4.editor_factory import ReadonlyEditor, TextEditor


def register(registry):
    """ Register interactions for the given registry.

    If there are any conflicts, an error will occur.

    Parameters
    ----------
    registry : TargetRegistry
        The registry being registered to.
    """

    register_editable_textbox_handlers(
        registry=registry,
        target_class=TextEditor,
        widget_getter=lambda wrapper: wrapper._target.control,
    )
    registry.register_handler(
        target_class=ReadonlyEditor,
        interaction_class=query.DisplayedText,
        handler=lambda wrapper, _: wrapper._target.control.text()
    )
