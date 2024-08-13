""" Quick export module """

from .pool import ProxyPool, acheck_proxy


proxy_pool = ProxyPool()

__all__ = ['proxy_pool']
