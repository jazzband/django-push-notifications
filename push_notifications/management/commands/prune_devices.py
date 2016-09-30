from django.core.management.base import BaseCommand


class Command(BaseCommand):
	can_import_settings = True
	help = 'Deactivate APNS devices that are not receiving notifications'

	def handle(self, *args, **options):
		from push_notifications.models import APNSDevice, get_expired_tokens
		app_ids = set(APNSDevice.objects.values_list('application_id', flat=True).distinct())
		for app_id in app_ids:
			expired = get_expired_tokens(app_id)
			cnt = APNSDevice.objects.filter(registration_id__in=expired).update(active=False)
			self.stdout.write('deactivated %d devices' % cnt)
