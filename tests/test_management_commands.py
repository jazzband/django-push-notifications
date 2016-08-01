from django.core.management import call_command
from django.test import TestCase
from ._mock import mock


class CommandsTestCase(TestCase):

	def test_prune_devices(self):
		from push_notifications.models import APNSDevice

		device = APNSDevice.objects.create(
			registration_id="616263",  # hex encoding of b'abc'
		)

		feedback_method = "push_notifications.apns._apns_create_socket_to_feedback"
		recv_feedback_method = "push_notifications.apns._apns_receive_feedback"
		with mock.patch(feedback_method, mock.MagicMock()):
			with mock.patch(recv_feedback_method, mock.MagicMock()) as receiver:
				receiver.side_effect = lambda s: [(b'', b'abc')]
				call_command('prune_devices')

		device = APNSDevice.objects.get(pk=device.pk)
		self.assertFalse(device.active)
