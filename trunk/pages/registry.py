import copy

from zope.interface import Interface
from zope.interface import implements
import zope.component
from repoze.bfg.interfaces import IRequest

_marker = object()


def registerEventListener(event_iface=Interface):
    """ Registers an event listener (aka 'subscriber') listening for
    events of the type ``event_iface`` and returns a list which is
    appended to by the subscriber.  When an event is dispatched that
    matches ``event_iface``, that event will be appended to the list.
    You can then compare the values in the list to expected event
    notifications.  This method is useful when testing code that wants
    to call ``zope.component.event.dispatch`` or
    ``zope.component.event.objectEventNotify``."""
    L = []
    def subscriber(*event):
        L.extend(event)
    registerSubscriber(subscriber, event_iface)
    return L


def registerView(name, result='', view=None, for_=(Interface, Interface)):
    """ Registers ``repoze.bfg`` view function under the name
    ``name``.  The view will return a webob Response object with the
    ``result`` value as its body attribute.  To gain more control, if
    you pass in a non-None ``view``, this view function will be used
    instead of an automatically generated view function (and
    ``result`` is not used).  This function is useful when dealing
    with code that wants to call,
    e.g. ``repoze.bfg.view.render_view_to_response``."""
    if view is None:
        def view(context, request):
            from webob import Response
            return Response(result)
    from repoze.bfg.interfaces import IView
    return registerAdapter(view, for_, IView, name)

def registerViewPermission(name, result=True, viewpermission=None,
                           for_=(Interface, Interface)):
    """ Registers a ``repoze.bfg`` 'view permission' object under
    the name ``name``.  The view permission return a result
    denoted by the ``result`` argument.  If ``result`` is True, a
    ``repoze.bfg.security.Allowed`` object is returned; else a
    ``repoze.bfg.security.Denied`` object is returned.  To gain
    more control, if you pass in a non-None ``viewpermission``,
    this view permission object will be used instead of an
    automatically generated view permission (and ``result`` is not
    used).  This method is useful when dealing with code that
    wants to call, e.g. ``repoze.bfg.view.view_execution_permitted``.
    Note that view permissions are not checked unless a security
    policy is in effect (see ``registerSecurityPolicy``)."""
    from repoze.bfg.security import Allowed
    from repoze.bfg.security import Denied
    if result is True:
        result = Allowed('message')
    else:
        result = Denied('message')
    if viewpermission is None:
        def viewpermission(context, request):
            return result
    from repoze.bfg.interfaces import IViewPermission
    return registerAdapter(viewpermission, for_, IViewPermission, name)

def registerUtility(impl, iface=Interface, name=''):
    """ Register a Zope component architecture utility component.
    This is exposed as a convenience in this package to avoid needing
    to import the ``registerUtility`` function from ``zope.component``
    within unit tests that make use of the ZCA.  ``impl`` is the
    implementation of the utility.  ``iface`` is the interface type
    ``zope.interface.Interface`` by default.  ``name`` is the empty
    string by default.  See `The ZCA book
    <http://www.muthukadan.net/docs/zca.html>`_ for more information
    about ZCA utilities."""
    #import zope.component 
    gsm = zope.component.getSiteManager()
    gsm.registerUtility(impl, iface, name=name)
    return impl

def registerAdapter(impl, for_=Interface, provides=Interface, name=''):
    """ Register a Zope component architecture adapter component.
    This is exposed as a convenience in this package to avoid needing
    to import the ``registerAdapter`` function from ``zope.component``
    within unit tests that make use of the ZCA.  ``impl`` is the
    implementation of the component (often a class).  ``for_`` is the
    ``for`` interface type ``zope.interface.Interface`` by default. If
    ``for`` is not a tuple or list, it will be converted to a
    one-tuple before being passed to underlying ZCA registerAdapter
    API.  ``name`` is the empty string by default.  ``provides`` is
    the ZCA provides interface, also ``zope.interface.Interface`` by
    default.  ``name`` is the name of the adapter, the empty string by
    default.  See `The ZCA book
    <http://www.muthukadan.net/docs/zca.html>`_ for more information
    about ZCA adapters."""
    #import zope.component
    
    gsm = zope.component.getSiteManager()
    #
    if not isinstance(for_, (tuple, list)):
        for_ = (for_,)
    gsm.registerAdapter(impl, for_, provides, name=name)
    return impl

def registerSubscriber(subscriber, iface=Interface):
    """ Register a Zope component architecture subscriber component.
    This is exposed as a convenience in this package to avoid needing
    to import the ``registerHandler`` function from ``zope.component``
    within unit tests that make use of the ZCA.  ``subscriber`` is the
    implementation of the component (often a function).  ``iface`` is
    the interface type the subscriber will be registered for
    (``zope.interface.Interface`` by default). If ``iface`` is not a
    tuple or list, it will be converted to a one-tuple before being
    passed to underlying zca registerHandler query.  See `The ZCA book
    <http://www.muthukadan.net/docs/zca.html>`_ for more information
    about ZCA subscribers."""
    import zope.component
    gsm = zope.component.getSiteManager()
    if not isinstance(iface, (tuple, list)):
        iface = (iface,)
    gsm.registerHandler(subscriber, iface)
    return subscriber

def registerTraverserFactory(traverser, for_=Interface):
    from repoze.bfg.interfaces import ITraverserFactory
    return registerAdapter(traverser, for_, ITraverserFactory)

