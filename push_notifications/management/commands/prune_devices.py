from django.core.management.base import BaseCommand


class Command(BaseCommand):
	can_import_settings = True
	help = 'Deactivate APNS devices that are not receiving notifications'

	def handle(self, *args, **options):
		from push_notifications.models import APNSDevice, get_expired_tokens
		expired = get_expired_tokens()
		devices = APNSDevice.objects.filter(registration_id__in=expired)
		for d in devices:
			self.stdout.write('deactivating [%s]' % d.registration_id)
			d.active = False
			d.save()
		self.stdout.write('deactivated %d devices' % len(devices))
