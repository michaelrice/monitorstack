# Copyright 2017, Kevin Carter <kevin@cloudnull.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Get metrics from a KVM hypervisor."""
import socket

import click

from monitorstack import utils
from monitorstack.cli import pass_context


DOC = """Get metrics from a KVM hypervisor."""
COMMAND_NAME = 'kvm'


@click.command(COMMAND_NAME, short_help=DOC.split('\n')[0])
@pass_context
def cli(ctx):
    """Get metrics from a KVM hypervisor."""
    setattr(cli, '__doc__', DOC)

    # Lower level import because we only want to load this module
    #  when this plugin is called.
    try:
        import libvirt
    except ImportError:
        raise SystemExit('The "kvm plugin requires libvirt-python to be'
                         ' installed".')

    output = {
        'measurement_name': 'kvm',
        'meta': {
            'kvm_host_id': abs(hash(socket.getfqdn()))
        }
    }

    # Open a read-only connection to libvirt
    conn = libvirt.openReadOnly("qemu:///system")

    try:
        variables = dict()

        # Get all of the KVM instances on this host.
        domains = conn.listDomainsID()
        variables['kvm_vms'] = len(domains)
        variables['kvm_total_vcpus'] = conn.getCPUMap()[0]
        variables['kvm_scheduled_vcpus'] = 0

        # Loop through each instance to gather additional data.
        for domain in domains:
            variables['kvm_scheduled_vcpus'] += conn.lookupByID(
                domain
            ).maxVcpus()

        # Return the data.
        output['variables'] = variables

    except Exception as exp:
        # We may have picked up an exception while querying libvirt for data.
        output['exit_code'] = 1
        output['message'] = '{} failed -- {}'.format(
            COMMAND_NAME,
            utils.log_exception(exp=exp)
        )
    else:
        output['exit_code'] = 0
        output['message'] = 'kvm is ok'
    finally:
        conn.close()
        return output
