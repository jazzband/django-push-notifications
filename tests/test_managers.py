from django.test import TestCase, override_settings

from push_notifications import models
from push_notifications.models import APNSDevice, GCMDevice, WebPushDevice, WNSDevice


class DeviceRouter:
	def db_for_read(self, model, **hints):
		return hints.get("read_db", "other")

	def db_for_write(self, model, **hints):
		return hints.get("write_db", "default")


@override_settings(DATABASE_ROUTERS=[])
class DeviceManagerTestCase(TestCase):
	databases = {"default", "other"}
	device_models = (GCMDevice, APNSDevice, WNSDevice, WebPushDevice)

	@classmethod
	def setUpTestData(cls):
		for model in cls.device_models:
			for alias in cls.databases:
				model.objects.using(alias).create(name=alias, registration_id=alias)

	def assert_database_operations(self, manager, read_db, write_db):
		self.assertEqual(
			list(manager.filter(name__in=self.databases).values_list("name", flat=True)),
			[read_db],
		)
		token = "created-{}-{}".format(read_db, write_db)
		device = manager.create(registration_id=token)
		self.assertEqual(device._state.db, write_db)
		for alias in self.databases:
			self.assertEqual(
				manager.model.objects.using(alias).filter(registration_id=token).exists(),
				alias == write_db,
			)

	def test_db_manager(self):
		for model in self.device_models:
			for alias in self.databases:
				with self.subTest(model=model.__name__, alias=alias):
					self.assert_database_operations(model.objects.db_manager(alias), alias, alias)

	@override_settings(DATABASE_ROUTERS=[DeviceRouter()])
	def test_db_manager_overrides_router(self):
		for model in self.device_models:
			for alias in self.databases:
				with self.subTest(model=model.__name__, alias=alias):
					self.assert_database_operations(model.objects.db_manager(alias), alias, alias)

	@override_settings(DATABASE_ROUTERS=[DeviceRouter()])
	def test_router_hints(self):
		for model in self.device_models:
			with self.subTest(model=model.__name__):
				manager = model.objects.db_manager(hints={
					"read_db": "default", "write_db": "other",
				})
				self.assert_database_operations(manager, "default", "other")

	def test_instance_hint(self):
		for model in self.device_models:
			with self.subTest(model=model.__name__):
				instance = model.objects.using("other").get(registration_id="other")
				manager = model.objects.db_manager(hints={"instance": instance})
				self.assert_database_operations(manager, "other", "other")

	def test_queryset_class(self):
		for model, queryset_class in (
			(GCMDevice, models.GCMDeviceQuerySet),
			(APNSDevice, models.APNSDeviceQuerySet),
			(WNSDevice, models.WNSDeviceQuerySet),
			(WebPushDevice, models.WebPushDeviceQuerySet),
		):
			with self.subTest(model=model.__name__):
				queryset = model.objects.db_manager("other").filter(active=True)
				self.assertIs(type(queryset), queryset_class)
				self.assertTrue(callable(queryset.send_message))
