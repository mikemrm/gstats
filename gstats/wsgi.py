# Copyright (c) 2010 Sabin Iacob <iacobs@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
#     The above copyright notice and this permission notice shall be included in
#     all copies or substantial portions of the Software.
# 
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#     THE SOFTWARE.

import zmq
import os


class Application(object):
    def __init__(self, zmq_context, gstats_addr, allowed_ips=['127.0.0.1', ]):
        self.ctx = zmq_context
        self.gstats_addr = gstats_addr
        self.allowed_ips = allowed_ips

    def dispatch(self, env):
        """ very simple URL dispatch, a la Cake: /zelink maps to handle_zelink """
        pi = env['PATH_INFO']
        if pi == '/':
            handler = getattr(self, 'handle_stats%s' % path[0], None)    
        else:    
            path = next(filter(None, env['PATH_INFO'].split('/')))
            handler = getattr(self, 'handle_%s' % path, None)

        if not handler:
            return '404 Not Found', [b'Not found']

        return handler(env)

    def handle_stats(self, env):
        comm = self.ctx.socket(zmq.REQ)
        comm.connect(self.gstats_addr)
        comm.send(b'STATS')
        ret = comm.recv()
        comm.close()
        return '200 OK', [ret]

    def handle_rtimes(self, env):
        comm = self.ctx.socket(zmq.REQ)
        comm.connect(self.gstats_addr)
        comm.send(b'RTIMES')
        ret = comm.recv()
        comm.close()
        return '200 OK', [ret]

    def __call__(self, env, start_response):
        if env['REMOTE_ADDR'] not in self.allowed_ips:
            start_response('403 Forbidden', [])
            return [b'You are not allowed to see this!']

        status, ret = self.dispatch(env)
        start_response(status, [])
        return ret


def context_factory():
    context_store = []
    def inner():
        if not context_store:
            context_store.append(zmq.Context())
        return context_store[0]

    return inner

get_context = context_factory()
gstats_control = os.environ.get('GSTATS_COMMS_ADDR', 'tcp://127.0.0.1:2345')
allowed_ips = os.environ.get('GSTATS_ALLOWED_IPS', '127.0.0.1').split(':')

app = Application(get_context(), gstats_control, allowed_ips)
