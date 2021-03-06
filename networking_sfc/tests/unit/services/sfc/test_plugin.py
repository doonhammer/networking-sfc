# Copyright 2015 Futurewei. All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import mock

from networking_sfc.services.sfc.common import context as sfc_ctx
from networking_sfc.services.sfc.common import exceptions as sfc_exc
from networking_sfc.tests.unit.db import test_sfc_db

SFC_PLUGIN_KLASS = (
    "networking_sfc.services.sfc.plugin.SfcPlugin"
)


class SfcPluginTestCase(test_sfc_db.SfcDbPluginTestCase):
    def setUp(self, core_plugin=None, sfc_plugin=None, ext_mgr=None):
        if not sfc_plugin:
            sfc_plugin = SFC_PLUGIN_KLASS
        self.driver_manager_p = mock.patch(
            'networking_sfc.services.sfc.driver_manager.SfcDriverManager'
        )
        self.fake_driver_manager_class = self.driver_manager_p.start()
        self.fake_driver_manager = mock.Mock()
        self.fake_driver_manager_class.return_value = self.fake_driver_manager
        self.plugin_context = None
        super(SfcPluginTestCase, self).setUp(
            core_plugin=core_plugin, sfc_plugin=sfc_plugin,
            ext_mgr=ext_mgr
        )

    def _record_context(self, plugin_context):
        self.plugin_context = plugin_context

    def test_create_port_chain_driver_manager_called(self):
        self.fake_driver_manager.create_port_chain = mock.Mock(
            side_effect=self._record_context)
        with self.port_pair_group(port_pair_group={}) as pg:
            with self.port_chain(port_chain={
                'port_pair_groups': [pg['port_pair_group']['id']]
            }) as pc:
                driver_manager = self.fake_driver_manager
                driver_manager.create_port_chain.assert_called_once_with(
                    mock.ANY
                )
                self.assertIsInstance(
                    self.plugin_context, sfc_ctx.PortChainContext
                )
                self.assertIn('port_chain', pc)
                self.assertEqual(
                    self.plugin_context.current, pc['port_chain'])

    def test_create_port_chain_driver_manager_exception(self):
        self.fake_driver_manager.create_port_chain = mock.Mock(
            side_effect=sfc_exc.SfcDriverError(
                method='create_port_chain'
            )
        )
        with self.port_pair_group(port_pair_group={}) as pg:
            self._create_port_chain(
                self.fmt,
                {'port_pair_groups': [pg['port_pair_group']['id']]},
                expected_res_status=500)
            self._test_list_resources('port_chain', [])
        self.fake_driver_manager.delete_port_chain.assert_called_once_with(
            mock.ANY
        )

    def test_update_port_chain_driver_manager_called(self):
        self.fake_driver_manager.update_port_chain = mock.Mock(
            side_effect=self._record_context)
        with self.port_pair_group(port_pair_group={}) as pg:
            with self.port_chain(port_chain={
                'name': 'test1',
                'port_pair_groups': [pg['port_pair_group']['id']]
            }) as pc:
                req = self.new_update_request(
                    'port_chains', {'port_chain': {'name': 'test2'}},
                    pc['port_chain']['id']
                )
                res = self.deserialize(
                    self.fmt,
                    req.get_response(self.ext_api)
                )
                driver_manager = self.fake_driver_manager
                driver_manager.update_port_chain.assert_called_once_with(
                    mock.ANY
                )
                self.assertIsInstance(
                    self.plugin_context, sfc_ctx.PortChainContext
                )
                self.assertIn('port_chain', pc)
                self.assertIn('port_chain', res)
                self.assertEqual(
                    self.plugin_context.current, res['port_chain'])
                self.assertEqual(
                    self.plugin_context.original, pc['port_chain'])

    def test_update_port_chain_driver_manager_exception(self):
        self.fake_driver_manager.update_port_chain = mock.Mock(
            side_effect=sfc_exc.SfcDriverError(
                method='update_port_chain'
            )
        )
        with self.port_pair_group(port_pair_group={}) as pg:
            with self.port_chain(port_chain={
                'name': 'test1',
                'port_pair_groups': [pg['port_pair_group']['id']]
            }) as pc:
                self.assertIn('port_chain', pc)
                original_port_chain = pc['port_chain']
                req = self.new_update_request(
                    'port_chains', {'port_chain': {'name': 'test2'}},
                    pc['port_chain']['id']
                )
                updated_port_chain = copy.copy(original_port_chain)
                updated_port_chain['name'] = 'test2'
                res = req.get_response(self.ext_api)
                self.assertEqual(500, res.status_int)
                res = self._list('port_chains')
                self.assertIn('port_chains', res)
                self.assertItemsEqual(
                    res['port_chains'], [updated_port_chain])

    def test_delete_port_chain_manager_called(self):
        self.fake_driver_manager.delete_port_chain = mock.Mock(
            side_effect=self._record_context)
        with self.port_pair_group(port_pair_group={}) as pg:
            with self.port_chain(port_chain={
                'name': 'test1',
                'port_pair_groups': [pg['port_pair_group']['id']]
            }, do_delete=False) as pc:
                req = self.new_delete_request(
                    'port_chains', pc['port_chain']['id']
                )
                res = req.get_response(self.ext_api)
                self.assertEqual(204, res.status_int)
                driver_manager = self.fake_driver_manager
                driver_manager.delete_port_chain.assert_called_once_with(
                    mock.ANY
                )
                self.assertIsInstance(
                    self.plugin_context, sfc_ctx.PortChainContext
                )
            self.assertIn('port_chain', pc)
            self.assertEqual(self.plugin_context.current, pc['port_chain'])

    def test_delete_port_chain_driver_manager_exception(self):
        self.fake_driver_manager.delete_port_chain = mock.Mock(
            side_effect=sfc_exc.SfcDriverError(
                method='delete_port_chain'
            )
        )
        with self.port_pair_group(port_pair_group={
        }, do_delete=False) as pg:
            with self.port_chain(port_chain={
                'name': 'test1',
                'port_pair_groups': [pg['port_pair_group']['id']]
            }, do_delete=False) as pc:
                req = self.new_delete_request(
                    'port_chains', pc['port_chain']['id']
                )
                res = req.get_response(self.ext_api)
                self.assertEqual(500, res.status_int)
                self._test_list_resources('port_chain', [pc])

    def test_create_port_pair_group_driver_manager_called(self):
        self.fake_driver_manager.create_port_pair_group = mock.Mock(
            side_effect=self._record_context)
        with self.port_pair_group(port_pair_group={}) as pc:
            fake_driver_manager = self.fake_driver_manager
            fake_driver_manager.create_port_pair_group.assert_called_once_with(
                mock.ANY
            )
            self.assertIsInstance(
                self.plugin_context, sfc_ctx.PortPairGroupContext
            )
            self.assertIn('port_pair_group', pc)
            self.assertEqual(
                self.plugin_context.current, pc['port_pair_group'])

    def test_create_port_pair_group_driver_manager_exception(self):
        self.fake_driver_manager.create_port_pair_group = mock.Mock(
            side_effect=sfc_exc.SfcDriverError(
                method='create_port_pair_group'
            )
        )
        self._create_port_pair_group(self.fmt, {}, expected_res_status=500)
        self._test_list_resources('port_pair_group', [])
        driver_manager = self.fake_driver_manager
        driver_manager.delete_port_pair_group.assert_called_once_with(
            mock.ANY
        )

    def test_update_port_pair_group_driver_manager_called(self):
        self.fake_driver_manager.update_port_pair_group = mock.Mock(
            side_effect=self._record_context)
        with self.port_pair_group(port_pair_group={
            'name': 'test1'
        }) as pc:
            req = self.new_update_request(
                'port_pair_groups', {'port_pair_group': {'name': 'test2'}},
                pc['port_pair_group']['id']
            )
            res = self.deserialize(
                self.fmt,
                req.get_response(self.ext_api)
            )
            driver_manager = self.fake_driver_manager
            driver_manager.update_port_pair_group.assert_called_once_with(
                mock.ANY
            )
            self.assertIsInstance(
                self.plugin_context, sfc_ctx.PortPairGroupContext
            )
            self.assertIn('port_pair_group', pc)
            self.assertIn('port_pair_group', res)
            self.assertEqual(
                self.plugin_context.current, res['port_pair_group'])
            self.assertEqual(
                self.plugin_context.original, pc['port_pair_group'])

    def test_update_port_pair_group_driver_manager_exception(self):
        self.fake_driver_manager.update_port_pair_group = mock.Mock(
            side_effect=sfc_exc.SfcDriverError(
                method='update_port_pair_group'
            )
        )
        with self.port_pair_group(port_pair_group={
            'name': 'test1'
        }) as pc:
            self.assertIn('port_pair_group', pc)
            original_port_pair_group = pc['port_pair_group']
            req = self.new_update_request(
                'port_pair_groups', {'port_pair_group': {'name': 'test2'}},
                pc['port_pair_group']['id']
            )
            updated_port_pair_group = copy.copy(original_port_pair_group)
            updated_port_pair_group['name'] = 'test2'
            res = req.get_response(self.ext_api)
            self.assertEqual(500, res.status_int)
            res = self._list('port_pair_groups')
            self.assertIn('port_pair_groups', res)
            self.assertItemsEqual(
                res['port_pair_groups'], [updated_port_pair_group])

    def test_delete_port_pair_group_manager_called(self):
        self.fake_driver_manager.delete_port_pair_group = mock.Mock(
            side_effect=self._record_context)
        with self.port_pair_group(port_pair_group={
            'name': 'test1'
        }, do_delete=False) as pc:
            req = self.new_delete_request(
                'port_pair_groups', pc['port_pair_group']['id']
            )
            res = req.get_response(self.ext_api)
            self.assertEqual(204, res.status_int)
            driver_manager = self.fake_driver_manager
            driver_manager.delete_port_pair_group.assert_called_once_with(
                mock.ANY
            )
            self.assertIsInstance(
                self.plugin_context, sfc_ctx.PortPairGroupContext
            )
            self.assertIn('port_pair_group', pc)
            self.assertEqual(
                self.plugin_context.current, pc['port_pair_group'])

    def test_delete_port_pair_group_driver_manager_exception(self):
        self.fake_driver_manager.delete_port_pair_group = mock.Mock(
            side_effect=sfc_exc.SfcDriverError(
                method='delete_port_pair_group'
            )
        )
        with self.port_pair_group(port_pair_group={
            'name': 'test1'
        }, do_delete=False) as pc:
            req = self.new_delete_request(
                'port_pair_groups', pc['port_pair_group']['id']
            )
            res = req.get_response(self.ext_api)
            self.assertEqual(500, res.status_int)
            self._test_list_resources('port_pair_group', [pc])

    def test_create_port_pair_driver_manager_called(self):
        self.fake_driver_manager.create_port_pair = mock.Mock(
            side_effect=self._record_context)
        with self.port(
            name='port1',
            device_id='default'
        ) as src_port, self.port(
            name='port2',
            device_id='default'
        ) as dst_port:
            with self.port_pair(port_pair={
                'ingress': src_port['port']['id'],
                'egress': dst_port['port']['id']
            }) as pc:
                driver_manager = self.fake_driver_manager
                driver_manager.create_port_pair.assert_called_once_with(
                    mock.ANY
                )
                self.assertIsInstance(
                    self.plugin_context, sfc_ctx.PortPairContext
                )
                self.assertIn('port_pair', pc)
                self.assertEqual(self.plugin_context.current, pc['port_pair'])

    def test_create_port_pair_driver_manager_exception(self):
        self.fake_driver_manager.create_port_pair = mock.Mock(
            side_effect=sfc_exc.SfcDriverError(
                method='create_port_pair'
            )
        )
        with self.port(
            name='port1',
            device_id='default'
        ) as src_port, self.port(
            name='port2',
            device_id='default'
        ) as dst_port:
            self._create_port_pair(
                self.fmt,
                {
                    'ingress': src_port['port']['id'],
                    'egress': dst_port['port']['id']
                },
                expected_res_status=500)
            self._test_list_resources('port_pair', [])
            driver_manager = self.fake_driver_manager
            driver_manager.delete_port_pair.assert_called_once_with(
                mock.ANY
            )

    def test_update_port_pair_driver_manager_called(self):
        self.fake_driver_manager.update_port_pair = mock.Mock(
            side_effect=self._record_context)
        with self.port(
            name='port1',
            device_id='default'
        ) as src_port, self.port(
            name='port2',
            device_id='default'
        ) as dst_port:
            with self.port_pair(port_pair={
                'name': 'test1',
                'ingress': src_port['port']['id'],
                'egress': dst_port['port']['id']
            }) as pc:
                req = self.new_update_request(
                    'port_pairs', {'port_pair': {'name': 'test2'}},
                    pc['port_pair']['id']
                )
                res = self.deserialize(
                    self.fmt,
                    req.get_response(self.ext_api)
                )
                driver_manager = self.fake_driver_manager
                driver_manager.update_port_pair.assert_called_once_with(
                    mock.ANY
                )
                self.assertIsInstance(
                    self.plugin_context, sfc_ctx.PortPairContext
                )
                self.assertIn('port_pair', pc)
                self.assertIn('port_pair', res)
                self.assertEqual(
                    self.plugin_context.current, res['port_pair'])
                self.assertEqual(
                    self.plugin_context.original, pc['port_pair'])

    def test_update_port_pair_driver_manager_exception(self):
        self.fake_driver_manager.update_port_pair = mock.Mock(
            side_effect=sfc_exc.SfcDriverError(
                method='update_port_pair'
            )
        )
        with self.port(
            name='port1',
            device_id='default'
        ) as src_port, self.port(
            name='port2',
            device_id='default'
        ) as dst_port:
            with self.port_pair(port_pair={
                'name': 'test1',
                'ingress': src_port['port']['id'],
                'egress': dst_port['port']['id']
            }) as pc:
                self.assertIn('port_pair', pc)
                original_port_pair = pc['port_pair']
                req = self.new_update_request(
                    'port_pairs', {'port_pair': {'name': 'test2'}},
                    pc['port_pair']['id']
                )
                updated_port_pair = copy.copy(original_port_pair)
                updated_port_pair['name'] = 'test2'
                res = req.get_response(self.ext_api)
                self.assertEqual(500, res.status_int)
                res = self._list('port_pairs')
                self.assertIn('port_pairs', res)
                self.assertItemsEqual(res['port_pairs'], [updated_port_pair])

    def test_delete_port_pair_manager_called(self):
        self.fake_driver_manager.delete_port_pair = mock.Mock(
            side_effect=self._record_context)
        with self.port(
            name='port1',
            device_id='default'
        ) as src_port, self.port(
            name='port2',
            device_id='default'
        ) as dst_port:
            with self.port_pair(port_pair={
                'name': 'test1',
                'ingress': src_port['port']['id'],
                'egress': dst_port['port']['id']
            }, do_delete=False) as pc:
                req = self.new_delete_request(
                    'port_pairs', pc['port_pair']['id']
                )
                res = req.get_response(self.ext_api)
                self.assertEqual(204, res.status_int)
                fake_driver_manager = self.fake_driver_manager
                fake_driver_manager.delete_port_pair.assert_called_once_with(
                    mock.ANY
                )
                self.assertIsInstance(
                    self.plugin_context, sfc_ctx.PortPairContext
                )
                self.assertIn('port_pair', pc)
                self.assertEqual(self.plugin_context.current, pc['port_pair'])

    def test_delete_port_pair_driver_manager_exception(self):
        self.fake_driver_manager.delete_port_pair = mock.Mock(
            side_effect=sfc_exc.SfcDriverError(
                method='delete_port_pair'
            )
        )
        with self.port(
            name='port1',
            device_id='default'
        ) as src_port, self.port(
            name='port2',
            device_id='default'
        ) as dst_port:
            with self.port_pair(port_pair={
                'name': 'test1',
                'ingress': src_port['port']['id'],
                'egress': dst_port['port']['id']
            }, do_delete=False) as pc:
                req = self.new_delete_request(
                    'port_pairs', pc['port_pair']['id']
                )
                res = req.get_response(self.ext_api)
                self.assertEqual(500, res.status_int)
                self._test_list_resources('port_pair', [pc])
